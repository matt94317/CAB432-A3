output "app_url" {
  description = "Open this (CloudFront, or the custom domain when CloudFront is off)"
  value       = module.edge.app_url
}

output "api_url" {
  value = "${module.edge.app_url}/api"
}

output "domain_url" {
  description = "ALB through the custom domain"
  value       = module.edge.domain_url
}

output "alb_dns_name" {
  value = module.edge.alb_dns_name
}

output "cloudfront_distribution_id" {
  value = module.edge.cloudfront_id
}

# --- Used by scripts/deploy.sh ---

output "aws_profile" {
  value = var.aws_profile
}

output "aws_region" {
  value = var.aws_region
}

output "ecr_repository_urls" {
  value = module.registry.repository_urls
}

output "ecs_cluster_name" {
  value = module.cluster.cluster_name
}

output "ecs_service_names" {
  value = {
    api    = module.api.service_name
    worker = module.worker.service_name
    mcp    = module.mcp.service_name
    web    = module.web.service_name
  }
}

output "cognito_user_pool_id" {
  value = module.auth.user_pool_id
}

output "cognito_client_id" {
  value = module.auth.client_id
}

# --- Backing services ---

output "sync_queue_url" {
  value = module.queue.queue_url
}

output "dlq_url" {
  value = module.queue.dlq_url
}

output "cache_endpoint" {
  value = "${module.cache.primary_endpoint}:${module.cache.port}"
}

output "secret_name" {
  description = "Set real TikTok values here (put-secret-value)"
  value       = module.secrets.name
}

output "dashboard_name" {
  value = module.observability.dashboard_name
}

# --- Gradescope infrastructure YAML (terraform output -raw gradescope_infra_yaml) ---

locals {
  services = {
    api    = { module = module.api, what = "FastAPI REST API" }
    worker = { module = module.worker, what = "SQS sync worker" }
    mcp    = { module = module.mcp, what = "MCP server for AI assistants" }
    web    = { module = module.web, what = "nginx serving the React app" }
  }

  infra = concat(
    [
      { type = "ECS cluster", arn = module.cluster.cluster_arn, description = "Fargate cluster that runs the api, worker, mcp and web services." },
    ],
    [for k, s in local.services : {
      type        = "ECS service"
      arn         = s.module.service_arn
      description = "Runs the ${s.what} as Fargate tasks in private subnets."
    }],
    [for k, s in local.services : {
      type        = "CloudWatch log group"
      arn         = s.module.log_group_arn
      description = "Container logs for the ${k} service."
    }],
    [for k, url in module.registry.repository_urls : {
      type        = "ECR repository"
      arn         = module.registry.repository_arns[k]
      description = "Container images for the ${k} service."
    }],
    [
      { type = "Application Auto Scaling target", arn = module.api.autoscaling_target_id, description = "Scales the API from 1 to 4 tasks on CPU and requests per task." },
      { type = "Application Auto Scaling target", arn = module.worker.autoscaling_target_id, description = "Scales sync workers from 0 to 4 tasks on SQS queue depth." },
      { type = "Application Load Balancer", arn = module.edge.alb_arn, description = "HTTPS entry point routing /api, /mcp and the web app to their services." },
      { type = "SQS queue", arn = module.queue.queue_arn, description = "Buffers TikTok sync jobs for the workers." },
      { type = "SQS queue", arn = module.queue.dlq_arn, description = "Dead-letter queue for sync jobs that keep failing." },
      { type = "EventBridge Scheduler schedule", arn = module.queue.schedule_arn, description = "Queues a scheduled sync every 6 hours." },
      { type = "Secrets Manager secret", arn = module.secrets.arn, description = "TikTok API credentials injected into the worker." },
      { type = "ElastiCache replication group", arn = module.cache.arn, description = "Valkey cache for dashboard aggregates." },
      { type = "Cognito user pool", arn = module.auth.user_pool_arn, description = "Sign-up, login and JWTs for the app, API and MCP server." },
      { type = "Cognito user pool client", arn = module.auth.client_id, description = "Public app client the React app uses to sign in." },
      { type = "ACM certificate", arn = var.certificate_arn, description = "TLS certificate for ${var.domain_name} on the ALB." },
      { type = "CloudWatch dashboard", arn = module.observability.dashboard_arn, description = "Shows load, latency, errors, task counts, queue depth and cache hits." },
      { type = "CloudWatch alarm", arn = module.observability.alarm_arns.dlq, description = "Fires when a sync job lands in the dead-letter queue." },
      { type = "CloudWatch alarm", arn = module.observability.alarm_arns.alb_5xx, description = "Fires when the ALB returns too many 5xx errors." },
      { type = "CloudWatch alarm", arn = module.worker.scaling_alarm_arns[0], description = "Scales sync workers out when jobs are waiting in the SQS queue." },
      { type = "CloudWatch alarm", arn = module.worker.scaling_alarm_arns[1], description = "Scales sync workers back in to zero when the SQS queue is empty." },
    ],
    module.edge.dns_record_fqdn == null ? [] : [
      { type = "Route 53 record", arn = module.edge.dns_record_fqdn, description = "Points ${var.domain_name} at the ALB." },
    ],
    var.enable_cloudfront ? [
      { type = "CloudFront distribution", arn = module.edge.cloudfront_arn, description = "Edge cache for the web app; passes /api and /mcp to the ALB." },
    ] : [],
  )
}

output "gradescope_infra_yaml" {
  value = yamlencode({
    cloudInfrastructure = local.infra
    metaData            = { qutUsernameTag = var.qut_username }
  })
}
