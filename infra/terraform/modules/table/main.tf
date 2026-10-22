# DynamoDB table holding all app data (single-table design).
# Layout and access patterns: packages/core/src/hookd_core/repositories/dynamodb.py

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

variable "point_in_time_recovery" {
  description = "Continuous backups (restore to any second in the last 35 days)"
  type        = bool
  default     = true
}

resource "aws_dynamodb_table" "this" {
  name         = var.name
  billing_mode = "PAY_PER_REQUEST" # on-demand: no capacity to manage, near-zero cost when idle
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }
  attribute {
    name = "gsi1pk"
    type = "S"
  }
  attribute {
    name = "gsi1sk"
    type = "S"
  }

  # Sparse: only assignments set gsi1pk, for the scheduled sync fan-out
  global_secondary_index {
    name            = "gsi1"
    projection_type = "ALL"
    key_schema {
      attribute_name = "gsi1pk"
      key_type       = "HASH"
    }
    key_schema {
      attribute_name = "gsi1sk"
      key_type       = "RANGE"
    }
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery
  }
}

output "name" {
  value = aws_dynamodb_table.this.name
}

output "arn" {
  value = aws_dynamodb_table.this.arn
}
