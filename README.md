# peterparker.ca

The public home of a portfolio of production-grade machine learning and AI projects.
One page per project, generated from that project's public repository README, so a page
can only say what the repository says, and a project appears the day its repository turns
public.

Live at https://peterparker.ca.

## How it works

- `projects.yaml` lists the projects: name, one-liner, technical line, status, repository.
  It is the only hand-written content.
- `python -m portfolio_site build` reads each listed repository from the GitHub API. If the
  API marks it public, the README is rendered into `dist/projects/<slug>/`; otherwise the
  project gets a card on the index and no page. Relative links in a README are rewritten
  to open on GitHub. Raw HTML in a README is escaped; the site ships no JavaScript.
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
