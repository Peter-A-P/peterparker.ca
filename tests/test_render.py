"""Markdown becomes HTML: a README pointing at its repository, or an explainer."""

from __future__ import annotations

from portfolio_site.render import (
    render_markdown,
    render_readme,
    rewrite_relative,
    split_more,
    split_title,
)

REPO = "https://github.com/Peter-A-P/example"


def test_split_title_removes_only_the_h1(readme: str) -> None:
    title, rest = split_title(readme)
    assert title == "Example Project"
    assert not rest.startswith("#")
    assert rest.startswith("One line that says")
    assert "## Result" in rest


def test_split_title_without_h1_returns_none() -> None:
    assert split_title("just text\n") == (None, "just text\n")


def test_rewrite_relative_links_and_leaves_the_rest() -> None:
    assert rewrite_relative("PLAN.md", REPO, "main") == f"{REPO}/blob/main/PLAN.md"
    assert rewrite_relative("./docs/x.md", REPO, "main") == f"{REPO}/blob/main/docs/x.md"
    assert rewrite_relative("img.png", REPO, "main", raw=True) == f"{REPO}/raw/main/img.png"
    for untouched in ("https://a.b/c", "#result", "mailto:x@y.z", "//cdn.example/x"):
        assert rewrite_relative(untouched, REPO, "main") == untouched


def test_render_readme_tables_links_images_and_no_raw_html(readme: str) -> None:
    _, body = split_title(readme)
    html = render_readme(body, REPO, "main")
    assert "<table>" in html
    assert "<td>0.42 (0.39, 0.45)</td>" in html
    assert f'href="{REPO}/blob/main/PLAN.md"' in html
    assert f'href="{REPO}/blob/main/docs/rejected.md"' in html
    assert f'src="{REPO}/raw/main/docs/chart.png"' in html
    assert 'href="https://example.org/x"' in html
    assert 'href="#result"' in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_split_more_splits_once_and_survives_a_missing_marker() -> None:
    assert split_more("The first screen.\n\n<!-- more -->\n\nThe rest.\n") == (
        "The first screen.",
        "The rest.",
    )
    assert split_more("Only ever one screen.\n") == ("Only ever one screen.", "")
    assert split_more("<!-- more -->\n\nEverything behind the disclosure.") == (
        "",
        "Everything behind the disclosure.",
    )


def test_render_markdown_keeps_tables_and_still_escapes_raw_html() -> None:
    html = render_markdown("| a | b |\n|---|---|\n| 1 | 2 |\n\n<script>x</script>\n")
    assert "<table>" in html and "<td>1</td>" in html
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_render_markdown_leaves_links_alone() -> None:
    html = render_markdown("[a](https://example.org/x) and [b](/log/)\n")
    assert 'href="https://example.org/x"' in html and 'href="/log/"' in html
