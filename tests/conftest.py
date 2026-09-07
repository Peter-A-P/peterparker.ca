"""Shared fixtures and fakes for the tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def readme() -> str:
    return (FIXTURES / "readme_rule_a.md").read_text(encoding="utf-8")


class FakeFetch:
    """Stands in for ``urllib_fetch``: knows some repositories, records what was asked.

    ``repos`` maps ``owner/name`` to ``(is_private, readme_markdown)``.
    """

    def __init__(self, repos: dict[str, tuple[bool, str]]) -> None:
        self.repos = repos
        self.calls: list[str] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        self.calls.append(url)
        prefix = "https://api.github.com/repos/"
        assert url.startswith(prefix)
        rest = url[len(prefix) :]
        wants_readme = rest.endswith("/readme")
        full_name = rest.removesuffix("/readme")
        if full_name not in self.repos:
            return 404, b'{"message":"Not Found"}'
        private, readme = self.repos[full_name]
        if wants_readme:
            assert headers["Accept"] == "application/vnd.github.raw+json"
            return 200, readme.encode("utf-8")
        meta = {
            "full_name": full_name,
            "html_url": f"https://github.com/{full_name}",
            "default_branch": "main",
            "private": private,
            "visibility": "private" if private else "public",
            "description": "desc",
            "homepage": None,
            "pushed_at": "2026-10-03T12:00:00Z",
        }
        return 200, json.dumps(meta).encode("utf-8")
