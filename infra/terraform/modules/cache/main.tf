# ElastiCache Valkey (Redis-compatible), single node

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

variable "name" {
  type = string
}

variable "subnet_ids" {
  description = "Private subnets"
  type        = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "port" {
  description = "6379 normally; CAB432 only opens 11211 (memcached SG)"
  type        = number
  default     = 6379
}

variable "node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "num_nodes" {
  type    = number
  default = 1
}

variable "engine_version" {
  type    = string
  default = "8.1"
}

variable "parameter_group_name" {
  type    = string
  default = "default.valkey8"
}

resource "aws_elasticache_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = var.name
  description          = "Hookd Tracker cache"

  engine               = "valkey"
  engine_version       = var.engine_version
  parameter_group_name = var.parameter_group_name
  node_type            = var.node_type
  num_cache_clusters   = var.num_nodes
  port                 = var.port

  automatic_failover_enabled = var.num_nodes > 1
  multi_az_enabled           = var.num_nodes > 1

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = var.security_group_ids

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false # app uses plain redis://

  snapshot_retention_limit = 0
  apply_immediately        = true
}

output "arn" {
  value = aws_elasticache_replication_group.this.arn
}

output "primary_endpoint" {
  value = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "port" {
  value = var.port
}

output "redis_url" {
  value = "redis://${aws_elasticache_replication_group.this.primary_endpoint_address}:${var.port}/0"
}

# Node ids for CloudWatch (metrics are per node)
output "cluster_ids" {
  value = [for i in range(var.num_nodes) : format("%s-%03d", var.name, i + 1)]
}
