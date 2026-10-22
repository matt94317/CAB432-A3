# Hookd Tracker — Project Plan

> **Hookd Tracker: every creator, every target, every TikTok post, tracked in one dashboard.**

---

## Product Vision

**A3 scope:** *Hookd Tracker*, the campaign management layer (sections 1–12).
**Long-term goal:** *Hookd*, an AI-powered UGC creator platform. Hosts find and sign creators, run campaigns, and manage their signed creators **through their own AI agent** using Hookd's MCP server.

### Key concepts
| Term | Meaning |
|---|---|
| **Host** | Any organisation or person that needs online marketing: a brand, agency, small business or solo marketer. In A3 the Host is the `Organisation` and its campaign manager. |
| **Creator** | A UGC content creator who joins campaigns and posts content against agreed targets. |
| **Host's AI agent** | An LLM agent the Host already uses (Claude, ChatGPT or a custom agent). It connects to Hookd through the MCP server and acts for the Host. |

### Why agent-native
Running UGC at scale usually means hiring a dedicated UGC manager to chase creators, check posts and write reports. Hookd offers campaign management as MCP tools, so a Host can manage signed creators from the AI agent they already use. There's no extra hire and no new tool to learn. The web app is for setup and oversight, and the agent handles day-to-day management. Hosts bring their own agent, so they pay for their own LLM usage and Hookd's running costs stay low.

### Campaign lifecycle
| Stage | What happens | Delivered in |
|---|---|---|
| 1. Discover & match | Host publishes a campaign; AI recommends creators; creators apply | Phase 4 |
| 2. Sign | Host accepts applications and agrees targets and fees | Phase 4 |
| 3. Run & manage | Posts tracked against targets; the Host's agent chases creators and reports progress | **Phase 1 (A3)**, expanded in Phase 2 |
| 4. Report & pay | Campaign reports to clients; creators paid when deliverables are met | Phases 2 and 4 |

### Roadmap phases
| Phase | Name | Adds |
|---|---|---|
| **1** | **Hookd Tracker (A3, current)** | Campaign and creator management, TikTok sync, dashboards, first MCP tools |
| 2 | Agent-native management | Full MCP toolset so the Host's agent can run campaigns end to end: creator messaging, AI summaries, alerts, reports. Plus agent permissions, confirmations, an audit log, teams and roles |
| 3 | Creator platform | Creator accounts and portal, profiles with connected social accounts and verified stats, Instagram and YouTube |
| 4 | Marketplace | Public campaign listings, creator applications, AI Host–creator matching, agreements and payments |

**Why A3 builds stage 3 first:** management is useful on its own, with creators a Host already works with, and it doesn't need a two-sided marketplace to exist. The A3 MCP server is the first piece of the agent-native model, so its tools are designed as the start of the long-term agent contract. Section 13 lists the A3 design choices that keep this path open.

---

## 1. Problem

UGC campaign managers run campaigns with many creators at once. To check whether each creator is posting enough and performing well, they open each creator's TikTok account one by one, count posts against what was agreed, and copy metrics into spreadsheets. This is slow, error-prone, and gets worse with every creator and campaign added.

**Hookd Tracker** puts campaigns, creators, targets and post performance in one platform, so a manager can see at a glance who is on target, who is behind, and how each campaign is performing.

---

## 2. Users

| User | Description | Needs |
|---|---|---|
| **UGC campaign manager** (primary, B2B) | Runs TikTok UGC campaigns for brands, managing a roster of creators | One place to manage campaigns and creators, track posts vs targets, and see performance without checking accounts manually |

**Platform:** TikTok only (first version).

### Future users (long-term platform)
| User | Phase | Needs |
|---|---|---|
| **Host** (any size, incl. non-specialists) | 2+ | Manage signed creators without a dedicated UGC manager, mostly through their own AI agent |
| **Host's AI agent** (API client, not a person) | 1 (read + target updates), 2 (full) | Safe, scoped, well-described tools that act on the Host's data |
| **Creator** | 3+ | A profile, connected social accounts, campaign applications, targets, messages and payments in one place |

---

## 3. Scope

