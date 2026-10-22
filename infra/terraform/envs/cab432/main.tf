# Hookd Tracker on the CAB432 account.
# Account-specific choices live in cab432.tfvars; modules are shared with envs/personal.

locals {
  name = var.name_prefix

  images = { for s in ["api", "worker", "mcp", "web"] : s => "${module.registry.repository_urls[s]}:${var.image_tag}" }

  # Env shared by the Python services (AWS_ENDPOINT_URL must stay unset in AWS)
  common_env = {
    AWS_REGION            = var.aws_region
    SYNC_QUEUE_URL        = module.queue.queue_url
    REDIS_URL             = module.cache.redis_url
    COGNITO_USER_POOL_ID  = module.auth.user_pool_id
    COGNITO_APP_CLIENT_ID = module.auth.client_id
    TIKTOK_MODE           = var.tiktok_mode
    STORAGE               = "dynamodb"
    DYNAMODB_TABLE        = module.table.name
    SYNC_MODE             = "queue" # "Sync now" goes to the worker over SQS
  }
}

module "registry" {
  source       = "../../modules/registry"
  name_prefix  = local.name
  repositories = ["api", "worker", "mcp", "web"]
}

module "queue" {
  source              = "../../modules/queue"
  name                = "${local.name}-sync"
  schedule_expression = var.sync_schedule
  scheduler_role_arn  = var.scheduler_role_arn
}

module "secrets" {
  source = "../../modules/secrets"
  name   = "${local.name}-app"
  keys   = ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"]
}

module "cache" {
  source             = "../../modules/cache"
  name               = "${local.name}-cache"
  subnet_ids         = var.private_subnet_ids
  security_group_ids = var.cache_security_group_ids
  port               = var.cache_port
}

module "auth" {
  source                = "../../modules/auth"
  name                  = local.name
  existing_user_pool_id = var.existing_cognito_user_pool_id
}

module "cluster" {
  source                = "../../modules/cluster"
  name                  = local.name
  existing_cluster_name = var.existing_ecs_cluster_name
  task_role_arn         = var.task_role_arn
  execution_role_arn    = var.execution_role_arn
  queue_arns            = [module.queue.queue_arn]
  table_arns            = [module.table.arn]
  secret_arns           = [module.secrets.arn]
}

# All app data. RDS is blocked on CAB432; the plan is to move back to RDS after A3
module "table" {
  source = "../../modules/table"
  name   = local.name
}

module "edge" {
  source             = "../../modules/edge"
  name               = local.name
  vpc_id             = var.vpc_id
  subnet_ids         = var.public_subnet_ids
  security_group_ids = var.alb_security_group_ids
  certificate_arn    = var.certificate_arn
  domain_name        = var.domain_name
  zone_name          = var.zone_name

  dns_allow_overwrite = var.dns_allow_overwrite
  enable_cloudfront   = var.enable_cloudfront

  default_service = "web"
  services = {
    web = { health_path = "/" }
    api = { health_path = "/api/health", paths = ["/api", "/api/*"], priority = 10 }
    # MCP answers a plain GET with 4xx, which still means it's up
    mcp = { health_path = "/mcp", health_matcher = "200-499", paths = ["/mcp", "/mcp/*"], priority = 20 }
  }
}

# --- Services ---

module "api" {
  source             = "../../modules/service"
  name               = "${local.name}-api"
  image              = local.images.api
  log_retention_days = var.log_retention_days

  cluster_name       = module.cluster.cluster_name
  cluster_arn        = module.cluster.cluster_arn
  task_role_arn      = module.cluster.task_role_arn
  execution_role_arn = module.cluster.execution_role_arn
  subnet_ids         = var.private_subnet_ids
  security_group_ids = var.service_security_group_ids

  container_port   = 8080
  target_group_arn = module.edge.target_group_arns.api
  command = [
    "uvicorn", "hookd_api.main:app", "--host", "0.0.0.0", "--port", "8080",
    "--proxy-headers", "--forwarded-allow-ips", "*",
  ]
  environment = merge(local.common_env, lookup(var.extra_environment, "api", {}))

  desired_count = 1
  autoscaling = {
    min_capacity        = 1
    max_capacity        = 4
    cpu_target          = 60
    requests_per_target = 50
    alb_resource_label  = module.edge.resource_labels.api
  }
}

module "worker" {
  source             = "../../modules/service"
  name               = "${local.name}-worker"
  image              = local.images.worker
  log_retention_days = var.log_retention_days

  cluster_name       = module.cluster.cluster_name
  cluster_arn        = module.cluster.cluster_arn
  task_role_arn      = module.cluster.task_role_arn
  execution_role_arn = module.cluster.execution_role_arn
  subnet_ids         = var.private_subnet_ids
  security_group_ids = var.service_security_group_ids

  environment = merge(local.common_env, lookup(var.extra_environment, "worker", {}))
  secrets = {
    TIKTOK_CLIENT_KEY    = module.secrets.value_from.TIKTOK_CLIENT_KEY
    TIKTOK_CLIENT_SECRET = module.secrets.value_from.TIKTOK_CLIENT_SECRET
  }

  # Worker-pull: idle at 0 tasks, scale on sync queue depth
  desired_count = 0
  autoscaling = {
    min_capacity       = 0
    max_capacity       = 4
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
  queue_scaling = {
    queue_name   = module.queue.queue_name
    idle_minutes = 5
  }
}

module "mcp" {
  source             = "../../modules/service"
  name               = "${local.name}-mcp"
  image              = local.images.mcp
  log_retention_days = var.log_retention_days

  cluster_name       = module.cluster.cluster_name
  cluster_arn        = module.cluster.cluster_arn
  task_role_arn      = module.cluster.task_role_arn
  execution_role_arn = module.cluster.execution_role_arn
  subnet_ids         = var.private_subnet_ids
  security_group_ids = var.service_security_group_ids

  container_port   = 8080
  target_group_arn = module.edge.target_group_arns.mcp
  environment = merge(
    local.common_env,
    { HOOKD_API_URL = "https://${var.domain_name}/api", PORT = "8080" },
    lookup(var.extra_environment, "mcp", {}),
  )

  desired_count = 1
}

module "web" {
  source             = "../../modules/service"
  name               = "${local.name}-web"
  image              = local.images.web
  log_retention_days = var.log_retention_days

  cluster_name       = module.cluster.cluster_name
  cluster_arn        = module.cluster.cluster_arn
  task_role_arn      = module.cluster.task_role_arn
  execution_role_arn = module.cluster.execution_role_arn
  subnet_ids         = var.private_subnet_ids
  security_group_ids = var.service_security_group_ids

  # nginx serving the built SPA; Cognito ids are baked in at build time
  container_port   = 8080
  target_group_arn = module.edge.target_group_arns.web
  environment      = lookup(var.extra_environment, "web", {})

  desired_count = 1
}

module "observability" {
  source         = "../../modules/observability"
  name           = local.name
  alb_arn_suffix = module.edge.alb_arn_suffix
  cluster_name   = module.cluster.cluster_name
  service_names = {
    api    = module.api.service_name
    worker = module.worker.service_name
    mcp    = module.mcp.service_name
    web    = module.web.service_name
  }
  queue_name        = module.queue.queue_name
  dlq_name          = module.queue.dlq_name
  cache_cluster_ids = module.cache.cluster_ids
}
