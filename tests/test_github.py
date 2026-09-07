"""Only verifiably public repositories come back."""

from __future__ import annotations

from datetime import date

import pytest

from portfolio_site.github import GitHub, urllib_fetch
from tests.conftest import FakeFetch


def test_missing_repo_is_none() -> None:
    gh = GitHub(fetch=FakeFetch({}))
    assert gh.public_repo("o/missing") is None


def test_private_repo_is_none_and_readme_is_never_requested() -> None:
    fetch = FakeFetch({"o/secret": (True, "# Secret\n")})
    assert GitHub(fetch=fetch).public_repo("o/secret") is None
    assert fetch.calls == ["https://api.github.com/repos/o/secret"]


def test_public_repo_returns_metadata_and_readme() -> None:
    fetch = FakeFetch({"o/open": (False, "# Open\n\nBody.\n")})
    repo = GitHub(token="t", fetch=fetch).public_repo("o/open")  # noqa: S106 - fake token
    assert repo is not None
    assert repo.html_url == "https://github.com/o/open"
    assert repo.default_branch == "main"
    assert repo.pushed_on == date(2026, 10, 3)
    assert repo.readme_markdown == "# Open\n\nBody.\n"


def test_real_fetch_refuses_other_hosts() -> None:
    with pytest.raises(ValueError, match="outside the GitHub API"):
        urllib_fetch("https://example.org/", {})