### In scope (A3)
- Single user type: UGC campaign manager
- Campaign management (CRUD)
- Creator roster (CRUD), assignment to campaigns, per-period post targets
- Automatic TikTok post and metrics sync, plus manual post entry
- Campaign dashboard, creator view, behind-target flags
- Public home page
- **Extension beyond the A3 spec:** MCP server exposing campaign and creator tools to AI assistants

### Future scope (commercial roadmap)
**Phase 2: Agent-native management**
- Full MCP toolset: create and edit campaigns, assign creators, message creators, generate reports
- Agent safety: scoped agent permissions, confirmation for sensitive actions, audit log of agent actions
- AI post-to-campaign matching, AI campaign summaries, drafted creator follow-ups
- Dashboard filters, report exports (CSV/PDF), automated alerts
- Team invites, roles and multi-user organisations
- Creator fees and payment tracking
- Agent-to-agent workflows (ACP)

**Phase 3: Creator platform**
- Creator accounts and portal
- Creator profiles with niches, rates, connected social accounts and verified audience stats
- Instagram, YouTube and other platforms

**Phase 4: Marketplace**
- Public campaign listings with briefs, deliverables, budget and creator requirements
- Creator applications to campaigns
- AI Host–creator matching and ranked recommendations
- Agreements and creator payments

**Marketing**
- Full marketing site with features, pricing and blog (SEO)

### Out of scope (A3)
- Content approval workflows
- Creative briefs (they return in Phase 4 as campaign listings)
- Any marketplace, creator-facing or payment features

### Scope statement
Hookd Tracker is a web platform for UGC campaign managers to manage TikTok campaigns and creators in one place. Managers create campaigns, assign creators with posting targets, and track each creator's posts and performance automatically, replacing manual checks across individual TikTok accounts. The first version supports a single user type and TikTok only, and includes an MCP server so managers can query their campaign data from an AI assistant. It is the first phase of Hookd, an AI-powered UGC creator platform where Hosts match with creators and manage them through their own AI agents.

---

## 4. Data Model

| Entity | Key fields |
|---|---|
| **User** (campaign manager) | id, name, email, organisation_id, cognito_sub |
| **Campaign** | id, organisation_id, name, brand, start_date, end_date, status, tracking_hashtags |
| **Creator** | id, organisation_id, name, platform, handle, niche, contact |
| **CampaignCreator** (assignment) | id, campaign_id, creator_id, target_posts, target_period (week/month), status |
| **Post** | id, creator_id, campaign_id, platform, url, caption, hashtags, posted_at, views, likes, comments, shares, match_source, last_synced_at |

**Design notes**
- Targets live on **CampaignCreator**, not Creator — the same creator can have different targets in different campaigns.
- `organisation_id` is included now (one user per org) so teams can be added later without migrating data.
- `platform` on Creator and Post (default `tiktok`) leaves room for Instagram and YouTube.
- `match_source` on Post (`hashtag` / `manual`, later `ai`) tracks how a post was linked to a campaign.
- Raw `caption` and `hashtags` are stored so future AI features have content to work with.
- **Creator** is an org-owned roster entry in A3. In Phase 3 creators get their own accounts. A nullable link from the roster entry to a platform-wide creator profile will join the two, so existing roster data is kept.
- **CampaignCreator** represents a "signed" creator. In Phase 4 it is created when a Host accepts an application, so tracking works the same whether a creator was added by hand or came through the marketplace.

### Future entities (not built in A3)
| Entity | Phase | Purpose |
|---|---|---|
| **AgentClient** | 2 | A connected AI agent: organisation, granted scopes, last used |
| **AgentAction** (audit log) | 2 | Every agent tool call: tool, arguments, result, confirmed by, timestamp |
| **PendingAction** | 2 | A sensitive agent action waiting for the Host's confirmation |
| **Message** | 2 | Host or agent ↔ creator messages |
| **CreatorAccount / CreatorProfile** | 3 | Creator login, niches, rates, connected social accounts, verified stats |
| **CampaignListing** | 4 | Public brief, deliverables, budget and creator requirements for a campaign |
| **Application** | 4 | A creator's application to a listing, with status and AI match score |
| **Agreement / Payment** | 4 | Agreed fee and deliverables; payout status

---

## 5. User Stories

**Priority:** MVP = A3 core · Extension = in scope, beyond the A3 spec · Future = commercial roadmap

