# Cognito: reuse an existing user pool or create one, plus a public app client

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

variable "existing_user_pool_id" {
  description = "null = create a pool"
  type        = string
  default     = null
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  create_pool  = var.existing_user_pool_id == null
  user_pool_id = local.create_pool ? aws_cognito_user_pool.this[0].id : var.existing_user_pool_id
}

# Same settings as the CLI example in infra/README.md
resource "aws_cognito_user_pool" "this" {
  count = local.create_pool ? 1 : 0
  name  = var.name

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.name}-web"
  user_pool_id = local.user_pool_id

  generate_secret               = false
  explicit_auth_flows           = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  enable_token_revocation       = true
  prevent_user_existence_errors = "ENABLED"

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  read_attributes  = ["email", "name"]
  write_attributes = ["email", "name"]
}

output "user_pool_id" {
  value = local.user_pool_id
}

output "user_pool_arn" {
  value = "arn:aws:cognito-idp:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:userpool/${local.user_pool_id}"
}

output "client_id" {
  value = aws_cognito_user_pool_client.web.id
}
