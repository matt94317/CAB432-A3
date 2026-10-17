# envs/personal (not built yet)

For running Hookd Tracker in our own AWS account after the assignment. Copy
`envs/cab432` and change the variables below; the modules stay the same.

| Variable | CAB432 | Personal |
|---|---|---|
| `aws_profile`, `account_id` | `CAB432`, 901444280953 | own profile and account |
| `name_prefix`, tags | `n12191434-a3-hookd`, QUT tags | e.g. `hookd-prod`; drop `qut_username`/`purpose` from `default_tags` |
| `existing_ecs_cluster_name` | `n12191434-a2-cluster` | `null` (module creates a cluster with Container Insights) |
| `task_role_arn`, `execution_role_arn` | pre-made CAB432 roles | `null` (module creates least-privilege roles) |
| `scheduler_role_arn` | `CAB432-EventBridge-scheduler-Role` | `null` (queue module creates one) |
| `existing_cognito_user_pool_id` | shared A2 pool | `null` (auth module creates the pool) |
| Security groups | `CAB432SG`, `CAB432MemcachedSG` | own SGs: ALB 443 from anywhere, services 8080 from the ALB SG, cache 6379 from the service SG |
| `cache_port` | 11211 (only port the CAB432 SG opens) | 6379 |
| `vpc_id`, subnets | shared CAB432 VPC | own VPC; add a `network` module (VPC, 2+ AZs, NAT) |
| Domain / cert | `n12191434.cab432.com` | `app.hookdtracker.com`, its own ACM cert and zone |
| `dns_allow_overwrite` | false | not needed |

Also add a remote state backend (the S3 block in `versions.tf`) and the
database module once it's chosen.