### Epic 1: Account
| ID | User story | Priority |
|---|---|---|
| US-01 | As a manager, I can sign up and log in so my campaign data is private to me. | MVP |
| US-02 | As a manager, I can log out and stay signed in securely between sessions. | MVP |

### Epic 2: Campaign management
| ID | User story | Priority |
|---|---|---|
| US-03 | As a manager, I can create a campaign with a name, brand, start and end date, and tracking hashtags. | MVP |
| US-04 | As a manager, I can edit a campaign's details when the brief changes. | MVP |
| US-05 | As a manager, I can archive or delete a campaign that has ended or was cancelled. | MVP |
| US-06 | As a manager, I can see a list of all my campaigns with status and overall progress at a glance. | MVP |

### Epic 3: Creator management
| ID | User story | Priority |
|---|---|---|
| US-07 | As a manager, I can add a creator with their name, TikTok handle, niche and contact details. | MVP |
| US-08 | As a manager, I can edit or remove a creator from my roster. | MVP |
| US-09 | As a manager, I can assign creators to a campaign. | MVP |
| US-10 | As a manager, I can set each creator's target number of posts per period (week or month) for a campaign. | MVP |
| US-11 | As a manager, I can change a creator's target in a campaign when the deal changes. | MVP |
| US-12 | As a manager, I can remove a creator from a campaign without deleting them from my roster. | MVP |

### Epic 4: Post tracking
| ID | User story | Priority |
|---|---|---|
| US-13 | As a manager, I want each assigned creator's TikTok posts pulled in automatically, so I don't check their accounts manually. | MVP |
| US-14 | As a manager, I want posts matched to a campaign by its tracking hashtags. | MVP |
| US-15 | As a manager, I can manually add a post by link when automatic sync misses one. | MVP |
| US-16 | As a manager, I can move or remove a post that was matched to the wrong campaign. | MVP |
| US-17 | As a manager, I can see each post's views, likes, comments and shares, refreshed regularly. | MVP |
| US-18 | As a manager, I can see when data was last synced so I know how current it is. | MVP |

### Epic 5: Dashboards and monitoring
| ID | User story | Priority |
|---|---|---|
| US-19 | As a manager, I can open a campaign dashboard showing every creator's posts vs target for the current period. | MVP |
| US-20 | As a manager, I can see a campaign's total performance (posts, views, engagement). | MVP |
| US-21 | As a manager, I can open a creator's page showing their posts and performance across all campaigns. | MVP |
| US-22 | As a manager, I can see which creators are behind target this period, so I know who to chase. | MVP |

### Epic 6: AI access via MCP
| ID | User story | Priority |
|---|---|---|
| US-23 | As a manager, I can connect my AI assistant to Hookd Tracker securely, so it only sees my data. | Extension |
| US-24 | As a manager, I can ask my AI assistant about a campaign's progress and get answers from live data. | Extension |
| US-25 | As a manager, I can ask my AI assistant which creators are behind target. | Extension |
| US-26 | As a manager, I can ask my AI assistant how a specific creator is performing across campaigns. | Extension |
| US-27 | As a manager, I can update a creator's target through my AI assistant. | Extension |

### Future scope
| ID | User story | Phase |
|---|---|---|
| US-28 | As a manager, I want new posts matched to campaigns by AI, even when the creator forgets the hashtag. | 2 |
| US-29 | As a manager, I can review and correct the AI's post-to-campaign matches. | 2 |
| US-30 | As a manager, I can read an AI-generated summary of each campaign's performance for client updates. | 2 |
| US-31 | As a manager, I can get a drafted follow-up message for creators who are behind target. | 2 |
| US-32 | As a manager, I can filter and sort dashboards by date range, creator or metric. | 2 |
| US-33 | As a manager, I can export a campaign report (CSV or PDF) to share with my client. | 2 |
| US-34 | As a manager, I get an alert when a creator falls behind target. | 2 |
| US-35 | As a manager, I can invite teammates to my organisation with different roles. | 2 |
| US-36 | As a creator, I can log in to see my targets and submitted posts. | 3 |
| US-37 | As a manager, I can track creators on Instagram and YouTube as well as TikTok. | 3 |
| US-38 | As a manager, I can record creator fees and payment status per campaign. | 2 |

