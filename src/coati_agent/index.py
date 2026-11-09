"""The docs index: heading-aware chunks, their embeddings, and search in memory.

Why not Vector Search: an endpoint can't scale to zero (one unit minimum,
about $200 a month), and the docs are a couple of hundred chunks. A cosine
scan over a few hundred vectors takes well under a millisecond, so the index
ships with the agent (spec D1). `DocsIndex.search` is the one place to swap
if the corpus ever outgrows that.

    python -m coati_agent.index --out build/index      # embed with the workspace's model
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import mlflow
import numpy as np
from mlflow.entities import SpanType

from .prompt import DATA_DIR, load_export
from .tools import Citation, ServerTool, ToolResult

# About 300 to 800 tokens, at roughly four characters a token.
MIN_CHARS = 1200
MAX_CHARS = 3200
SEP = " › "

SEARCH_DOCS_SPEC = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": (
            "Search the Latitude 10 platform documentation (docs.latitude10.tech): "
            "the registry, hosted API reference and API client, hosted docs, SDKs, "
            "hosted MCP, keys, plans and limits, enterprise. Returns numbered passages "
            "with their URLs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to look for, in a few words.",
                }
            },
            "required": ["query"],
        },
    },
}


@dataclass(frozen=True)
class Section:
    heading: str
    body: str


@dataclass(frozen=True)
class Chunk:
    id: str
    url: str
    title: str
    heading: str
    text: str

    @property
    def embed_text(self) -> str:
        return f"{self.heading}\n\n{self.text}"


# --- chunking -------------------------------------------------------------


def sections(text: str, title: str) -> list[Section]:
    """Split a page at its h2 and h3 headings, never inside a code fence."""
    out: list[Section] = []
    h2: str | None = None
    h3: str | None = None
    body: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(body).strip()
        if text:
            out.append(Section(SEP.join(p for p in (title, h2, h3) if p), text))
        body.clear()

    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            flush()
            h2, h3 = line[3:].strip(), None
        elif not in_fence and line.startswith("### "):
            flush()
            h3 = line[4:].strip()
        elif not in_fence and line.startswith("# "):
            continue  # the page title, already in every heading
        else:
            body.append(line)
    flush()
    return out


def _paragraphs(body: str) -> list[str]:
    """Blank-line separated blocks, keeping a code fence in one block."""
    blocks: list[str] = []
    for block in body.split("\n\n"):
        if blocks and blocks[-1].count("```") % 2 == 1:
            blocks[-1] += "\n\n" + block
        else:
            blocks.append(block)
    return [b for b in (b.strip() for b in blocks) if b]


def _pack(parts: Sequence[str]) -> list[str]:
    """Greedily join parts with blank lines, up to MAX_CHARS a piece."""
    pieces: list[str] = []
    for part in parts:
        if pieces and len(pieces[-1]) + 2 + len(part) <= MAX_CHARS:
            pieces[-1] += "\n\n" + part
        else:
            pieces.append(part)
    return pieces


def chunk_page(row: dict[str, Any]) -> list[Chunk]:
    """Chunks of about MIN_CHARS to MAX_CHARS, each starting at a heading."""
    # Each piece is (its heading, its text); a long section becomes several.
    pieces: list[tuple[str, str]] = []
    for section in sections(row["text"], row["title"]):
        for text in _pack(_paragraphs(section.body)):
            pieces.append((section.heading, text))

    groups: list[list[tuple[str, str]]] = []
    for heading, text in pieces:
        group = groups[-1] if groups else None
        if group is not None:
            size = sum(len(_render(h, t, i)) + 2 for i, (h, t) in enumerate(group))
            if size + len(_render(heading, text, 1)) <= MAX_CHARS or size < MIN_CHARS / 2:
                group.append((heading, text))
                continue
        groups.append([(heading, text)])

    return [
        Chunk(
            id=f"{row['path']}#{n}",
            url=row["url"],
            title=row["title"],
            heading=group[0][0],
            text="\n\n".join(_render(h, t, i) for i, (h, t) in enumerate(group)),
        )
        for n, group in enumerate(groups)
    ]


def _render(heading: str, text: str, position: int) -> str:
    # The chunk's first heading is its label; later ones stay in the text.
    return text if position == 0 else f"## {heading.split(SEP)[-1]}\n\n{text}"


def load_rows(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    docs = load_export(data_dir)["docs.jsonl"]  # hash-checked against the manifest
    return [json.loads(line) for line in docs.splitlines() if line.strip()]


# --- embeddings and search ------------------------------------------------


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> np.ndarray: ...


class DatabricksEmbedder:
    """A Databricks embeddings endpoint, called through an OpenAI-style client.

    Pay-per-token endpoints have a per-workspace rate limit, and Free Edition's
    is low: calls are spaced at least `min_interval` seconds apart, and a 429
    waits and retries with a doubling delay.
    """

    def __init__(
        self,
        client: Any,
        endpoint: str,
        retries: int = 6,
        min_interval: float = 1.5,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.client = client
        self.endpoint = endpoint
        self.retries = retries
        self.min_interval = min_interval
        self.sleep = sleep
        self.clock = clock
        self._last: float | None = None

    def _pace(self) -> None:
        if self._last is not None:
            wait = self.min_interval - (self.clock() - self._last)
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        for attempt in range(self.retries + 1):
            self._pace()
            try:
                response = self.client.embeddings.create(model=self.endpoint, input=list(texts))
            except Exception as error:
                if getattr(error, "status_code", None) != 429 or attempt == self.retries:
                    raise
                self.sleep(2.0**attempt)
            else:
                return np.array([item.embedding for item in response.data], dtype=np.float32)
        raise AssertionError("unreachable")


def _normalise(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


class DocsIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, model: str = ""):
        if len(chunks) != len(vectors):
            raise ValueError(f"{len(vectors)} vectors for {len(chunks)} chunks")
        self.chunks = chunks
        self.vectors = _normalise(vectors)
        self.model = model

    def search(self, query_vector: np.ndarray, k: int = 5) -> list[tuple[Chunk, float]]:
        scores = self.vectors @ _normalise(query_vector)
        best = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in best]

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "vectors.npy", self.vectors)
        lines = (json.dumps(asdict(c), ensure_ascii=False) for c in self.chunks)
        (directory / "chunks.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        meta = {"chunks": len(self.chunks), "dim": int(self.vectors.shape[1]), "model": self.model}
        (directory / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, directory: Path) -> DocsIndex:
        lines = (directory / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
        chunks = [Chunk(**json.loads(line)) for line in lines if line.strip()]
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        return cls(chunks, np.load(directory / "vectors.npy"), model=meta.get("model", ""))


def build_index(
    rows: list[dict[str, Any]], embedder: Embedder, batch_size: int = 8, model: str = ""
) -> DocsIndex:
    chunks = [chunk for row in rows for chunk in chunk_page(row)]
    texts = [c.embed_text for c in chunks]
    batches = [embedder.embed(texts[i : i + batch_size]) for i in range(0, len(texts), batch_size)]
    return DocsIndex(chunks, np.vstack(batches), model=model)


# --- the tool -------------------------------------------------------------


def search_docs_tool(index: DocsIndex, embedder: Embedder, k: int = 5) -> ServerTool:
    @mlflow.trace(span_type=SpanType.RETRIEVER, name="retrieve_docs")
    def retrieve(query: str) -> list[dict[str, Any]]:
        hits = index.search(embedder.embed([query])[0], k=k)
        # MLflow's document shape, which its groundedness judges read.
        return [
            {
                "page_content": chunk.text,
                "metadata": {"doc_uri": chunk.url, "chunk_id": chunk.id, "title": chunk.heading},
                "id": chunk.id,
                "score": score,
            }
            for chunk, score in hits
        ]

    def search_docs(query: str) -> ToolResult:
        if not query.strip():
            return ToolResult(content="Error: the query is empty. Say what to look for.")
        docs = retrieve(query.strip())
        content = "\n\n".join(
            f"[{n}] {d['metadata']['title']} ({d['metadata']['doc_uri']})\n{d['page_content']}"
            for n, d in enumerate(docs, start=1)
        )
        citations: list[Citation] = []
        for d in docs:
            citation = Citation(title=d["metadata"]["title"], url=d["metadata"]["doc_uri"])
            if citation not in citations:
                citations.append(citation)
        return ToolResult(content=content, citations=citations)

    return search_docs


# --- building it for real -------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Embed the docs into an index directory.")
    parser.add_argument("--out", type=Path, default=Path("build/index"))
    parser.add_argument("--endpoint", default="databricks-gte-large-en")
    parser.add_argument("--profile", default=None, help="Databricks CLI profile")
    args = parser.parse_args(argv)

    from .workspace import openai_client

    client = openai_client(args.profile, max_retries=0)  # DatabricksEmbedder retries
    index = build_index(load_rows(), DatabricksEmbedder(client, args.endpoint), model=args.endpoint)
    index.save(args.out)
    print(f"{len(index.chunks)} chunks, {index.vectors.shape[1]} dimensions -> {args.out}")


if __name__ == "__main__":
    main()
