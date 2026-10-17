# Hookd Tracker

Every creator, every target, every TikTok post, tracked in one dashboard.
See [Docs/hookd-tracker-project-plan.md](Docs/hookd-tracker-project-plan.md) for the full plan and [Docs/CAB432_A3_Project_Guidance.pdf](Docs/CAB432_A3_Project_Guidance.pdf) for the assignment brief.

## Layout

```
apps/
  www/       Public home page (HTML/CSS/JS + GSAP)
  web/       React + Vite app (dashboards, campaigns, creators)
  api/       FastAPI service           -> hookd_api
  worker/    SQS sync workers          -> hookd_worker
  mcp/       MCP server (extension)    -> hookd_mcp
packages/
  core/      Shared Python: SQLAlchemy models, Alembic migrations, matching logic -> hookd_core
  ui/        Shared design tokens
infra/       Infrastructure as code + local dev config
scripts/     Seed data, type generation
Docs/        Project plan and A3 guidance
```

`packages/core` is shared by the API and the worker so both write to the same
models (the worker upserts posts, the API reads them).

## Local development

```bash
cp .env.example .env
docker compose up -d postgres redis sqs     # backing services
uv sync --all-packages                      # Python deps (uv workspace)
uv run alembic -c packages/core/alembic.ini upgrade head
uv run uvicorn hookd_api.main:app --reload  # http://localhost:8000/api/health

npm install                                 # JS deps (npm workspace)
npm run dev -w apps/web                     # http://localhost:5173
```

Or run everything in containers: `docker compose up --build`.

## Common commands

| Task | Command |
|---|---|
| Lint / format | `uv run ruff check .` / `uv run ruff format .` |
| Python tests | `uv run pytest` |
| New migration | `uv run alembic -c packages/core/alembic.ini revision --autogenerate -m "msg"` |
| Regenerate API types | `npm run gen:api -w apps/web` (API must be running) |

## Testing with a real TikTok account

There is no seeded demo data. For user testing, link a real TikTok account and
let the sync worker pull its actual posts and metrics:

1. In `.env`, set `TIKTOK_MODE=live` and fill in `TIKTOK_CLIENT_KEY` and
   `TIKTOK_CLIENT_SECRET` from the TikTok developer app.
2. Create a campaign, add a creator using the test account's TikTok handle, and
   assign them with a posting target.
3. Post to the test account using the campaign hashtag, then run a sync and
   check the posts appear against the creator's target.

`TIKTOK_MODE=mock` (the default) is still available for running locally
without TikTok credentials.

## Branching

| Branch | Purpose |
|---|---|
| `main` | Production-ready. Only updated by PR from `dev` once CI passes. |
| `dev` | Integration branch. Feature branches merge here by PR. |
| `feature/<name>` | One epic or story, branched from `dev`. Put Jira keys (e.g. `HOOKD-7`) in commit messages. |

Flow: `feature/*` → PR → `dev` → PR (release) → `main`.