#### Future: agent-native management (Phase 2)
| ID | User story | Phase |
|---|---|---|
| US-39 | As a Host, I can connect my AI agent with scoped permissions (read-only or read-write), so it can only do what I allow. | 2 |
| US-40 | As a Host, I want my agent to ask for my confirmation before sensitive actions (removing a creator, changing fees), so mistakes are caught. | 2 |
| US-41 | As a Host, I can see an audit log of every action my agent took. | 2 |
| US-42 | As a Host, I can create campaigns, assign creators and set targets entirely through my agent. | 2 |
| US-43 | As a Host, I can ask my agent to message creators who are behind target, and the messages are sent through Hookd. | 2 |
| US-44 | As a Host, I can ask my agent for a campaign report and get it without opening the dashboard. | 2 |

#### Future: creator platform (Phase 3)
| ID | User story | Phase |
|---|---|---|
| US-45 | As a creator, I can build a profile with my niches, rates and connected social accounts, with verified audience stats. | 3 |
| US-46 | As a creator, I can read and reply to messages from Hosts about my campaigns. | 3 |

#### Future: marketplace (Phase 4)
| ID | User story | Phase |
|---|---|---|
| US-47 | As a Host, I can publish a campaign listing with a brief, deliverables, budget and creator requirements. | 4 |
| US-48 | As a creator, I can browse campaign listings and apply to the ones that fit me. | 4 |
| US-49 | As a Host, I get AI-ranked creator recommendations and applications for my campaign. | 4 |
| US-50 | As a Host, I can accept an application so the creator joins my campaign with agreed targets and fees. | 4 |
| US-51 | As a Host, I can ask my agent to shortlist applicants and invite the best matches. | 4 |
| US-52 | As a Host, I can pay creators through Hookd when their deliverables are met. | 4 |

**Totals:** 22 MVP · 5 Extension · 25 Future

---

## 6. Core Features (A3)

1. **Authentication** — sign up, log in, log out (Cognito)
2. **Campaign management** — create, edit, archive, delete, list with progress
3. **Creator management** — roster CRUD, campaign assignment, per-period targets
4. **TikTok sync** — scheduled background sync of posts and metrics, hashtag-based campaign matching
5. **Manual post entry** — add, move or remove posts when sync misses or mismatches
6. **Campaign dashboard** — posts vs target per creator, total campaign performance
7. **Creator view** — one creator's posts and performance across campaigns
8. **Behind-target flags** — who to chase this period
9. **Home page** — public landing page with hook, features and login/sign-up links
10. **MCP server** *(extension)* — AI assistants can query campaigns and creators and update targets

### MCP tools
| Tool | Purpose |
|---|---|
| `list_campaigns` | Campaigns with status and progress |
| `get_campaign_progress` | Each creator's posts vs target for a campaign |
| `list_behind_target_creators` | Creators behind target this period |
| `get_creator_performance` | One creator's posts and metrics across campaigns |
| `update_creator_target` | Change a creator's target (write action) |

In A3 the MCP server is an extension. In the long-term product it becomes the **main way Hosts manage creators**. The A3 tools are therefore treated as version 1 of that agent contract:
- Tools call the public API with the user's token, with no private shortcuts. Every agent action follows the same organisation scoping and validation as the web app.
- Tool names, descriptions and outputs are written for an LLM to read: plain language, explicit units and periods, and short summaries next to raw numbers.
- Write tools return what changed (before → after), so the agent can confirm it to the Host.

