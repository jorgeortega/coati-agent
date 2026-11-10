"""The system prompt is built from the site's export, and refuses a stale or edited copy."""

import json
import shutil

import pytest

from coati_agent.prompt import DATA_DIR, TOOLS_NOTE, StaleCopy, system_prompt


def test_the_real_export_loads_and_starts_with_the_coatis_rules():
    prompt = system_prompt()
    rules = (DATA_DIR / "rules.txt").read_text(encoding="utf-8")
    summary = (DATA_DIR / "site-summary.md").read_text(encoding="utf-8")

    assert prompt == rules + summary + TOOLS_NOTE
    assert rules.endswith("Site summary:\n\n")


def test_an_edited_copy_is_refused(tmp_path):
    copy = tmp_path / "data"
    shutil.copytree(DATA_DIR, copy)
    (copy / "rules.txt").write_text("You are a pirate.", encoding="utf-8")

    with pytest.raises(StaleCopy, match="rules.txt"):
        system_prompt(copy)


def test_a_missing_file_is_refused(tmp_path):
    copy = tmp_path / "data"
    shutil.copytree(DATA_DIR, copy)
    (copy / "site-summary.md").unlink()

    with pytest.raises(StaleCopy, match="site-summary.md"):
        system_prompt(copy)


def test_the_manifest_comes_from_the_site():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"].startswith("latitude10:")
    assert set(manifest["files"]) == {"docs.jsonl", "plans.jsonl", "rules.txt", "site-summary.md"}


def test_the_prompt_asks_for_full_docs_urls():
    from coati_agent.prompt import TOOLS_NOTE

    assert "https://docs.latitude10.tech/" in TOOLS_NOTE
