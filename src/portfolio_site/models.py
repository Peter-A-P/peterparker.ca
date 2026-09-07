"""The site's data: what ``projects.yaml`` may contain and how it is validated."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


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


class Group(StrEnum):
    """The two lists on the index page."""

    PORTFOLIO = "portfolio"
    ALONGSIDE = "alongside"


@dataclass(frozen=True, slots=True)
class Project:
    """One card on the index and, when its repository is public, one page."""

    number: str
    slug: str
    name: str
    one_liner: str
    technical_line: str
    status: Status
    group: Group
    repo: str | None = None  # "owner/name" on GitHub
    demo: str | None = None  # URL of the live demo, when publicly reachable
    note: str | None = None  # one short public sentence shown under the links

    @property
    def repo_url(self) -> str | None:
        """The repository's GitHub URL, or ``None`` when there is no repository."""
        return f"https://github.com/{self.repo}" if self.repo else None


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

    def in_group(self, group: Group) -> list[Project]:
        """Projects in one group, in the order they appear in the file."""
        return [p for p in self.projects if p.group is group]


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


def _project(raw: dict[str, Any], index: int) -> Project:
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
    group_raw = _require(raw, "group", where)
    try:
        group = Group(group_raw)
    except ValueError as exc:
        allowed = ", ".join(g.value for g in Group)
        raise DataError(f"{where}: group '{group_raw}' is not one of {allowed}") from exc
    repo = _optional(raw, "repo", where)
    if repo is not None and not REPO_RE.match(repo):
        raise DataError(f"{where}: repo '{repo}' must be 'owner/name'")
    demo = _optional(raw, "demo", where)
    if demo is not None and not demo.startswith("https://"):
        raise DataError(f"{where}: demo '{demo}' must be an https URL")
    return Project(
        number=number,
        slug=slug,
        name=_require(raw, "name", where),
        one_liner=_require(raw, "one_liner", where),
        technical_line=_require(raw, "technical_line", where),
        status=status,
        group=group,
        repo=repo,
        demo=demo,
        note=_optional(raw, "note", where),
    )


def load_site(path: Path) -> Site:
    """Read and validate ``projects.yaml``."""
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
        projects.append(_project(p, i))
    _check_unique(projects, "slug")
    _check_unique(projects, "number")
    return Site(
        title=_require(site_raw, "title", "site"),
        tagline=_require(site_raw, "tagline", "site"),
        intro=_require(site_raw, "intro", "site"),
        description=_require(site_raw, "description", "site"),
        base_url=_require(site_raw, "base_url", "site").rstrip("/"),
        github=_require(site_raw, "github", "site"),
        projects=tuple(projects),
    )


def _check_unique(projects: list[Project], attr: str) -> None:
    seen: set[str] = set()
    for p in projects:
        value = str(getattr(p, attr))
        if value in seen:
            raise DataError(f"duplicate {attr} '{value}' in projects")
        seen.add(value)
