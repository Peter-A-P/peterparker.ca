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


def test_a_readmes_machine_markers_never_reach_the_page() -> None:
    """The bug this fixes: project 02 writes its results table between a pair of HTML
    comments, the parser escapes raw HTML rather than passing it through, and the marker
    was printed on the page as text directly under the heading it belongs to."""
    readme = (
        "## Result\n\n"
        "<!-- mselect:results:start -->\n"
        "| Measure | Result |\n|---|---|\n| tau | 0.778 (0.716 to 0.832) |\n"
        "<!-- mselect:results:end -->\n\n"
        "After the table.\n"
    )
    html = render_readme(readme, REPO, "main")
    assert "mselect:results" not in html
    assert "&lt;!--" not in html and "<!--" not in html
    assert "<td>0.778 (0.716 to 0.832)</td>" in html
    assert "After the table." in html


def test_a_comment_inside_a_fence_is_content_and_survives() -> None:
    readme = "```html\n<!-- keep me: this is the example -->\n```\n\n<!-- drop me -->\n\nText.\n"
    html = render_readme(readme, REPO, "main")
    assert "keep me" in html
    assert "drop me" not in html


def test_stripping_comments_does_not_stop_raw_html_being_escaped() -> None:
    html = render_readme("<!-- x -->\n\n<script>alert(1)</script>\n", REPO, "main")
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_markers_between_the_separator_and_the_rows_do_not_split_the_table() -> None:
    """Where the markers actually sit in 02's and 03's READMEs, which is not where the test
    above put them.

    The monthly job rewrites only the rows, so the markers go between the header separator
    and the first row rather than around the whole table. Stripping a marker used to leave
    its line behind as a blank line, and a blank line closes a table, so the page showed a
    header with no body followed by the rows as a paragraph of pipes. Every results table on
    the site was broken this way, and GitHub rendered the same files correctly, so the source
    looked fine.
    """
    readme = (
        "## Result\n\n"
        "| Run | Arm | Accuracy |\n"
        "|---|---|---|\n"
        "<!-- drift:start -->\n"
        "| 2026-09 | anthropic-alias | 95.0% (92.9% to 96.9%, n = 420) |\n"
        "| 2026-09 | openai-snapshot | 94.8% (92.6% to 96.9%, n = 420) |\n"
        "<!-- drift:end -->\n\n"
        "After the table.\n"
    )
    html = render_readme(readme, REPO, "main")
    assert "drift:start" not in html and "drift:end" not in html
    # Both rows are table cells, not a stray paragraph of pipes.
    assert "<td>anthropic-alias</td>" in html
    assert "<td>openai-snapshot</td>" in html
    assert "<tbody>" in html
    assert "<p>| 2026-09" not in html
    assert html.count("<table>") == 1
    assert "After the table." in html
