"""A whole build: a public README is a page, an explainer stands in until there is one."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from portfolio_site.build import build
from portfolio_site.github import GitHub
from portfolio_site.models import Project, Site, Status
from tests.conftest import FakeFetch


def _project(number: str, slug: str, name: str, status: Status, repo: str | None) -> Project:
    return Project(
        number=number,
        slug=slug,
        name=name,
        one_liner=f"{name} does a thing.",
        technical_line="t",
        status=status,
        repo=repo,
    )


def _site() -> Site:
    return Site(
        title="T",
        tagline="tag",
        intro="intro",
        description="d",
        base_url="https://example.org",
        github="https://github.com/o",
        projects=(
            _project("01", "open", "Open", Status.SHIPPED, "o/open"),
            _project("02", "secret", "Secret", Status.PLANNED, "o/secret"),
            _project("03", "early", "Early", Status.PLANNED, "o/early"),
            _project("04", "norepo", "No Repo", Status.PLANNED, None),
        ),
    )


def test_build_pages_index_and_sitemap(tmp_path: Path, readme: str) -> None:
    fetch = FakeFetch(
        {"o/open": (False, readme), "o/secret": (True, "# S\n"), "o/early": (False, "# E\n")}
    )
    out = tmp_path / "dist"
    report = build(_site(), out, GitHub(fetch=fetch), today="2026-10-04")

    assert [p.path for p in report.pages] == ["/projects/open/", "/projects/early/"]
    assert report.skipped == ["o/secret"]
    assert report.warnings == ["o/early is public but projects.yaml still says 'planned'"]

    assert (out / "projects" / "open" / "index.html").exists()
    assert not (out / "projects" / "secret").exists()
    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "<h1>Open</h1>" in page
    assert "<td>0.42 (0.39, 0.45)</td>" in page
    assert "Example Project" not in page, "the README's own H1 is dropped"

    index = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/projects/open/"' in index
    assert "Secret" in index
    assert 'href="/projects/secret/"' not in index
    assert "No Repo" in index
    assert "Four projects, one standard." in index
    assert "Result published" in index
    assert "Planned" in index

    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://example.org/</loc>" in sitemap
    assert "https://example.org/projects/open/</loc>" in sitemap
    assert "secret" not in sitemap
    assert (out / "style.css").exists()
    assert (out / "fonts" / "inter-latin.woff2").exists()
    assert (out / "robots.txt").read_text(encoding="utf-8").endswith("sitemap.xml\n")


def test_a_live_demo_is_a_button_at_the_top_of_its_page(tmp_path: Path, readme: str) -> None:
    # The demo is the only thing on a project page a visitor can use rather than read, and
    # it spent a week as small print in the metadata row where nobody found it. It belongs
    # above the fold, and it belongs there once: the same link twice on one screen reads as
    # two different things.
    site = _site()
    with_demo = replace(
        site.projects[0],
        demo="https://demo.example",
        demo_note="A slider and six datasets.",
    )
    site = replace(site, projects=(with_demo, *site.projects[1:]))
    fetch = FakeFetch(
        {"o/open": (False, readme), "o/secret": (True, "# S\n"), "o/early": (False, "# E\n")}
    )
    out = tmp_path / "dist"
    build(site, out, GitHub(fetch=fetch), today="2026-10-04")

    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    hero = page.split('</div>\n  <div class="wrap narrow readme">', 1)[0]
    assert 'class="demo-button" href="https://demo.example"' in hero
    assert "Open the live demo" in hero
    assert "A slider and six datasets." in hero
    assert hero.count("https://demo.example") == 1, "the demo is linked once, not twice"
    assert "Live demo</span>" not in page, "the metadata row no longer repeats it"


def test_a_project_without_a_demo_gets_no_button(tmp_path: Path, readme: str) -> None:
    fetch = FakeFetch(
        {"o/open": (False, readme), "o/secret": (True, "# S\n"), "o/early": (False, "# E\n")}
    )
    out = tmp_path / "dist"
    build(_site(), out, GitHub(fetch=fetch), today="2026-10-04")

    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "demo-button" not in page
    assert "demo-cta" not in page


def test_nothing_on_a_wrap_cancels_its_gutter() -> None:
    """A class sharing an element with .wrap must not zero the side padding .wrap sets.

    `.readme` did, so a project page's body text sat one gutter left of its own hero. The
    two agreed on the column and disagreed on where it starts, which reads as a page built
    out of two templates rather than one.
    """
    root = Path("src/portfolio_site")
    stylesheet = (root / "static" / "style.css").read_text(encoding="utf-8")

    sharing: set[str] = set()
    for template in (root / "templates").glob("*.html"):
        for attr in re.findall(
            r'class="([^"]*\bwrap\b[^"]*)"', template.read_text(encoding="utf-8")
        ):
            sharing.update(name for name in attr.split() if name not in {"wrap", "narrow"})

    for name in sorted(sharing):
        for body in re.findall(rf"\.{re.escape(name)}\s*{{([^}}]*)}}", stylesheet):
            for value in re.findall(r"(?<![-\w])padding\s*:\s*([^;]+)", body):
                parts = value.split()
                sides = parts[1] if len(parts) > 1 else parts[0]
                assert sides.strip() not in {"0", "0px", "0rem"}, (
                    f".{name} sets 'padding: {value.strip()}', which cancels the gutter "
                    f"the wrap it sits on provides"
                )


def test_offline_build_has_index_but_no_pages(tmp_path: Path) -> None:
    report = build(_site(), tmp_path / "dist", None, today="2026-10-04")
    assert report.pages == []
    assert report.skipped == ["o/open", "o/secret", "o/early"]
    assert (tmp_path / "dist" / "index.html").exists()
    # No log entries: no log page, no nav link, no "Latest" strip.
    assert not (tmp_path / "dist" / "log").exists()
    index = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert 'href="/log/"' not in index and "What changed recently" not in index


def test_log_page_latest_strip_and_project_history(tmp_path: Path, readme: str) -> None:
    import datetime as dt

    from portfolio_site.models import LogEntry

    site = replace(
        _site(),
        log=(
            LogEntry(dt.date(2026, 10, 1), "01", Status.SHIPPED, "Open published its result."),
            LogEntry(dt.date(2026, 9, 7), "02", Status.PLANNED, "Secret planned."),
            LogEntry(dt.date(2026, 9, 1), "01", Status.BUILDING, "Open started."),
        ),
    )
    fetch = FakeFetch({"o/open": (False, readme), "o/secret": (True, "# S\n")})
    out = tmp_path / "dist"
    build(site, out, GitHub(fetch=fetch), today="2026-10-04")

    log = (out / "log" / "index.html").read_text(encoding="utf-8")
    assert (
        log.index("Open published its result.")
        < log.index("Secret planned.")
        < log.index("Open started.")
    ), "newest first"
    assert 'href="/projects/open/"' in log and 'href="/projects/secret/"' not in log
    assert "<strong>Secret</strong>" in log, "a project without a page is named, not linked"

    index = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/log/"' in index and "What changed recently" in index
    assert "Open published its result." in index

    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "Open started." in page and "Open published its result." in page
    assert "Secret planned." not in page, "a page shows only its own history"

    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://example.org/log/</loc>" in sitemap


EXPLAINER = "The first screen.\n\n<!-- more -->\n\n## Deeper\n\nThe rest of it.\n"


def _explained(*numbers: str) -> Site:
    """The usual site, with an explainer added to the projects named."""
    site = _site()
    projects = tuple(
        replace(p, explainer=EXPLAINER) if p.number in numbers else p for p in site.projects
    )
    return replace(site, projects=projects)


def test_an_explainer_is_the_page_until_the_repository_is_public(
    tmp_path: Path, readme: str
) -> None:
    fetch = FakeFetch({"o/open": (False, readme), "o/secret": (True, "# S\n")})
    out = tmp_path / "dist"
    # 02 has a private repository, 04 has no repository at all. Both explain themselves.
    report = build(_explained("02", "04"), out, GitHub(fetch=fetch), today="2026-10-04")

    assert [p.path for p in report.pages] == [
        "/projects/open/",
        "/projects/secret/",
        "/projects/norepo/",
    ]
    assert report.skipped == ["o/secret", "o/early"], "a private repository is still skipped"
    assert "<- explainer" in report.summary()

    page = (out / "projects" / "secret" / "index.html").read_text(encoding="utf-8")
    assert "<h1>Secret</h1>" in page
    assert "The first screen." in page
    assert '<details class="more">' in page and "The rest of it." in page
    assert "hand-written explanation rather than a results table" in page
    assert "github.com/o/secret" not in page, "a private repository is never linked"
    assert "Last updated" not in page, "there is no repository to date the page from"

    index = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/projects/secret/"' in index, "the card's title opens the explainer"
    assert index.count('href="/projects/secret/"') == 1, (
        "the title is the only link to the page; the links row does not repeat it"
    )
    assert "Click a project's name to open its page" in index, "and the index says so once"
    assert ">Repository<" not in index, (
        "a card repeats nothing the page already carries; the repository is on the page"
    )
    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert 'href="https://github.com/o/open">o/open<' in page, "which is where it is"
    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://example.org/projects/norepo/</loc>" in sitemap


def test_a_public_readme_replaces_the_explainer(tmp_path: Path, readme: str) -> None:
    fetch = FakeFetch({"o/open": (False, readme)})
    out = tmp_path / "dist"
    build(_explained("01"), out, GitHub(fetch=fetch), today="2026-10-04")

    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "<td>0.42 (0.39, 0.45)</td>" in page, "the README is the page"
    assert "The first screen." not in page and "<details" not in page
    assert "hand-written explanation rather than a results table" not in page


def test_an_explainer_without_a_marker_shows_all_at_once(tmp_path: Path) -> None:
    site = _site()
    projects = tuple(
        replace(p, explainer="One screen, no more.\n") if p.number == "04" else p
        for p in site.projects
    )
    out = tmp_path / "dist"
    build(replace(site, projects=projects), out, None, today="2026-10-04")
    page = (out / "projects" / "norepo" / "index.html").read_text(encoding="utf-8")
    assert "One screen, no more." in page
    assert "<details" not in page, "nothing to disclose, so no disclosure"


def test_a_project_page_shows_two_updates_and_folds_the_rest_away(tmp_path: Path) -> None:
    """A project accumulates updates for a year; its page still has one job, the result.

    Project 01 had eight entries and project 04 seven, all printed above the README, so the
    thing a reader came for started below the fold. The two newest stay, the rest go behind a
    disclosure. No script is involved: it is the <details> element the explainer already uses.
    """
    import datetime as dt

    from portfolio_site.models import LogEntry

    site = replace(
        _site(),
        log=(
            LogEntry(dt.date(2026, 10, 5), "01", Status.SHIPPED, "Newest thing."),
            LogEntry(dt.date(2026, 10, 4), "01", Status.BUILDING, "Second thing."),
            LogEntry(dt.date(2026, 10, 3), "01", Status.BUILDING, "Third thing."),
            LogEntry(dt.date(2026, 10, 2), "01", Status.BUILDING, "Fourth thing."),
        ),
    )
    out = tmp_path / "dist"
    build(
        site,
        out,
        GitHub(fetch=FakeFetch({"o/open": (False, "# Open\n\nBody.\n")})),
        today="2026-10-06",
    )
    page = (out / "projects" / "open" / "index.html").read_text(encoding="utf-8")

    before, _, behind = page.partition('<details class="history-more">')
    assert "Newest thing." in before and "Second thing." in before
    assert "Third thing." not in before and "Fourth thing." not in before
    assert "Third thing." in behind and "Fourth thing." in behind
    assert "<summary>2 earlier updates</summary>" in behind


def test_a_short_history_gets_no_disclosure_and_one_earlier_update_is_singular(
    tmp_path: Path,
) -> None:
    """Two entries is the whole history, so there is nothing to fold and no control to show.
    Three entries leaves exactly one behind the disclosure, where "1 earlier updates" would
    be the giveaway that the count was never looked at."""
    import datetime as dt

    from portfolio_site.models import LogEntry

    readme = GitHub(fetch=FakeFetch({"o/open": (False, "# Open\n\nBody.\n")}))
    two = (
        LogEntry(dt.date(2026, 10, 5), "01", Status.SHIPPED, "Newest thing."),
        LogEntry(dt.date(2026, 10, 4), "01", Status.BUILDING, "Second thing."),
    )
    build(replace(_site(), log=two), tmp_path / "a", readme, today="2026-10-06")
    page = (tmp_path / "a" / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "history-more" not in page and "Second thing." in page

    third = (*two, LogEntry(dt.date(2026, 10, 3), "01", Status.BUILDING, "Third thing."))
    build(replace(_site(), log=third), tmp_path / "b", readme, today="2026-10-06")
    page = (tmp_path / "b" / "projects" / "open" / "index.html").read_text(encoding="utf-8")
    assert "<summary>1 earlier update</summary>" in page


def test_the_bar_and_the_footer_are_the_same_width_on_every_page(
    tmp_path: Path, readme: str
) -> None:
    """The site's frame holds still when the reader clicks into a project.

    The bar and the footer once followed the reading page's narrower column, so the whole
    page, logo and all, jumped inwards by ten rem a side on every click into a project and
    back out again on the way home. A reading column that is narrower than the frame is a
    choice; a frame that resizes itself under the reader is not.
    """
    fetch = FakeFetch(
        {"o/open": (False, readme), "o/secret": (True, "# S\n"), "o/early": (False, "# E\n")}
    )
    out = tmp_path / "dist"
    build(_site(), out, GitHub(fetch=fetch), today="2026-10-04")

    pages = sorted(out.rglob("index.html"))
    assert len(pages) > 1, "a one-page build cannot show the frame moving"
    for page in pages:
        where = page.relative_to(out).as_posix()
        html = page.read_text(encoding="utf-8")
        bar = html.split('<header class="top">', 1)[1].split("</header>", 1)[0]
        foot = html.split("<footer>", 1)[1].split("</footer>", 1)[0]
        for part, name in ((bar, "bar"), (foot, "footer")):
            outer = re.search(r'<div class="([^"]*)"', part)
            assert outer is not None, f"{where}: no wrap in the {name}"
            assert outer.group(1) == "wrap", (
                f"{where}: the {name} is on '{outer.group(1)}' rather than the site-wide "
                f"'wrap', so the frame changes width between pages"
            )


def test_a_wide_table_is_not_held_to_the_reading_measure() -> None:
    """The results table a reader came for is seven columns wide and 46rem is not enough.

    `.readme table` caps itself at its column, so the rule that lets a table out again has
    to lift that cap as well as set a width. It did not, once, and the breakout did nothing
    at all while looking exactly like it should have worked.
    """
    stylesheet = (Path("src/portfolio_site") / "static" / "style.css").read_text(encoding="utf-8")
    body = re.search(r"\.readme > table[^{]*{([^}]*)}", stylesheet)
    assert body is not None, "no breakout rule for a readme table"
    assert "max-width: none" in body.group(1), (
        "the breakout sets a width but leaves '.readme table { max-width: 100% }' capping it"
    )
