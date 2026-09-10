"""A whole build: public repositories get pages, private ones do not."""

from __future__ import annotations

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
    from dataclasses import replace

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
