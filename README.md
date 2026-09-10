# peterparker.ca

The public home of a portfolio of production-grade machine learning and AI projects.
One page per project, generated from that project's public repository README, so a page
can only say what the repository says, and a project appears the day its repository turns
public.

Live at https://peterparker.ca.

## How it works

- `projects.yaml` lists the projects: name, one-liner, technical line, status, repository.
  Together with the explainers in `content/`, it is the only hand-written content.
  Its `log:` section records every change of a
  project's status with a date and one sentence; the site renders it at `/log/`, as a
  "Latest" strip on the index, and as history on each project page.
- `python -m portfolio_site build` reads each listed repository from the GitHub API. If the
  API marks it public, the README is rendered into `dist/projects/<slug>/`; otherwise the
  project gets a card on the index, and a page only if it names an explainer. Relative
  links in a README are rewritten to open on GitHub. Raw HTML in a README is escaped;
  the site ships no JavaScript.
- A project may name an `explainer:`, a Markdown file in `content/`. It is that project's
  page until its repository is public, and the README replaces it the day it is, so the
  two are never shown together. An explainer claims no measured result and its page says
  the project has none yet. A `<!-- more -->` line splits the first screen from the rest,
  which the page puts behind a "Learn more" disclosure: a native `<details>` element,
  because the site ships no JavaScript.
- Typefaces are Inter and Newsreader, self-hosted from `src/portfolio_site/static/fonts/`
  under the SIL Open Font License, so the page makes no third-party requests and the
  content security policy stays `'self'` only.
- GitHub Actions rebuilds on every push, once a day, and on demand, and deploys `dist/` to
  Azure Static Web Apps. The daily run is what publishes a newly public repository within
  a day without anyone touching this repository.

## Working on it

```bash
python -m venv .venv && . .venv/Scripts/activate   # or .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest -q
python -m portfolio_site build --out dist            # GITHUB_TOKEN optional; raises the rate limit
python -m portfolio_site build --out dist --offline  # index only, no network
python -m http.server -d dist 8080
```

Typed, `ruff` and `mypy --strict` clean, tests that fail meaningfully. Plain punctuation
in everything written here.

## Deployment

Azure Static Web Apps, free tier, in a personal Azure subscription. The deployment token
lives in the repository secret `AZURE_STATIC_WEB_APPS_API_TOKEN`; nothing else is
configured on the Azure side except the custom domains `peterparker.ca` and
`www.peterparker.ca`, which point here from Cloudflare DNS. `staticwebapp.config.json`
sets the 404 page and the response headers.
