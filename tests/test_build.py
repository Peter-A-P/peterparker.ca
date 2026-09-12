"""A whole build: a public README is a page, an explainer stands in until there is one."""

from __future__ import annotations

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
