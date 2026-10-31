# --- Account ---

variable "aws_profile" {
  description = "AWS CLI profile (SSO). Required so the default profile is never used."
  type        = string
}

variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "account_id" {
  description = "The only account this env may touch"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for every resource name"
  type        = string
}

variable "qut_username" {
  type = string
}

variable "purpose" {
  type = string
}

# --- Network (shared VPC) ---

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  description = "ALB subnets"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "ECS tasks and ElastiCache (NAT for outbound)"
  type        = list(string)
}

variable "alb_security_group_ids" {
  type = list(string)
}

variable "service_security_group_ids" {
  type = list(string)
}

variable "cache_security_group_ids" {
  type = list(string)
}

variable "cache_port" {
  type    = number
  default = 6379
}

# --- Existing resources (null = create) ---

variable "existing_ecs_cluster_name" {
  type    = string
  default = null
}

variable "existing_cognito_user_pool_id" {
  type    = string
  default = null
}

variable "task_role_arn" {
  type    = string
  default = null
}

variable "execution_role_arn" {
  type    = string
  default = null
}

variable "scheduler_role_arn" {
  type    = string
  default = null
}

# --- Edge ---

variable "domain_name" {
  description = "Custom domain for the ALB (and CloudFront's origin)"
  type        = string
}

variable "zone_name" {
  description = "Route 53 public zone for domain_name"
  type        = string
}

variable "certificate_arn" {
  description = "ACM cert for domain_name in aws_region"
  type        = string
}

variable "dns_allow_overwrite" {
  description = "Replace an existing A record for domain_name"
  type        = bool
  default     = false
}

variable "enable_cloudfront" {
  type    = bool
  default = true
}

# --- App ---

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "tiktok_mode" {
  description = "mock or live"
  type        = string
  default     = "mock"
}

variable "llm_provider" {
  description = "Chat model provider for the assistant: bedrock or openrouter. CAB432 denies bedrock:InvokeModel by organisation policy, so A3 uses openrouter"
  type        = string
  default     = "openrouter"
}

variable "openrouter_model" {
  type    = string
  default = "anthropic/claude-haiku-5.5"
}

variable "bedrock_model_id" {
  description = "Bedrock model or inference profile for the in-app assistant (mcp service)"
  type        = string
  default     = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "sync_schedule" {
  type    = string
  default = "rate(6 hours)"
}

# TODO(database): the database isn't chosen yet (RDS is blocked in CAB432;
# likely DynamoDB). Pass its settings here per service until it has a module,
# e.g. { api = { DATABASE_URL = "..." }, worker = { ... } }.
variable "extra_environment" {
  description = "Extra env vars per service (api, worker, mcp, web)"
  type        = map(map(string))
  default     = {}
}

variable "log_retention_days" {
  description = "ECS log retention; 0 = never expire (CAB432 denies logs:PutRetentionPolicy)"
  type        = number
  default     = 14
}
