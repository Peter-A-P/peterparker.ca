"""The index cards are levelled by hand, and this is what keeps them levelled.

A card's tags are chips the browser wraps greedily at the card's width, so it is their
pixel widths, not their number, that decide how many rows a card grows. Editing one chip
can push a card from four rows to six, which is invisible in ``projects.yaml`` and plain
on the page: the card beside it is then left half empty. The same goes for a one-liner,
where a clause too many costs a line.

So the layout is measured here, from the real text and the site's own font files, and the
tests fail while a card would not come out the way the copy was written to come out. The
numbers below mirror ``style.css``; the first test is what stops the two drifting apart.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

from portfolio_site.models import Project, load_site

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "portfolio_site" / "static"

REM = 16.0

# Every declaration the arithmetic below leans on. If one of these changes, the numbers
# in this file are stale and the first test says so rather than letting it pass quietly.
STYLESHEET = (
    ".wrap { max-width: 66rem; margin: 0 auto; padding: 0 1.5rem; }",
    "grid-template-columns: repeat(auto-fill, minmax(27rem, 1fr)); gap: 1.1rem;",
    "padding: 1.3rem 1.4rem 1.2rem;",
    "display: flex; flex-direction: column; gap: .7rem;",
    ".tags { list-style: none; margin: .1rem 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: .4rem; }",  # noqa: E501
    "font-size: .76rem; color: var(--ink-2); background: var(--code);",
    "border: 1px solid var(--line); border-radius: 999px; padding: .12rem .6rem; line-height: 1.45;",  # noqa: E501
    ".one-liner { margin: 0; color: var(--ink-2); font-size: .97rem; }",
    "h3 { font-size: 1.42rem; line-height: 1.22; }",
    ".num { font-size: 1.35rem;",
    "font-size: .9rem; font-weight: 500; }",  # .links
    "line-height: 1.6;",  # body
)

WRAP, WRAP_PAD = 66 * REM, 1.5 * REM  # .wrap
COLUMN_MIN, GRID_GAP = 27 * REM, 1.1 * REM  # .grid
CARD_PAD_X, CARD_PAD_Y = 1.4 * REM, 1.3 * REM + 1.2 * REM  # .card
CARD_EDGES = 4.0  # the 1px border plus the 3px status rail down the left
CARD_GAP = 0.7 * REM  # between the card's rows

TAG_SIZE, TAG_PAD_X, TAG_GAP, TAG_EDGES = 0.76 * REM, 0.6 * REM, 0.4 * REM, 2.0
TAG_ROW = TAG_SIZE * 1.45 + 2 * (0.12 * REM) + TAG_EDGES
TITLE_SIZE, TITLE_LINE = 1.42 * REM, 1.42 * REM * 1.22
ONE_SIZE, ONE_LINE = 0.97 * REM, 0.97 * REM * 1.6
LINK_SIZE, LINK_LINE = 0.9 * REM, 0.9 * REM * 1.6
TOP_ROW = 1.35 * REM * 1.6  # the number and status line

MAX_TAG_ROWS = 4
"""Four rows is the shape every card's tags were written to. A fifth unbalances the grid."""

LEVEL_TOLERANCE = 40.0
"""How far apart the cards may finish, in pixels. Under two lines of card text."""


class Metrics:
    """Advance widths from one of the fonts the site actually serves."""

    def __init__(self, file: str) -> None:
        font = TTFont(STATIC / "fonts" / file)
        self.units: int = int(font["head"].unitsPerEm)
        self.glyphs: dict[int, str] = dict(font.getBestCmap())
        self.advance: dict[str, int] = {
            name: int(metric[0]) for name, metric in font["hmtx"].metrics.items()
        }
        font.close()

    def width(self, text: str, size: float) -> float:
        """What this text measures at this font size, in pixels."""
        fallback = self.advance[".notdef"]
        units = sum(self.advance.get(self.glyphs.get(ord(c), ""), fallback) for c in text)
        return units / self.units * size


INTER = Metrics("inter-latin.woff2")
NEWSREADER = Metrics("newsreader-latin.woff2")


