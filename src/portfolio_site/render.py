"""Markdown to HTML for a README, with links that keep pointing at the repository."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

H1_RE = re.compile(r"^# (.+?)\s*$", re.M)


def split_title(markdown: str) -> tuple[str | None, str]:
    """Return the first H1 and the Markdown without it.

    The page template prints the project's name itself, so the README's title would
    otherwise appear twice.
    """
    match = H1_RE.search(markdown)
    if match is None:
        return None, markdown
    rest = markdown[: match.start()] + markdown[match.end() :]
    return match.group(1).strip(), rest.lstrip("\n")


def _is_relative(href: str) -> bool:
    if not href or href.startswith(("#", "//", "mailto:")):
        return False
    return not urlsplit(href).scheme


def rewrite_relative(href: str, repo_html_url: str, branch: str, *, raw: bool = False) -> str:
    """Point a repository-relative link at GitHub so it still resolves from the site."""
    if not _is_relative(href):
        return href
    kind = "raw" if raw else "blob"
    return f"{repo_html_url}/{kind}/{branch}/{href.lstrip('./')}"


def _walk(tokens: list[Token], repo_html_url: str, branch: str) -> None:
    for token in tokens:
        if token.type == "link_open":
            href = token.attrGet("href")
            if isinstance(href, str):
                token.attrSet("href", rewrite_relative(href, repo_html_url, branch))
        elif token.type == "image":
            src = token.attrGet("src")
            if isinstance(src, str):
                token.attrSet("src", rewrite_relative(src, repo_html_url, branch, raw=True))
        if token.children:
            _walk(token.children, repo_html_url, branch)


def render_readme(markdown: str, repo_html_url: str, branch: str) -> str:
    """Render a README body to HTML.

    Raw HTML in the README is escaped rather than passed through: the site serves no
    scripts and its Content-Security-Policy says so. Tables are enabled because Rule A's
    results table is the point of the page.
    """
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    tokens = md.parse(markdown)
    _walk(tokens, repo_html_url, branch)
    return str(md.renderer.render(tokens, md.options, {}))
