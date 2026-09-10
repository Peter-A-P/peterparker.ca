"""The site's data: what ``projects.yaml`` may contain and how it is validated."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from portfolio_site.render import MORE_MARKER

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
MAX_THEMES = 8  # the stylesheet carries one filter rule per slot


class Status(StrEnum):
    """Where a project stands, as shown on its card."""

    LIVE = "live"  # running and publicly reachable
    SHIPPED = "shipped"  # repository public with a measured result
    BUILDING = "building"  # being built now
    PLANNED = "planned"  # planned, nothing public yet


STATUS_LABEL: dict[Status, str] = {
    Status.LIVE: "Live",
    Status.SHIPPED: "Result published",
    Status.BUILDING: "In progress",
    Status.PLANNED: "Planned",
}


@dataclass(frozen=True, slots=True)
class Project:
    """One card on the index and, when its repository is public, one page."""

    number: str
    slug: str
    name: str
    one_liner: str
    technical_line: str
    status: Status
    repo: str | None = None  # "owner/name" on GitHub
    demo: str | None = None  # URL of the live demo, when publicly reachable
    note: str | None = None  # one short public sentence shown under the links
    themes: tuple[str, ...] = ()  # slugs from Site.themes; drive the index filters
    explainer: str | None = None  # Markdown, this project's page until its repository is public

    @property
    def repo_url(self) -> str | None:
        """The repository's GitHub URL, or ``None`` when there is no repository."""
        return f"https://github.com/{self.repo}" if self.repo else None


@dataclass(frozen=True, slots=True)
class LogEntry:
    """One dated change of a project's status. Entries are never edited after the fact; a
    wrong entry gets a later entry that corrects it."""

    date: dt.date
    number: str  # the project's number in this file
    status: Status  # the status the project moved to
    note: str  # one public sentence on what happened


@dataclass(frozen=True, slots=True)
class Site:
    """Everything the templates need that is not a project."""

    title: str
    tagline: str
    intro: str
    description: str
    base_url: str
    github: str
    projects: tuple[Project, ...]
    themes: dict[str, str] = field(default_factory=dict)  # slug -> label, in display order
    log: tuple[LogEntry, ...] = ()  # newest first

    def project(self, number: str) -> Project:
        """The project with this number."""
        for p in self.projects:
            if p.number == number:
                return p
        raise KeyError(number)

    def log_for(self, number: str) -> tuple[LogEntry, ...]:
        """This project's entries, newest first."""
        return tuple(e for e in self.log if e.number == number)

    def theme_slot(self, slug: str) -> int:
        """1-based position of a theme; the stylesheet has one filter rule per slot."""
        return list(self.themes).index(slug) + 1

    def theme_count(self, slug: str) -> int:
        """How many projects carry a theme."""
        return sum(slug in p.themes for p in self.projects)


class DataError(ValueError):
    """``projects.yaml`` is not usable."""


