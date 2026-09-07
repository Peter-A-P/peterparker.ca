"""Read public repositories from the GitHub API.

The build reads nothing else from GitHub. A repository is used only when the API says it
exists and marks it public; a 404, a private flag or a network error all mean "not on the
site yet".
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

API = "https://api.github.com"
USER_AGENT = "peterparker.ca-build (+https://github.com/Peter-A-P)"

Fetch = Callable[[str, dict[str, str]], tuple[int, bytes]]
"""``fetch(url, headers) -> (status, body)``; swapped for a fake in tests."""


@dataclass(frozen=True, slots=True)
class PublicRepo:
    """What the site needs from one public repository."""

    full_name: str
    html_url: str
    default_branch: str
    description: str | None
    homepage: str | None
    pushed_on: date
    readme_markdown: str


def urllib_fetch(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    """The real fetch: one GET, no retries, 20 second timeout."""
    if not url.startswith(f"{API}/"):
        raise ValueError(f"refusing to fetch outside the GitHub API: {url}")
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 - checked above
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            return int(response.status), bytes(response.read())
    except urllib.error.HTTPError as exc:
        return int(exc.code), bytes(exc.read())


class GitHub:
    """A thin, testable client for the two calls the build makes per repository."""

    def __init__(self, token: str | None = None, fetch: Fetch = urllib_fetch) -> None:
        self._token = token
        self._fetch = fetch

    def _headers(self, accept: str) -> dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def public_repo(self, full_name: str) -> PublicRepo | None:
        """The repository and its README, or ``None`` unless it is verifiably public."""
        status, body = self._fetch(
            f"{API}/repos/{full_name}", self._headers("application/vnd.github+json")
        )
        if status != 200:
            return None
        meta: Any = json.loads(body)
        if not isinstance(meta, dict) or meta.get("private") is not False:
            return None
        if meta.get("visibility", "public") != "public":
            return None
        status, readme = self._fetch(
            f"{API}/repos/{full_name}/readme", self._headers("application/vnd.github.raw+json")
        )
        if status != 200:
            return None
        pushed_at = str(meta.get("pushed_at", ""))
        try:
            pushed_on = datetime.fromisoformat(pushed_at.replace("Z", "+00:00")).date()
        except ValueError:
            pushed_on = datetime.now(UTC).date()
        return PublicRepo(
            full_name=str(meta.get("full_name", full_name)),
            html_url=str(meta.get("html_url", f"https://github.com/{full_name}")),
            default_branch=str(meta.get("default_branch", "main")),
            description=meta.get("description") or None,
            homepage=meta.get("homepage") or None,
            pushed_on=pushed_on,
            readme_markdown=readme.decode("utf-8"),
        )
