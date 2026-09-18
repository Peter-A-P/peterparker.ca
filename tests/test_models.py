"""projects.yaml is validated, and the real file passes."""

from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_site.models import DataError, Status, load_site

ROOT = Path(__file__).resolve().parents[1]
# Em dash, en dash, curly single and double quotes, ellipsis, as code points so the
# source file itself carries none of them.
TYPOGRAPHIC = tuple(chr(c) for c in (0x2014, 0x2013, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026))


def test_real_projects_yaml_loads() -> None:
    site = load_site(ROOT / "projects.yaml")
    assert site.base_url == "https://peterparker.ca"
    numbers = [p.number for p in site.projects]
    assert numbers == sorted(numbers), "projects are listed in numeric order"
    assert site.themes, "the index filters need at least one theme"
    for project in site.projects:
        assert project.themes, f"{project.slug}: every project carries at least one theme"
    assert site.theme_slot(next(iter(site.themes))) == 1
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
    "    technical_line: t\n    status: planned\n"
)
LOG = "log:\n  - date: 2026-09-07\n    project: '01'\n    status: planned\n    note: Planned.\n"


def test_minimal_file_loads_and_strips_trailing_slash(tmp_path: Path) -> None:
    site = load_site(_write(tmp_path, GOOD))
    assert site.base_url == "https://example.org"
    assert site.projects[0].status is Status.PLANNED
    assert site.projects[0].repo_url is None


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (GOOD.replace("planned", "done"), "status 'done'"),
        (GOOD.replace("slug: one", "slug: One"), "slug 'One'"),
        (GOOD + "    repo: not-a-repo\n", "repo 'not-a-repo'"),
        (GOOD + "    demo: http://insecure.example\n", "must be an https URL"),
        (GOOD + "    demo_note: A sentence.\n", "without a 'demo'"),
        (GOOD + GOOD.replace("'01'", "'02'"), "duplicate slug"),
        (GOOD + GOOD.replace("slug: one", "slug: two"), "duplicate number"),
        (GOOD + "    themes: [nope]\n", "unknown theme 'nope'"),
        (GOOD + "    themes: nope\n", "must be a list"),
        (GOOD + LOG.replace("'01'", "'09'"), "project '09' is not in 'projects'"),
        (GOOD + LOG.replace("2026-09-07", "yesterday"), "must be YYYY-MM-DD"),
        (GOOD + LOG.replace("status: planned", "status: done"), "status 'done'"),
        (GOOD + LOG.replace("Planned.", "Planned"), "ending in a full stop"),
        (GOOD + LOG.replace("status: planned", "status: building"), "change both in the same edit"),
        (GOOD + "log: nope\n", "'log' must be a list"),
    ],
)
def test_bad_files_fail_with_a_reason(tmp_path: Path, bad: str, message: str) -> None:
    with pytest.raises(DataError, match=message):
        load_site(_write(tmp_path, bad))


def test_a_demo_note_is_optional_and_rides_with_its_demo(tmp_path: Path) -> None:
    # A note beside a button nobody can press is a note about nothing, which is why the
    # loader refuses it. With the demo present it is carried through unchanged.
    with_demo = GOOD + "    demo: https://demo.example\n    demo_note: What it shows.\n"
    project = load_site(_write(tmp_path, with_demo)).projects[0]
    assert project.demo == "https://demo.example"
    assert project.demo_note == "What it shows."

    without = load_site(_write(tmp_path, GOOD + "    demo: https://demo.example\n")).projects[0]
    assert without.demo_note is None


def test_log_is_sorted_newest_first_and_checked_against_the_card(tmp_path: Path) -> None:
    good = GOOD.replace("status: planned", "status: building")
    log = (
        "log:\n"
        "  - date: 2026-09-01\n    project: '01'\n    status: planned\n    note: Planned.\n"
        "  - date: 2026-09-10\n    project: '01'\n    status: building\n    note: Started.\n"
    )
    site = load_site(_write(tmp_path, good + log))
    assert [e.status for e in site.log] == [Status.BUILDING, Status.PLANNED]
    assert site.log[0].date.isoformat() == "2026-09-10" and site.log[0].note == "Started."
    assert site.log_for("01") == site.log and site.project("01").slug == "one"
    assert load_site(_write(tmp_path, GOOD)).log == ()


def test_real_log_agrees_with_the_cards() -> None:
    site = load_site(ROOT / "projects.yaml")
    assert site.log, "the log has at least the entries that opened it"
    for e in site.log:
        assert e.note.endswith(".")
        for ch in TYPOGRAPHIC:
            assert ch not in e.note, "typographic punctuation in a log note"


EXPLAINER = "The first screen.\n\n<!-- more -->\n\n## Deeper\n\nThe rest.\n"


def _with_explainer(tmp_path: Path, content: str | None, name: str = "content/x.md") -> Path:
    """A projects.yaml naming an explainer, with the file beside it unless content is None."""
    if content is not None:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return _write(tmp_path, GOOD + f"    explainer: {name}\n")


def test_explainer_is_read_from_beside_projects_yaml(tmp_path: Path) -> None:
    site = load_site(_with_explainer(tmp_path, EXPLAINER))
    text = site.projects[0].explainer
    assert text is not None
    assert text.startswith("The first screen.") and text.endswith("The rest.")


def test_a_project_without_an_explainer_has_none(tmp_path: Path) -> None:
    assert load_site(_write(tmp_path, GOOD)).projects[0].explainer is None


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (None, "is not a file"),
        ("   \n", "is empty"),
        ("# A title\n\nBody.\n", "must not open with an H1"),
        (EXPLAINER + "\n<!-- more -->\n\nAgain.\n", "one at most"),
    ],
)
def test_bad_explainers_fail_with_a_reason(
    tmp_path: Path, content: str | None, message: str
) -> None:
    with pytest.raises(DataError, match=message):
        load_site(_with_explainer(tmp_path, content))


def test_an_explainer_cannot_reach_outside_the_repository(tmp_path: Path) -> None:
    (tmp_path.parent / "outside.md").write_text("Elsewhere.\n", encoding="utf-8")
    with pytest.raises(DataError, match="must sit inside the site repository"):
        load_site(_write(tmp_path, GOOD + "    explainer: ../outside.md\n"))


def test_real_explainers_are_plain_and_carry_no_title() -> None:
    site = load_site(ROOT / "projects.yaml")
    explained = [p for p in site.projects if p.explainer is not None]
    assert explained, "at least one project explains itself while its repository is private"
    for project in explained:
        text = project.explainer
        assert text is not None
        for ch in TYPOGRAPHIC:
            assert ch not in text, f"{project.slug}: typographic punctuation in the explainer"
        assert not text.startswith("# "), project.slug


def test_two_entries_on_one_day_order_by_the_file(tmp_path: Path) -> None:
    """A project can change status twice in a day. The file's order decides which is later."""
    good = GOOD.replace("status: planned", "status: shipped")
    log = (
        "log:\n"
        "  - date: 2026-09-11\n    project: '01'\n    status: building\n    note: Started.\n"
        "  - date: 2026-09-11\n    project: '01'\n    status: shipped\n    note: Public.\n"
    )
    site = load_site(_write(tmp_path, good + log))
    assert [e.note for e in site.log] == ["Public.", "Started."], "later write reads as newer"