def card_width() -> float:
    """The usable width inside one card, at the widest layout the grid produces."""
    content = WRAP - 2 * WRAP_PAD
    columns = int((content + GRID_GAP) // (COLUMN_MIN + GRID_GAP))
    column = (content - (columns - 1) * GRID_GAP) / columns
    return column - 2 * CARD_PAD_X - CARD_EDGES


CARD = card_width()


def lines_taken(text: str, size: float, metrics: Metrics, width: float = CARD) -> int:
    """How many lines this text wraps into, breaking on spaces as a browser does."""
    taken, line = 1, ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if not line or metrics.width(candidate, size) <= width:
            line = candidate
        else:
            taken, line = taken + 1, word
    return taken


def chip(tag: str) -> float:
    """The rendered width of one tag chip."""
    return INTER.width(tag, TAG_SIZE) + 2 * TAG_PAD_X + TAG_EDGES


def tag_rows(project: Project) -> list[list[str]]:
    """The chips grouped as flex-wrap groups them: in order, greedily, left to right."""
    rows: list[list[str]] = [[]]
    used = 0.0
    for tag in project.technical_line.split(" · "):
        needed = chip(tag) + (TAG_GAP if rows[-1] else 0)
        if rows[-1] and used + needed > CARD:
            rows.append([tag])
            used = chip(tag)
        else:
            rows[-1].append(tag)
            used += needed
    return rows


def spare(row: list[str]) -> float:
    """The empty width left at the end of a row of chips."""
    return CARD - sum(chip(t) for t in row) - TAG_GAP * (len(row) - 1)


def card_height(project: Project) -> float:
    """How tall this card comes out.

    A card ends in a links row only when the project has a live demo, the one link a card
    still carries, because a demo is something to use rather than read. Everything else is
    reached through the title: the page, and the repository the page links. A card
    carrying a note has that on its own line above it. So a card with a demo runs one line
    taller than its neighbours, about ``LINK_LINE`` px, and the tolerance below is what
    says that is still level enough.
    """
    has_links = project.demo is not None
    note_lines = lines_taken(project.note, LINK_SIZE, INTER) if project.note else 0
    rows = [
        TOP_ROW,
        lines_taken(project.name, TITLE_SIZE, NEWSREADER) * TITLE_LINE,
        lines_taken(project.one_liner, ONE_SIZE, INTER) * ONE_LINE,
        len(tag_rows(project)) * TAG_ROW + (len(tag_rows(project)) - 1) * TAG_GAP,
    ]
    if note_lines:
        rows.append(note_lines * LINK_LINE)
    if has_links:
        rows.append(LINK_LINE)
    return CARD_PAD_Y + sum(rows) + (len(rows) - 1) * CARD_GAP


def test_the_card_arithmetic_still_matches_the_stylesheet() -> None:
    style = (STATIC / "style.css").read_text(encoding="utf-8")
    missing = [rule for rule in STYLESHEET if rule not in style]
    assert not missing, (
        "style.css no longer contains "
        + "; ".join(missing)
        + ". The card measurements in this file mirror those declarations, so change both "
        "or these tests are measuring a page that no longer exists."
    )


def test_no_card_needs_more_than_four_rows_of_tags() -> None:
    """A chip that no longer fits beside its neighbour pushes the whole card taller."""
    site = load_site(ROOT / "projects.yaml")
    for project in site.projects:
        rows = tag_rows(project)
        if len(rows) > MAX_TAG_ROWS:
            widest = max(project.technical_line.split(" · "), key=chip)
            raise AssertionError(
                f"project {project.number}: its tags take {len(rows)} rows, not "
                f"{MAX_TAG_ROWS}. Rows run "
                + ", ".join(f"{round(CARD - spare(r))}px" for r in rows)
                + f" of {round(CARD)}px. The widest is {widest!r} at "
                f"{round(chip(widest))}px, leaving {round(CARD - TAG_GAP - chip(widest))}px "
                "for whatever shares its row. Shorten the long ones until every pair fits, "
                "then order them so each row fills."
            )


def test_the_cards_come_out_the_same_height() -> None:
    """Two columns, so a tall card leaves the one beside it empty at the bottom."""
    site = load_site(ROOT / "projects.yaml")
    heights = {p.number: card_height(p) for p in site.projects}
    spread = max(heights.values()) - min(heights.values())
    assert spread <= LEVEL_TOLERANCE, (
        f"the cards differ by {round(spread)}px, more than the {round(LEVEL_TOLERANCE)}px "
        "they are allowed: "
        + ", ".join(f"{number} {round(height)}px" for number, height in heights.items())
        + ". A one-liner is the usual lever: a line of it is about "
        f"{round(ONE_LINE)}px."
    )