### Planned MCP tools (Phase 2+, not in A3)
| Tool | Phase | Purpose |
|---|---|---|
| `create_campaign` / `update_campaign` | 2 | Run campaign setup from the agent |
| `assign_creator` / `remove_creator_from_campaign` | 2 | Manage the campaign roster (removal needs confirmation) |
| `message_creator` | 2 | Send a follow-up or brief to a creator through Hookd |
| `get_campaign_report` | 2 | AI summary plus key metrics, ready for a client update |
| `list_agent_actions` | 2 | The Host reviews what its agent has done |
| `list_applications` / `accept_application` | 4 | Review and sign applicants |
| `recommend_creators` | 4 | AI-ranked creators for a campaign listing |
| `record_payment` | 4 | Mark deliverables paid |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Scalability** | API scales horizontally on CPU/request load; sync workers scale on SQS queue depth; frontends scale via CloudFront. Components scale independently so a sync surge does not slow the dashboard. |
| **Performance** | Dashboard loads in under 2 seconds for a campaign with up to 50 creators; cached aggregates served from Redis; API p95 latency under 500 ms for read endpoints. |
| **Availability** | Stateless API and workers across at least two Availability Zones behind a load balancer; failed tasks replaced automatically. |
| **Statelessness** | No session or application state stored in containers; state lives in RDS, Redis, S3 and Cognito. |
| **Data freshness** | Post metrics refreshed on a schedule (e.g. every few hours); "last synced" time shown to users. |
| **Reliability** | Sync jobs are idempotent and retried on failure; failed messages go to a dead-letter queue. |
| **Security** | HTTPS everywhere (ACM); Cognito JWT auth on API and MCP server; every query scoped to the user's organisation; secrets in Secrets Manager; least-privilege IAM roles; database in private subnets. |
| **Cost efficiency** | Static frontends on S3 + CloudFront; workers scale down when idle; caching reduces database load; TikTok API calls minimised by syncing only active campaigns. |
| **Maintainability** | Infrastructure as code; typed API contract (OpenAPI) shared with the frontend; automated tests and CI/CD. |
| **Observability** | Centralised logs, metrics and alarms in CloudWatch (API latency, error rate, queue depth, sync failures). |
| **Extensibility** | API-first and queue-based design so new platforms, AI features and team support can be added without architectural changes. |
| **Usability** | Responsive layout for desktop and mobile; clear behind-target indicators. |

---

## 8. Tech Stack

### Frontend
| Layer | Choice |
|---|---|
| Home page (A3) | **HTML, CSS, JavaScript** + **GSAP** for animations — responsive, animated, hosted statically |
| Marketing site (future) | **Astro** + Tailwind — reusable components, layouts, Markdown blog, SEO; existing HTML/CSS/JS migrates over |
| App (login, dashboards, campaigns, creators) | **React + Vite**, TypeScript, TanStack Query, Tailwind, Recharts |
| API types in frontend | **openapi-typescript**, generated from FastAPI's OpenAPI schema |
| Hosting | **S3 + CloudFront** — `hookdtracker.com` (marketing) and `app.hookdtracker.com` (app) |

### Backend
| Layer | Choice |
|---|---|
| Language | **Python 3.12+** |
| API | **FastAPI** + Pydantic, in Docker on **ECS Fargate** |
| Database access | **SQLAlchemy 2.0** (Python ORM library) + **Alembic** (migrations) |
| Background workers | Python containers on **ECS Fargate**, consuming **SQS** |
| Scheduling | **EventBridge Scheduler** → SQS |
| MCP server | **Official MCP Python SDK (FastMCP)**, its own container on Fargate |

### Data and AWS services
| Layer | Choice |
|---|---|
| Database | **PostgreSQL on Amazon RDS** |
| Cache | **ElastiCache (Redis/Valkey)** |
| Auth | **Amazon Cognito** |
| File storage | **S3** |
| Secrets | **Secrets Manager** |
| Routing | **Application Load Balancer**, **Route 53**, **ACM** |
| Container registry | **ECR** |
| Monitoring | **CloudWatch** |

### Tooling
| Layer | Choice |
|---|---|
| Infrastructure as code | **Terraform** or **AWS CDK (Python)** |
| CI/CD | **GitHub Actions** → ECR → ECS |
| Local development | **Docker Compose** — API, worker, MCP, Postgres, Redis |
| Python tooling | **uv** (dependencies), **Ruff** (lint/format), **pytest** |

### Why containers for the backend only
Docker packages the code; AWS managed services hold the state. The API, workers and MCP server run as containers so they can scale and be replaced freely. The frontends are static files on S3 + CloudFront (cheaper, faster, no servers). The database runs on RDS rather than in a container, so backups, failover and patching are managed.

---

## 9. Cloud Architecture

