"""Markdown to HTML: a repository README, or a project's hand-written explainer."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

H1_RE = re.compile(r"^# (.+?)\s*$", re.M)

MORE_MARKER = "<!-- more -->"
"""Separates an explainer's first screen from the part behind "Learn more".

The split happens on the raw text, before rendering, so the marker never reaches the
renderer, which escapes raw HTML rather than passing it through.
"""


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


def split_more(markdown: str) -> tuple[str, str]:
    """Split an explainer on its ``MORE_MARKER`` into a first screen and the rest.

    The rest is empty when the marker is absent, in which case the whole explainer shows
    at once and the page grows no disclosure.
    """
    intro, _, rest = markdown.partition(MORE_MARKER)
    return intro.strip(), rest.strip()


COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCES = ("```", "~~~")


def _segments(markdown: str) -> list[tuple[bool, str]]:
    """Split Markdown into (is_fenced_code, text) runs, so a rule can skip code."""
    segments: list[tuple[bool, str]] = []
    buffer: list[str] = []
    fence: str | None = None
    for line in markdown.splitlines(keepends=True):
        opener = line.lstrip()[:3]
        if fence is None and opener in FENCES:
            segments.append((False, "".join(buffer)))
            buffer = [line]
            fence = opener
        elif fence is not None and opener == fence:
            buffer.append(line)
            segments.append((True, "".join(buffer)))
            buffer, fence = [], None
        else:
            buffer.append(line)
    segments.append((fence is not None, "".join(buffer)))
    return segments


def strip_html_comments(markdown: str) -> str:
    """Remove HTML comments, except inside fenced code where they are the content.

    The renderer escapes raw HTML instead of passing it through, so a comment that
    reaches it is printed on the page as text. READMEs use comments as machine markers:
    project 02 writes its results table between `<!-- mselect:results:start -->` and its
    end marker, and a reader should see neither the marker nor an escaped version of it.
    """
    return "".join(text if code else COMMENT_RE.sub("", text) for code, text in _segments(markdown))


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


def _parser() -> MarkdownIt:
    """The one Markdown configuration the site uses.

    Raw HTML is escaped rather than passed through: the site serves no scripts and its
    Content-Security-Policy says so. Tables are enabled because Rule A's results table is
    the point of a project page.
    """
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    return md


def render_readme(markdown: str, repo_html_url: str, branch: str) -> str:
    """Render a README body to HTML, with repository-relative links rewritten to GitHub."""
    md = _parser()
    tokens = md.parse(strip_html_comments(markdown))
    _walk(tokens, repo_html_url, branch)
    return str(md.renderer.render(tokens, md.options, {}))


def render_markdown(markdown: str) -> str:
    """Render hand-written site Markdown, such as a project's explainer.

    Nothing is rewritten: there is no repository to rewrite towards, so an explainer's
    links are absolute or site-relative.
    """
    return str(_parser().render(strip_html_comments(markdown)))
