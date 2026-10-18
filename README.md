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
cp .env.example .env                        # then set COGNITO_* (see infra/README.md)
cp apps/web/.env.example apps/web/.env      # then set VITE_COGNITO_*
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
| Regenerate API types | `npm run gen:api -w apps/web` (after changing API schemas or routes) |

## Post sync

Each creator's recent posts are fetched, matched to their campaigns by tracking
hashtag (within the campaign dates), and upserted with their latest metrics.
The logic is `hookd_core.sync`, shared by the API and the worker.

| Setting | |
|---|---|
| `SYNC_MODE=inline` (default) | "Sync now" runs inside the API request. Needed while the stores are in-memory, because the worker can't see the API's data |
| `SYNC_MODE=queue` | The API queues one job per creator on `SYNC_QUEUE_URL`; the worker syncs them. EventBridge sends `{"type":"scheduled_sync"}` to sync everyone on an active campaign |
| `TIKTOK_MODE=mock` (default) | Deterministic fake posts that use the campaign hashtags; metrics grow between syncs |
| `TIKTOK_MODE=live` | TikTok Research API (`TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`) |
| `CAMPAIGN_TIMEZONE` | Campaign dates and weekly/monthly targets are days in this timezone (default `Australia/Brisbane`) |

Posts the manager adds, moves or removes are marked `manual`: sync keeps their
campaign and only refreshes metrics. Removed posts are kept flagged, so sync
doesn't add them back.

## Testing with a real TikTok account

There is no seeded demo data. For user testing, link a real TikTok account and
let sync pull its actual posts and metrics:

1. In `.env`, set `TIKTOK_MODE=live` and fill in `TIKTOK_CLIENT_KEY` and
   `TIKTOK_CLIENT_SECRET` from a TikTok developer app with Research API access
   (it reads other accounts' public videos).
2. Create a campaign, add a creator using the test account's TikTok handle, and
   assign them with a posting target.
3. Post to the test account using the campaign hashtag, then press **Sync now**
   on the campaign page and check the post appears.

## Troubleshooting

**`ModuleNotFoundError: No module named 'hookd_...'` (macOS):** if the repo is in an
iCloud-synced folder (Desktop/Documents), iCloud marks files in `.venv` as hidden and
Python 3.12.13+ skips hidden `.pth` files, breaking the workspace installs. Keep the
venv out of iCloud by giving it a `.nosync` name:

```bash
rm -rf .venv && mkdir .venv.nosync && ln -s .venv.nosync .venv && uv sync
```

## Branching

| Branch | Purpose |
|---|---|
| `main` | Production-ready. Only updated by PR from `dev` once CI passes. |
| `dev` | Integration branch. Feature branches merge here by PR. |
| `feature/<name>` | One epic or story, branched from `dev`. Put Jira keys (e.g. `HOOKD-7`) in commit messages. |

Flow: `feature/*` → PR → `dev` → PR (release) → `main`.
