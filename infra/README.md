# Infrastructure

Terraform for AWS (plan section 9). `local/` holds config for local development only (docker compose).

```
terraform/
  modules/        one per concern, shared by every account
    registry        ECR repos (scan on push, keep last 10 images)
    queue           SQS sync queue + DLQ, EventBridge Scheduler schedule
    secrets         Secrets Manager secret (TikTok credentials)
    cache           ElastiCache Valkey
    auth            Cognito app client (+ user pool when not reusing one)
    cluster         ECS cluster + task/execution roles (reuse or create)
    edge            ALB, target groups, HTTPS listener, Route 53 alias, CloudFront
    service         one ECS Fargate service: log group, task def, autoscaling
    observability   CloudWatch dashboard and alarms
  envs/
    cab432/       the CAB432 shared account (assignment 3)
```

## What gets deployed

```
browser -> CloudFront (*.cloudfront.net) -> n12191434.cab432.com (ALB, HTTPS)
             /          -> web    (nginx + React build)
             /api/*     -> api    (FastAPI, 1-4 tasks, CPU + requests/task)
             /mcp*      -> mcp    (MCP server)
EventBridge Scheduler (6 h) -> SQS -> worker (0-4 tasks on queue depth) -> DLQ after 5 tries
api / worker -> Valkey (ElastiCache), Cognito, Secrets Manager
```

All services run on Fargate (ARM64) in the private subnets and listen on 8080.
CloudFront caches the SPA and passes `/api` and `/mcp` through uncached.

## Prerequisites

- Terraform >= 1.10, AWS CLI v2, Docker with buildx, jq
- An SSO profile named `CAB432` for account 901444280953. The provider always
  uses this named profile and refuses any other account, so your default
  profile is never touched.

## Deploy

```bash
aws sso login --profile CAB432

cd infra/terraform/envs/cab432
terraform init
terraform plan  -var-file=cab432.tfvars
terraform apply -var-file=cab432.tfvars

cd ../../../..
scripts/deploy.sh            # build arm64 images, push to ECR, roll the services
scripts/deploy.sh api        # or just some of them
```

The first apply creates the services before any image exists; their tasks fail
to start until `scripts/deploy.sh` has pushed images, then they come up.

After the first apply, set the real TikTok credentials (Terraform only writes
placeholders and ignores the value afterwards):

```bash
aws secretsmanager put-secret-value --profile CAB432 \
  --secret-id n12191434-a3-hookd-app \
  --secret-string '{"TIKTOK_CLIENT_KEY":"...","TIKTOK_CLIENT_SECRET":"..."}'
scripts/deploy.sh worker     # tasks read secrets at start
```

To watch auto scaling, `scripts/scaling-test.sh` fills the sync queue with
fake jobs (worker 0 → 4 → 0) and then loads `/api/health` on the ALB with `ab`
(api 1 → 4), printing task counts, queue depth and firing alarms every 30s:

```bash
scripts/scaling-test.sh            # worker, then api (~25 min)
scripts/scaling-test.sh worker     # or just one part
scripts/scaling-test.sh status     # one status line, no load
```

Useful outputs: `terraform output app_url`, and
`terraform output -raw gradescope_infra_yaml > ../../../../submission-a3-infra.yml` to
refresh the Gradescope file at the repo root.

## CAB432 constraints

The shared account blocks some actions, so `cab432.tfvars` passes existing
resources in. Each module creates the resource itself when the input is `null`.

| Resource | CAB432 | Why |
|---|---|---|
| IAM task / execution roles | reused `Task-Role-CAB432-ECS`, `Execution-Role-CAB432-ECS` | can't create IAM roles or policies |
| Scheduler role | reused `CAB432-EventBridge-scheduler-Role` | same |
| Security groups | reused `CAB432SG` (ALB + services), `CAB432MemcachedSG` (cache) | can't create security groups |
| VPC / subnets | shared CAB432 VPC | provided |
| ECS cluster | reused `n12191434-a2-cluster` | already exists (Container Insights on) |
| Cognito user pool | **created** (`n12191434-a3-hookd`) with its app client | A2's pool (`ap-southeast-2_ZvcLlofqW`) had no email verification; A3 owns its settings |
| ACM cert, Route 53 zone | reused | already issued / shared zone |
| Database | **DynamoDB table created** (`n12191434-a3-hookd`, on-demand) | RDS is blocked; back to RDS after A3 |
| Everything else | created, named `n12191434-a3-hookd-*` | tagged `qut-username`, `purpose = assessment 3`, `project = hookd` |

