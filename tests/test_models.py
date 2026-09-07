"""projects.yaml is validated, and the real file passes."""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_site.models import DataError, Group, Status, load_site

ROOT = Path(__file__).resolve().parents[1]
# Em dash, en dash, curly single and double quotes, ellipsis, as code points so the
# source file itself carries none of them.
TYPOGRAPHIC = tuple(chr(c) for c in (0x2014, 0x2013, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026))


def test_real_projects_yaml_loads() -> None:
    site = load_site(ROOT / "projects.yaml")
    assert site.base_url == "https://peterparker.ca"
    numbers = [p.number for p in site.in_group(Group.PORTFOLIO)]
    assert numbers == sorted(numbers), "portfolio projects are listed in numeric order"
    assert len(numbers) == 10
    for project in site.projects:
        assert project.one_liner.rstrip().endswith("."), project.slug
        for ch in TYPOGRAPHIC:
            assert ch not in project.one_liner, f"{project.slug}: typographic punctuation"
            assert ch not in project.technical_line, f"{project.slug}: typographic punctuation"


def _write(tmp_path: Path, projects: str) -> Path:
    path = tmp_path / "projects.yaml"
    path.write_text(
        "site:\n"
        "  title: T\n  tagline: t\n  intro: i\n  description: d\n"
        "  base_url: https://example.org/\n  github: https://github.com/x\n"
        f"projects:\n{projects}",
        encoding="utf-8",
    )
    return path


GOOD = (
    "  - number: '01'\n    slug: one\n    name: One\n    one_liner: A.\n"
    "    technical_line: t\n    status: planned\n    group: portfolio\n"
)


def test_minimal_file_loads_and_strips_trailing_slash(tmp_path: Path) -> None:
    site = load_site(_write(tmp_path, GOOD))
    assert site.base_url == "https://example.org"
    assert site.projects[0].status is Status.PLANNED
    assert site.projects[0].repo_url is None


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (GOOD.replace("planned", "done"), "status 'done'"),
        (GOOD.replace("portfolio", "extras"), "group 'extras'"),
        (GOOD.replace("slug: one", "slug: One"), "slug 'One'"),
        (GOOD + "    repo: not-a-repo\n", "repo 'not-a-repo'"),
        (GOOD + "    demo: http://insecure.example\n", "must be an https URL"),
        (GOOD + GOOD.replace("'01'", "'02'"), "duplicate slug"),
        (GOOD + GOOD.replace("slug: one", "slug: two"), "duplicate number"),
    ],
)
def test_bad_files_fail_with_a_reason(tmp_path: Path, bad: str, message: str) -> None:
    with pytest.raises(DataError, match=message):
        load_site(_write(tmp_path, bad))
