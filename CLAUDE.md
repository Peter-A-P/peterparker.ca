# Working notes for Claude Code

This repository builds https://peterparker.ca, the public portfolio site. Read
[README.md](README.md) first.

## What this site is

One page per project, rendered from the project's public repository README, plus an index
of one-liners from `projects.yaml`. Where a repository is not public yet, the project's
page may instead be a hand-written explainer that claims no result. Apart from those, the
site carries only what the public repositories carry. It is the recruiter-facing front door, so it stays fast, plain and honest: no
JavaScript, no analytics, no claims that a repository does not back with a number.

## Rules specific to this repository

- **`projects.yaml` is the only hand-written content.** Do not hand-edit anything in
  `dist/`; it is regenerated on every build.
- **A private repository is never read and never linked.** The build takes the GitHub
  API's word for whether a repository is public and reads nothing it does not mark
  public. Do not add a token with private-repository access to the workflow. A project
  whose repository is private can still have a page, but only from its explainer, and
  that page neither links the repository nor quotes it.
- **An explainer is a stand-in, never a claim.** A project may name an `explainer:` in
  `content/`: plain-language Markdown that is its page until its repository is public,
  and that the README replaces the day it is. It states no measured result, and the page
  says the project has none yet. Keep it in step with that project's own README "How it
  works": if one changes, change the other in the same change. A `<!-- more -->` line
  splits the first screen from the part behind "Learn more".
- **One-liners are the portfolio's own** and match the opening paragraph of the project's
  README. If a README's opening changes, change the one-liner here in the same change.
- **Status is set by hand** in `projects.yaml` (`live`, `shipped`, `building`, `planned`).
  The build warns when a public repository is still marked `planned` or `building`.
- **Every status change is logged** in `log:` at the end of `projects.yaml`, in the same
  edit as the status: date, project number, the new status, one public sentence ending in
  a full stop. The build refuses a log whose latest entry for a project disagrees with the
  project's status. Entries are never edited or removed; a wrong entry gets a later entry
  that corrects it. The log renders at `/log/`, as the "Latest" strip on the index, and as
  history on the project's page.
- **A card's title is its page link.** The row at the foot of a card carries only links
  that leave the site, the repository and a live demo, and never repeats the title's own
  link. The line above the grid is what tells the reader the title is clickable; if the
  cards' linking changes, change that line in the same edit.
- **Card copy is laid out, not just written.** A card's tags are chips the browser wraps
  by pixel width, so every card's tags are written to fill four rows and its one-liner is
  sized so the cards finish the same height. `tests/test_card_layout.py` measures both
  with the site's own font files and fails when an edit breaks the shape; it names the
  chip to shorten. Change a tag or a one-liner and run `pytest` before pushing.
- **Plain punctuation**: no em-dashes or other typographic dashes, straight quotes only.
- Engineering standard: Python 3.13, typed throughout, `mypy --strict` and `ruff` clean,
  tests that fail meaningfully, docs in the same commit as the change. Major versions are
  pinned in `pyproject.toml` with a comment saying why.

## Deploying

Pushing to `main` deploys. The workflow also runs daily so a repository that turns public
appears within a day. If the Azure token rotates, update the
`AZURE_STATIC_WEB_APPS_API_TOKEN` repository secret; nothing in the code changes.