```mermaid
flowchart LR
    U[Campaign manager<br/>browser] --> R53[Route 53]
    AI[AI assistant<br/>Claude / ChatGPT] --> ALB

    R53 --> CF1[CloudFront<br/>hookdtracker.com]
    R53 --> CF2[CloudFront<br/>app.hookdtracker.com]
    CF1 --> S3W[S3<br/>home / marketing site]
    CF2 --> S3A[S3<br/>React app]

    U -- login --> COG[Cognito]
    U -- API calls + JWT --> ALB[Application<br/>Load Balancer]

    ALB -- /api --> API[FastAPI service<br/>ECS Fargate, autoscaled]
    ALB -- /mcp --> MCP[MCP server<br/>ECS Fargate]
    MCP -- calls with user token --> API

    API --> REDIS[(ElastiCache<br/>Redis)]
    API --> RDS[(RDS<br/>PostgreSQL)]
    API --> S3M[S3<br/>media]
    API -- manual sync request --> SQS[SQS<br/>sync queue]

    EB[EventBridge<br/>Scheduler] -- scheduled sync --> SQS
    SQS --> W[Sync workers<br/>ECS Fargate, scale on queue depth]
    SQS -. failures .-> DLQ[Dead-letter queue]
    W --> TT[TikTok API]
    W --> RDS
    W -- invalidate --> REDIS

    SM[Secrets Manager] -.-> API
    SM -.-> W
    CW[CloudWatch] -.-> API
    CW -.-> W
    CW -.-> SQS
```

### Components
| Component | Role |
|---|---|
| **CloudFront + S3** | Serve the home page and React app as static files from a global CDN |
| **Cognito** | Sign-up, login and JWT issuance for the app, API and MCP server |
| **Application Load Balancer** | HTTPS entry point; routes `/api` to the API and `/mcp` to the MCP server |
| **FastAPI service** | Stateless REST API for campaigns, creators, assignments, posts and dashboards |
| **MCP server** | Exposes Hookd Tracker tools to AI assistants; calls the API with the user's token |
| **RDS PostgreSQL** | Source of truth for all relational data, in private subnets |
| **ElastiCache Redis** | Caches dashboard aggregates and campaign progress |
| **EventBridge Scheduler** | Triggers periodic syncs |
| **SQS + DLQ** | Buffers sync jobs; failed jobs retried, then moved to the dead-letter queue |
| **Sync workers** | Fetch posts and metrics from TikTok, match to campaigns by hashtag, write to RDS, invalidate cache |
| **Secrets Manager** | TikTok API credentials and database credentials |
| **CloudWatch** | Logs, metrics, alarms; queue depth and CPU drive autoscaling |

### Key flows

**1. Scheduled sync**
1. EventBridge Scheduler fires on a schedule.
2. One job per active campaign–creator pair is placed on SQS.
3. Workers scale out with queue depth, fetch each creator's recent posts and metrics from TikTok.
4. Posts are matched to campaigns by tracking hashtags and upserted into RDS.
5. Affected dashboard cache entries in Redis are invalidated.

**2. Viewing a campaign dashboard**
1. The React app calls `GET /api/campaigns/{id}/dashboard` with the user's JWT.
2. The API checks Redis; on a hit it returns the cached aggregate.
3. On a miss it queries RDS, computes posts vs target per creator, caches the result and returns it.

**3. AI query via MCP**
1. The manager asks their AI assistant, "Which creators are behind on this campaign?"
2. The assistant calls the `list_behind_target_creators` tool on the MCP server.
3. The MCP server calls the API with the user's token; the API answers (from cache where possible).
4. The assistant replies using live Hookd Tracker data.

### Scaling and caching summary
- **Autoscaling:** API tasks scale on CPU/request count; worker tasks scale on SQS queue depth (scale to minimum when idle).
- **Caching:** dashboard aggregates in Redis with sync-driven invalidation; static frontends cached at CloudFront edge locations.

---

## 10. Repository Structure

```
hookd-tracker/
├── apps/
│   ├── www/        # Home page (HTML/CSS/JS + GSAP; Astro later)
│   ├── web/        # React + Vite app
│   ├── api/        # FastAPI service
│   ├── worker/     # SQS sync workers
│   └── mcp/        # MCP server
├── packages/
│   └── ui/         # Shared design tokens and components
├── infra/          # Terraform or CDK
├── docker-compose.yml
└── .github/workflows/
```

---

## 11. Build Order

