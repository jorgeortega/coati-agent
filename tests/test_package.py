import coati_agent


def test_version_matches_pyproject():
    import tomllib
    from pathlib import Path

    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert coati_agent.__version__ == pyproject["project"]["version"]