Things to know:

- **Valkey on port 11211.** Port 6379 isn't open in any security group we can
  use, but `CAB432MemcachedSG` allows 11211 from `CAB432SG`. Valkey doesn't care
  which port it listens on, so the cache runs on 11211 and
  `REDIS_URL=redis://<endpoint>:11211/0`.
- **Containers listen on 8080**, which `CAB432SG` allows from anywhere (the ALB
  shares the same SG). The MCP server reads `PORT` (default 8001 locally).
- **Log groups can't be deleted** by students, so they use `skip_destroy`:
  `terraform destroy` leaves them behind and a later apply fails until they are
  imported (`terraform import 'module.api.aws_cloudwatch_log_group.this' /ecs/n12191434-a3-hookd-api`).
- **DNS:** `n12191434.cab432.com` still points at the A2 API Gateway domain.
  Apply fails on the Route 53 record until either that record is removed or
  `dns_allow_overwrite = true` is set in `cab432.tfvars` (which breaks A2).
- **Images are ARM64** (built on Apple Silicon); task definitions use the ARM64
  runtime platform.
- **DynamoDB permissions.** The services need `GetItem`, `PutItem`,
  `DeleteItem` and `Query` on the table and its `gsi1` index. The reused
  `Task-Role-CAB432-ECS` was only checked for put and query (2026-10-17), so
  confirm GetItem and DeleteItem after the first deploy (e.g. sign in and
  delete a campaign). In our own account the cluster module creates a role with
  exactly these (see [Personal account later](#personal-account-later)).

## State

Local state for now (`*.tfstate` is gitignored), so apply from one machine.
`envs/cab432/versions.tf` has a commented S3 backend with `use_lockfile`
(S3-native locking) to switch to shared state.

## Personal account later

To run Hookd Tracker in our own AWS account after the assignment, copy
`envs/cab432` to `envs/personal` and change the variables below; the modules
stay the same. Setting the reuse inputs to `null` makes the modules create the
resource themselves.

| Variable | CAB432 | Personal |
|---|---|---|
| `aws_profile`, `account_id` | `CAB432`, 901444280953 | own profile and account |
| `name_prefix`, tags | `n12191434-a3-hookd`, QUT tags | e.g. `hookd-prod`; drop `qut_username`/`purpose` from `default_tags` |
| `existing_ecs_cluster_name` | `n12191434-a2-cluster` | `null` (module creates a cluster with Container Insights) |
| `task_role_arn`, `execution_role_arn` | pre-made CAB432 roles | `null` (module creates least-privilege roles, including the DynamoDB actions above) |
| `scheduler_role_arn` | `CAB432-EventBridge-scheduler-Role` | `null` (queue module creates one) |
| `existing_cognito_user_pool_id` | `null` (A3 creates its own pool) | `null` |
| Security groups | `CAB432SG`, `CAB432MemcachedSG` | own SGs: ALB 443 from anywhere, services 8080 from the ALB SG, cache 6379 from the service SG |
| `cache_port` | 11211 (only port the CAB432 SG opens) | 6379 |
| `vpc_id`, subnets | shared CAB432 VPC | own VPC; add a `network` module (VPC, 2+ AZs, NAT) |
| Domain / cert | `n12191434.cab432.com` | `app.hookdtracker.com`, its own ACM cert and zone |
| `dns_allow_overwrite` | `true` (see DNS above) | not needed |
| `log_retention_days` | `0` (`logs:PutRetentionPolicy` is denied) | default 14 |

Also add a remote state backend (the S3 block in `versions.tf`) and, when we
move back to RDS, a database module.

## Cognito

Terraform creates the A3 user pool and its app client (`terraform output
cognito_user_pool_id` / `cognito_client_id`): email sign-in, email verified by
code, a required `name` attribute, and a public client (no secret) using SRP
with token revocation on. Verification emails use Cognito's default sender
(50 per day), plenty for A3; switch to SES if that becomes a limit.

They were applied ahead of the rest with `terraform apply -target=module.auth`
so local development could sign in. A full apply then sees them as done. Keep
`terraform.tfstate`: without it, the next apply would create a second pool.

For local development, put the pool id and client id in `.env` (`COGNITO_*`,
for the API) and `apps/web/.env` (`VITE_COGNITO_*`).

Sessions: access tokens last 60 minutes and are refreshed silently; the refresh
token keeps a manager signed in for 30 days. Logging out revokes the refresh token.
