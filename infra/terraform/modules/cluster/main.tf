# ECS cluster and the two task roles: reuse existing ones or create them

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

variable "existing_cluster_name" {
  description = "null = create a cluster"
  type        = string
  default     = null
}

variable "task_role_arn" {
  description = "Role the app code runs as. null = create one."
  type        = string
  default     = null
}

variable "execution_role_arn" {
  description = "Role ECS uses to pull images, write logs and read secrets. null = create one."
  type        = string
  default     = null
}

# Only used when the roles are created here
variable "queue_arns" {
  type    = list(string)
  default = []
}

variable "secret_arns" {
  type    = list(string)
  default = []
}

variable "table_arns" {
  description = "DynamoDB tables the services read and write (only used when creating the task role)"
  type        = list(string)
  default     = []
}

variable "extra_task_policy_arns" {
  description = "Managed policies for the created task role (e.g. DynamoDB access later)"
  type        = list(string)
  default     = []
}

locals {
  create_cluster        = var.existing_cluster_name == null
  create_task_role      = var.task_role_arn == null
  create_execution_role = var.execution_role_arn == null

  ecs_assume_role = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# --- Cluster ---

data "aws_ecs_cluster" "existing" {
  count        = local.create_cluster ? 0 : 1
  cluster_name = var.existing_cluster_name
}

resource "aws_ecs_cluster" "this" {
  count = local.create_cluster ? 1 : 0
  name  = var.name

  setting {
    name  = "containerInsights"
    value = "enhanced" # RunningTaskCount etc. on the dashboard
  }
}

# --- Execution role ---

resource "aws_iam_role" "execution" {
  count              = local.create_execution_role ? 1 : 0
  name               = "${var.name}-execution"
  assume_role_policy = local.ecs_assume_role
}

resource "aws_iam_role_policy_attachment" "execution" {
  count      = local.create_execution_role ? 1 : 0
  role       = aws_iam_role.execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  count = local.create_execution_role && length(var.secret_arns) > 0 ? 1 : 0
  role  = aws_iam_role.execution[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = var.secret_arns
    }]
  })
}

# --- Task role ---

resource "aws_iam_role" "task" {
  count              = local.create_task_role ? 1 : 0
  name               = "${var.name}-task"
  assume_role_policy = local.ecs_assume_role
}

resource "aws_iam_role_policy" "task_sqs" {
  count = local.create_task_role && length(var.queue_arns) > 0 ? 1 : 0
  role  = aws_iam_role.task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes",
      ]
      Resource = var.queue_arns
    }]
  })
}

resource "aws_iam_role_policy" "task_dynamodb" {
  count = local.create_task_role && length(var.table_arns) > 0 ? 1 : 0
  role  = aws_iam_role.task[0].id

  # The repositories only use these four calls (no batch, transaction or scan)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Query"]
      Resource = concat(var.table_arns, [for arn in var.table_arns : "${arn}/index/*"])
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_extra" {
  for_each   = local.create_task_role ? toset(var.extra_task_policy_arns) : toset([])
  role       = aws_iam_role.task[0].name
  policy_arn = each.value
}

output "cluster_name" {
  value = local.create_cluster ? aws_ecs_cluster.this[0].name : data.aws_ecs_cluster.existing[0].cluster_name
}

output "cluster_arn" {
  value = local.create_cluster ? aws_ecs_cluster.this[0].arn : data.aws_ecs_cluster.existing[0].arn
}

output "task_role_arn" {
  value = local.create_task_role ? aws_iam_role.task[0].arn : var.task_role_arn
}

output "execution_role_arn" {
  value = local.create_execution_role ? aws_iam_role.execution[0].arn : var.execution_role_arn
}