def _require(mapping: dict[str, Any], key: str, where: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{where}: '{key}' is required and must be a non-empty string")
    return value.strip()


def _optional(mapping: dict[str, Any], key: str, where: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{where}: '{key}' must be a non-empty string when present")
    return value.strip()


def _explainer(raw: dict[str, Any], where: str, base: Path) -> str | None:
    """Read the project's explainer: the page it gets until its repository is public.

    ``projects.yaml`` names a Markdown file beside itself. The text is read here, so the
    build itself opens no files and a bad path fails validation rather than the build.
    """
    name = _optional(raw, "explainer", where)
    if name is None:
        return None
    path = (base / name).resolve()
    if base not in path.parents:
        raise DataError(f"{where}: explainer '{name}' must sit inside the site repository")
    if not path.is_file():
        raise DataError(f"{where}: explainer '{name}' is not a file")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise DataError(f"{where}: explainer '{name}' is empty")
    if text.startswith("# "):
        raise DataError(
            f"{where}: explainer '{name}' must not open with an H1; the page prints the "
            "project's name itself"
        )
    markers = text.count(MORE_MARKER)
    if markers > 1:
        raise DataError(
            f"{where}: explainer '{name}' has {markers} '{MORE_MARKER}' markers; one at most"
        )
    return text


def _project(raw: dict[str, Any], index: int, base: Path) -> Project:
    where = f"projects[{index}]"
    number = _require(raw, "number", where)
    slug = _require(raw, "slug", where)
    if not SLUG_RE.match(slug):
        raise DataError(f"{where}: slug '{slug}' must be lower-case letters, digits and hyphens")
    status_raw = _require(raw, "status", where)
    try:
        status = Status(status_raw)
    except ValueError as exc:
        allowed = ", ".join(s.value for s in Status)
        raise DataError(f"{where}: status '{status_raw}' is not one of {allowed}") from exc
    repo = _optional(raw, "repo", where)
    if repo is not None and not REPO_RE.match(repo):
        raise DataError(f"{where}: repo '{repo}' must be 'owner/name'")
    demo = _optional(raw, "demo", where)
    if demo is not None and not demo.startswith("https://"):
        raise DataError(f"{where}: demo '{demo}' must be an https URL")
    themes_raw = raw.get("themes", [])
    if not isinstance(themes_raw, list) or not all(isinstance(t, str) for t in themes_raw):
        raise DataError(f"{where}: 'themes' must be a list of theme slugs")
    return Project(
        number=number,
        slug=slug,
        name=_require(raw, "name", where),
        one_liner=_require(raw, "one_liner", where),
        technical_line=_require(raw, "technical_line", where),
        status=status,
        repo=repo,
        demo=demo,
        note=_optional(raw, "note", where),
        themes=tuple(themes_raw),
        explainer=_explainer(raw, where, base),
    )


def load_site(path: Path) -> Site:
    """Read and validate ``projects.yaml``."""
    base = path.resolve().parent
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataError(f"{path}: top level must be a mapping")
    site_raw = raw.get("site")
    if not isinstance(site_raw, dict):
        raise DataError(f"{path}: 'site' mapping is required")
    projects_raw = raw.get("projects")
    if not isinstance(projects_raw, list) or not projects_raw:
        raise DataError(f"{path}: 'projects' must be a non-empty list")
    projects: list[Project] = []
    for i, p in enumerate(projects_raw):
        if not isinstance(p, dict):
            raise DataError(f"projects[{i}] must be a mapping")
        projects.append(_project(p, i, base))
    _check_unique(projects, "slug")
    _check_unique(projects, "number")
    themes = _themes(site_raw.get("themes"), path)
    for p in projects:
        for t in p.themes:
            if t not in themes:
                raise DataError(f"{p.slug}: unknown theme '{t}'")
    return Site(
        title=_require(site_raw, "title", "site"),
        tagline=_require(site_raw, "tagline", "site"),
        intro=_require(site_raw, "intro", "site"),
        description=_require(site_raw, "description", "site"),
        base_url=_require(site_raw, "base_url", "site").rstrip("/"),
        github=_require(site_raw, "github", "site"),
        projects=tuple(projects),
        themes=themes,
        log=_log(raw.get("log"), projects),
    )


def _log(raw: object, projects: list[Project]) -> tuple[LogEntry, ...]:
    """The status log: a list of {date, project, status, note}, returned newest first.

    The latest entry for a project must agree with the project's current status, so the
    log and the cards cannot drift apart.
    """
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise DataError("'log' must be a list of entries")
    numbers = {p.number: p for p in projects}
    entries: list[LogEntry] = []
    for i, e in enumerate(raw):
        where = f"log[{i}]"
        if not isinstance(e, dict):
            raise DataError(f"{where} must be a mapping")
        date_raw = e.get("date")
        if isinstance(date_raw, dt.date):
            date = date_raw
        else:
            try:
                date = dt.date.fromisoformat(str(date_raw))
            except ValueError as exc:
                raise DataError(f"{where}: date '{date_raw}' must be YYYY-MM-DD") from exc
        number = _require(e, "project", where)
        if number not in numbers:
            raise DataError(f"{where}: project '{number}' is not in 'projects'")
        status_raw = _require(e, "status", where)
        try:
            status = Status(status_raw)
        except ValueError as exc:
            allowed = ", ".join(s.value for s in Status)
            raise DataError(f"{where}: status '{status_raw}' is not one of {allowed}") from exc
        note = _require(e, "note", where)
        if not note.endswith("."):
            raise DataError(f"{where}: note must be a sentence ending in a full stop")
        entries.append(LogEntry(date=date, number=number, status=status, note=note))
    entries.sort(key=lambda e: e.date, reverse=True)
    latest: dict[str, LogEntry] = {}
    for e in reversed(entries):  # oldest first, so the last write is the newest
        latest[e.number] = e
    for number, e in latest.items():
        if numbers[number].status is not e.status:
            raise DataError(
                f"log: the latest entry for project {number} says '{e.status}' but the project's "
                f"status is '{numbers[number].status}'; change both in the same edit"
            )
    return tuple(entries)


def _themes(raw: object, path: Path) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict) or not all(
        isinstance(k, str) and SLUG_RE.match(k) and isinstance(v, str) and v.strip()
        for k, v in raw.items()
    ):
        raise DataError(f"{path}: 'site.themes' must map slugs to non-empty labels")
    if len(raw) > MAX_THEMES:
        raise DataError(f"{path}: at most {MAX_THEMES} themes are supported")
    return {k: v.strip() for k, v in raw.items()}


def _check_unique(projects: list[Project], attr: str) -> None:
    seen: set[str] = set()
    for p in projects:
        value = str(getattr(p, attr))
        if value in seen:
            raise DataError(f"duplicate {attr} '{value}' in projects")
        seen.add(value)
