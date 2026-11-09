"""Chunking the docs, ranking chunks, and the search_docs tool (fake vectors, no network)."""

import json

import numpy as np
import pytest

from coati_agent.index import (
    MAX_CHARS,
    MIN_CHARS,
    DocsIndex,
    build_index,
    chunk_page,
    load_rows,
    search_docs_tool,
    sections,
)
from coati_agent.prompt import DATA_DIR
from coati_agent.tools import Citation


def page(text, title="Keys", url="https://docs.latitude10.tech/keys"):
    return {"path": "keys.md", "url": url, "title": title, "text": text}


def para(n, word="alpha"):
    return " ".join([word] * n)


# --- sections -------------------------------------------------------------


def test_sections_split_at_h2_and_h3_and_keep_the_path():
    text = "# Keys\n\nIntro.\n\n## Project keys\n\nA.\n\n### Rotating\n\nB.\n\n## Agent keys\n\nC."
    got = [(s.heading, s.body) for s in sections(text, "Keys")]
    assert got == [
        ("Keys", "Intro."),
        ("Keys › Project keys", "A."),
        ("Keys › Project keys › Rotating", "B."),
        ("Keys › Agent keys", "C."),
    ]


def test_a_heading_inside_a_code_fence_is_not_a_section():
    text = "## Push\n\n```yaml\n## not a heading\nrun: x\n```\n\nAfter."
    got = sections(text, "CI")
    assert len(got) == 1
    assert "## not a heading" in got[0].body


# --- chunks ---------------------------------------------------------------


def test_small_sections_are_packed_together():
    text = "\n\n".join(f"## S{i}\n\n{para(30)}" for i in range(4))
    chunks = chunk_page(page(text))
    assert len(chunks) == 1
    assert chunks[0].heading == "Keys › S0"


def test_a_long_section_is_split_on_paragraphs_and_loses_nothing():
    paragraphs = [para(120, w) for w in ("red", "green", "blue", "cyan", "gold", "pink")]
    chunks = chunk_page(page("## Long\n\n" + "\n\n".join(paragraphs)))
    assert len(chunks) > 1
    assert all(len(c.text) <= MAX_CHARS for c in chunks)
    joined = "\n\n".join(c.text for c in chunks)
    assert all(p in joined for p in paragraphs)


def test_each_chunk_carries_its_page_and_heading_for_embedding():
    chunks = chunk_page(page("## Project keys\n\n" + para(20)))
    assert chunks[0].url == "https://docs.latitude10.tech/keys"
    assert chunks[0].embed_text.startswith("Keys › Project keys\n\n")


def test_the_real_docs_chunk_within_bounds():
    rows = load_rows(DATA_DIR)
    chunks = [c for row in rows for c in chunk_page(row)]

    assert {c.url for c in chunks} == {r["url"] for r in rows}
    assert len({c.id for c in chunks}) == len(chunks)
    too_big = [c.id for c in chunks if len(c.text) > MAX_CHARS and "\n\n" in c.text]
    assert too_big == []
    small = [c for c in chunks if len(c.text) < MIN_CHARS]
    # Only a page's last chunk may be short (nothing left to pack it with).
    assert len(small) <= len(rows)


# --- the index ------------------------------------------------------------


class FakeEmbedder:
    """Maps each text to a fixed vector by keyword, and counts its calls."""

    KEYS = ("sso", "price", "mcp")

    def __init__(self):
        self.batches = []

    def embed(self, texts):
        self.batches.append(list(texts))
        return np.array([[t.lower().count(k) + 0.01 for k in self.KEYS] for t in texts])


def two_page_index(embedder=None):
    rows = [
        page("## Single sign-on\n\nSSO with OpenID Connect. SSO SSO.", "Enterprise", "u/sso"),
        page("## Prices\n\nThe price of Pro. price.", "Pricing", "u/price"),
    ]
    return build_index(rows, embedder or FakeEmbedder(), batch_size=1)


def test_build_embeds_in_batches_and_keeps_order():
    embedder = FakeEmbedder()
    index = two_page_index(embedder)
    assert len(embedder.batches) == 2
    assert [c.url for c in index.chunks] == ["u/sso", "u/price"]