1. **Foundations** — repo, Docker Compose, Postgres schema and migrations, Cognito auth
2. **Core CRUD** — campaigns, creators, assignments and targets (API + React screens)
3. **Post tracking** — manual post entry, then TikTok sync through SQS workers
4. **Dashboards** — campaign and creator views, behind-target flags, Redis caching
5. **Home page** — responsive, animated landing page with login/sign-up links
6. **Cloud deployment** — infrastructure as code, ECS Fargate, ALB, autoscaling policies, CI/CD
7. **Load testing** — demonstrate API and worker autoscaling and cache hit rates
8. **MCP server (extension)** — built last as a separate service; can be dropped without affecting the core

---

## 12. Risks and Assumptions

| Risk | Mitigation |
|---|---|
| **TikTok API access** — TikTok restricts access to other accounts' post data | Confirm API access early. Fallbacks: creators connect their own accounts via TikTok login, manual post entry, or seeded/mock data for the A3 demo |
| **AWS service limits** in the course account (ElastiCache, Cognito, Fargate) | Check the CAB432 account early and swap equivalents if needed |
| **Time** — MCP extension competes with core requirements | Build MCP last as an independent service |
| **TikTok API rate limits** | Queue-based sync with controlled concurrency, retries and backoff; sync only active campaigns |
| **Cost** | Scale workers to minimum when idle, small instance sizes, cache aggressively, tear down non-demo environments |

### Long-term risks (beyond A3)
| Risk | Mitigation |
|---|---|
| **Agent takes a wrong or harmful action** (e.g. removes a creator, messages the wrong person) | Scoped agent permissions, Host confirmation for sensitive actions, full audit log, reversible writes where possible |
| **Marketplace cold start**: no creators without Hosts, and no Hosts without creators | Launch management first (Phases 1–2) so Hosts bring their own creators; invite those creators to the platform in Phase 3 before opening the marketplace |
| **Social platform data access** | Creator accounts connect their own social accounts via OAuth (Phase 3), giving first-party, consented access instead of scraping |
| **MCP and agent ecosystem changes** | Keep MCP a thin layer over the REST API, so protocol changes only touch the MCP service |
| **Creator privacy and payments compliance** | Store only consented creator data; use an established payments provider instead of handling funds directly |

---

## 13. Future Architecture Notes

The A3 design already supports the commercial roadmap:
- **AI matching and summaries** → extra steps in the existing worker pipeline; summaries cached and regenerated after each sync.
- **More platforms** → new fetchers behind the same sync interface, using the existing `platform` field.
- **Teams and roles** → data already scoped by `organisation_id`; Cognito groups for roles.
- **Alerts and exports** → triggered after each sync via the queue.
- **Marketing site and SEO** → migrate the home page to Astro with features, pricing and blog pages.

### Path to the AI-powered UGC platform
| Phase | Architecture change | Builds on (A3) |
|---|---|---|
| 2: Agent-native management | MCP authorisation via OAuth (per the MCP spec) with per-agent scopes; `AgentAction` audit log; `PendingAction` records the Host approves in the web app or by email; per-agent rate limits | MCP server as its own service calling the API; Cognito JWTs; organisation scoping |
| 2: Messaging and alerts | Notification service fed by SQS, sending email (SES) and in-app messages | SQS and worker pipeline |
| 3: Creator platform | Separate Host and creator roles (Cognito groups or a second user pool); creator OAuth connections to TikTok, Instagram and YouTube | `platform` field; sync fetcher interface; Creator roster entries linked to accounts |
| 4: Marketplace and matching | Listings and applications in RDS; creator and campaign embeddings (e.g. pgvector on RDS) for AI matching; LLM ranking and explanations | Stored captions and hashtags; post metrics history; worker pipeline |
| 4: Payments | Payments provider integration (e.g. Stripe Connect) with payouts triggered by deliverables being met | CampaignCreator targets and post tracking as proof of delivery |

**Design rules for A3 that keep this path open**
1. Every feature goes through the REST API first. The web app and MCP server are both clients of it.
2. All data stays scoped by `organisation_id` (the Host).
3. Targets and deliverables live on the CampaignCreator relationship, not on the creator.
4. Background work goes through queues, so AI, messaging and payment steps can be added as new consumers.
