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
  core/      Shared Python: repositories (DynamoDB), sync and matching logic -> hookd_core
  ui/        Shared design tokens
infra/       Terraform (infra/terraform) + local dev config
scripts/     Seed data, type generation, deploy.sh
Docs/        Project plan and A3 guidance
```

`packages/core` is shared by the API and the worker so both use the same stores
(the worker upserts posts, the API reads them).

## Local development

```bash
cp .env.example .env                        # then set COGNITO_* (see infra/README.md)
cp apps/web/.env.example apps/web/.env      # then set VITE_COGNITO_*
docker compose up -d dynamodb redis sqs     # backing services
uv sync --all-packages                      # Python deps (uv workspace)
uv run uvicorn hookd_api.main:app --reload  # http://localhost:8000/api/health (creates the table)

npm install                                 # JS deps (npm workspace)
npm run dev -w apps/web                     # http://localhost:5173
```

Or run everything in containers: `docker compose up --build`.

## Deploying to AWS

Terraform in `infra/terraform/envs/cab432`, then `scripts/deploy.sh` to build and
push the images. See [infra/README.md](infra/README.md).

## Common commands

| Task | Command |
|---|---|
| Lint / format | `uv run ruff check .` / `uv run ruff format .` |
| Python tests | `uv run pytest` |
| API tests on DynamoDB (moto) | `HOOKD_TEST_STORAGE=dynamodb uv run pytest apps/api` |
| Regenerate API types | `npm run gen:api -w apps/web` (after changing API schemas or routes) |

## Storage

A3 stores everything in one **DynamoDB** table (RDS is blocked on the CAB432
account); the plan is to move back to RDS PostgreSQL after the assignment.
Services only use the protocols in `hookd_core.repositories`, so that move
means adding SQL implementations and switching `STORAGE`. The SQLAlchemy models
and Alembic setup in `packages/core` are kept for it. The table layout is
documented in `hookd_core/repositories/dynamodb.py`.

| Setting | |
|---|---|
| `STORAGE=dynamodb` (default) | `DYNAMODB_TABLE`; `DYNAMODB_ENDPOINT_URL` for DynamoDB Local; `DYNAMODB_CREATE_TABLE=true` creates it locally (Terraform creates it in AWS) |
| `STORAGE=memory` | Per-process stores, lost on restart. The worker can't see the API's data, so use `SYNC_MODE=inline` |

## Post sync

Each creator's recent posts are fetched, matched to their campaigns by tracking
hashtag (within the campaign dates), and upserted with their latest metrics.
The logic is `hookd_core.sync`, shared by the API and the worker.

| Setting | |
|---|---|
| `SYNC_MODE=inline` (default) | "Sync now" runs inside the API request; no worker needed |
| `SYNC_MODE=queue` | The API queues one job per creator on `SYNC_QUEUE_URL`; the worker syncs them. EventBridge sends `{"type":"scheduled_sync"}` to sync everyone on an active campaign. Used in AWS and in `docker compose` |
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
