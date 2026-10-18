# Secrets Manager secret holding app secrets as JSON.
# Terraform writes placeholders once; real values are set out of band
# (console or `aws secretsmanager put-secret-value`) and never touched again.

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

variable "keys" {
  description = "JSON keys created with placeholder values"
  type        = list(string)
}

variable "recovery_window_in_days" {
  description = "0 = delete immediately on destroy, so the name can be reused"
  type        = number
  default     = 0
}

resource "aws_secretsmanager_secret" "this" {
  name                    = var.name
  description             = "Hookd Tracker app secrets"
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret_version" "initial" {
  secret_id     = aws_secretsmanager_secret.this.id
  secret_string = jsonencode({ for k in var.keys : k => "changeme" })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

output "arn" {
  value = aws_secretsmanager_secret.this.arn
}

output "name" {
  value = aws_secretsmanager_secret.this.name
}

# ECS secrets entries: { KEY = "<arn>:KEY::" }
output "value_from" {
  value = { for k in var.keys : k => "${aws_secretsmanager_secret.this.arn}:${k}::" }
}