def test_search_ranks_by_cosine_similarity():
    index = two_page_index()
    hits = index.search(np.array([1.0, 0.0, 0.0]), k=2)
    assert [c.url for c, _ in hits] == ["u/sso", "u/price"]
    assert hits[0][1] > hits[1][1]
    assert index.search(np.array([1.0, 0.0, 0.0]), k=1)[0][0].url == "u/sso"


def test_save_and_load_round_trip(tmp_path):
    index = two_page_index()
    index.save(tmp_path / "index")
    loaded = DocsIndex.load(tmp_path / "index")

    assert loaded.chunks == index.chunks
    np.testing.assert_allclose(loaded.vectors, index.vectors)
    meta = json.loads((tmp_path / "index" / "meta.json").read_text())
    assert meta["chunks"] == 2


def test_load_refuses_vectors_that_dont_match_the_chunks(tmp_path):
    index = two_page_index()
    index.save(tmp_path / "index")
    np.save(tmp_path / "index" / "vectors.npy", np.zeros((3, 3)))
    with pytest.raises(ValueError, match="3 vectors for 2 chunks"):
        DocsIndex.load(tmp_path / "index")


# --- the tool -------------------------------------------------------------


def test_search_docs_returns_numbered_sources_and_citations():
    embedder = FakeEmbedder()
    tool = search_docs_tool(two_page_index(embedder), embedder, k=2)

    result = tool(query="How does SSO work?")

    assert result.content.startswith("[1] Enterprise › Single sign-on (u/sso)\n")
    assert "[2] Pricing › Prices (u/price)" in result.content
    assert result.citations == [
        Citation(title="Enterprise › Single sign-on", url="u/sso"),
        Citation(title="Pricing › Prices", url="u/price"),
    ]


def test_search_docs_refuses_an_empty_query():
    embedder = FakeEmbedder()
    tool = search_docs_tool(two_page_index(embedder), embedder)
    assert "empty" in tool(query="  ").content


# --- the real embedder, against a fake client ------------------------------


class RateLimited(Exception):
    status_code = 429


class FlakyClient:
    """Refuses the first call with a 429, then answers."""

    def __init__(self):
        self.calls = 0
        self.embeddings = self

    def create(self, model, input):
        from types import SimpleNamespace

        self.calls += 1
        if self.calls == 1:
            raise RateLimited("REQUEST_LIMIT_EXCEEDED")
        return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0]) for _ in input])


def test_the_embedder_waits_and_retries_when_rate_limited():
    from coati_agent.index import DatabricksEmbedder

    sleeps = []
    embedder = DatabricksEmbedder(FlakyClient(), "databricks-gte-large-en", sleep=sleeps.append)

    vectors = embedder.embed(["a", "b"])

    assert vectors.shape == (2, 2)
    assert embedder.client.calls == 2
    assert sleeps and sleeps[0] >= 1


def test_the_embedder_gives_up_after_its_retries():
    from coati_agent.index import DatabricksEmbedder

    class AlwaysLimited(FlakyClient):
        def create(self, model, input):
            raise RateLimited("REQUEST_LIMIT_EXCEEDED")

    embedder = DatabricksEmbedder(AlwaysLimited(), "e", sleep=lambda s: None, retries=3)
    with pytest.raises(RateLimited):
        embedder.embed(["a"])


def test_the_embedder_spaces_its_calls():
    from types import SimpleNamespace

    from coati_agent.index import DatabricksEmbedder

    class Client:
        def __init__(self):
            self.embeddings = self

        def create(self, model, input):
            return SimpleNamespace(data=[SimpleNamespace(embedding=[1.0]) for _ in input])

    now = [100.0]
    sleeps = []
    embedder = DatabricksEmbedder(
        Client(), "e", min_interval=1.5, sleep=sleeps.append, clock=lambda: now[0]
    )
    embedder.embed(["a"])
    now[0] += 0.5
    embedder.embed(["b"])

    assert sleeps == [1.0]
