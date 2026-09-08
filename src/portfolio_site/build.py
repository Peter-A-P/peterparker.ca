"""Build the site into a directory. ``python -m portfolio_site build --out dist``."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from portfolio_site.github import GitHub, PublicRepo
from portfolio_site.models import STATUS_LABEL, Project, Site, Status, load_site
from portfolio_site.render import render_readme, split_title

ROOT_FILES = ("staticwebapp.config.json",)
WORDS = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
)


def number_word(n: int) -> str:
    """Spell out small counts for headings; larger ones stay digits."""
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


@dataclass(slots=True)
class PageInfo:
    """What the index needs to know about a generated project page."""

    project: Project
    repo: PublicRepo
    path: str  # site-relative, with leading and trailing slash


@dataclass(slots=True)
class BuildReport:
    """What happened, for the console and for tests."""

    pages: list[PageInfo] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # projects with a repo that is not public
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """One line per fact, for the build log."""
        lines = [f"{len(self.pages)} project page(s) built"]
        lines += [f"  page     {p.path}  <- {p.repo.full_name}" for p in self.pages]
        lines += [f"  no page  {s} (repository not public)" for s in self.skipped]
        lines += [f"  WARNING  {w}" for w in self.warnings]
        return "\n".join(lines)


def _package_dir(name: str) -> Path:
    with resources.as_file(resources.files("portfolio_site") / name) as path:
        return Path(path)


def _environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_package_dir("templates"))),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["status_label"] = lambda s: STATUS_LABEL[Status(s)]
    env.globals["number_word"] = number_word
    return env


def _write(out: Path, rel: str, content: str) -> None:
    target = out / rel.lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def build(
    site: Site,
    out: Path,
    github: GitHub | None,
    *,
    repo_root: Path | None = None,
    today: str | None = None,
) -> BuildReport:
    """Render everything into ``out``. ``github=None`` builds the index only (offline)."""
    report = BuildReport()
    env = _environment()
    generated = today or datetime.now(UTC).date().isoformat()
    common = {"site": site, "generated": generated, "Status": Status}

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    pages_by_slug: dict[str, PageInfo] = {}
    for project in site.projects:
        if project.repo is None:
            continue
        repo = github.public_repo(project.repo) if github else None
        if repo is None:
            report.skipped.append(project.repo)
            continue
        if project.status in (Status.PLANNED, Status.BUILDING):
            report.warnings.append(
                f"{project.repo} is public but projects.yaml still says '{project.status}'"
            )
        _title, body_md = split_title(repo.readme_markdown)
        body_html = render_readme(body_md, repo.html_url, repo.default_branch)
        path = f"/projects/{project.slug}/"
        html = env.get_template("project.html").render(
            **common, project=project, repo=repo, body=body_html, path=path
        )
        _write(out, f"{path}index.html", html)
        info = PageInfo(project=project, repo=repo, path=path)
        pages_by_slug[project.slug] = info
        report.pages.append(info)

    _write(out, "/index.html", env.get_template("index.html").render(**common, pages=pages_by_slug))
    _write(out, "/404.html", env.get_template("404.html").render(**common))
    _write(out, "/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site.base_url}/sitemap.xml\n")
    urls = [f"{site.base_url}/"] + [f"{site.base_url}{p.path}" for p in report.pages]
    _write(
        out,
        "/sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n",
    )
    shutil.copytree(_package_dir("static"), out, dirs_exist_ok=True)
    if repo_root is not None:
        for name in ROOT_FILES:
            source = repo_root / name
            if source.exists():
                shutil.copyfile(source, out / name)
    return report


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="portfolio-site")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="build the site")
    b.add_argument("--data", type=Path, default=Path("projects.yaml"))
    b.add_argument("--out", type=Path, default=Path("dist"))
    b.add_argument(
        "--offline",
        action="store_true",
        help="do not call GitHub; build the index only",
    )
    args = parser.parse_args(argv)

    site = load_site(args.data)
    github = None if args.offline else GitHub(token=os.environ.get("GITHUB_TOKEN") or None)
    report = build(site, args.out, github, repo_root=args.data.resolve().parent)
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
