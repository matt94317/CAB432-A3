# SQS queue + DLQ, fed by an EventBridge Scheduler schedule

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

variable "name" {
  description = "Queue name; the DLQ is <name>-dlq"
  type        = string
}

variable "visibility_timeout_seconds" {
  type    = number
  default = 120
}

variable "receive_wait_time_seconds" {
  type    = number
  default = 20
}

variable "max_receive_count" {
  description = "Receives before a message moves to the DLQ"
  type        = number
  default     = 5
}

variable "schedule_expression" {
  description = "null = no schedule"
  type        = string
  default     = "rate(6 hours)"
}

variable "schedule_message" {
  description = "Message body the schedule sends"
  type        = string
  default     = "{\"type\":\"scheduled_sync\"}"
}

variable "scheduler_role_arn" {
  description = "Role EventBridge Scheduler assumes to send to SQS. null = create one."
  type        = string
  default     = null
}

locals {
  create_schedule = var.schedule_expression != null
  create_role     = local.create_schedule && var.scheduler_role_arn == null
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name}-dlq"
  message_retention_seconds = 1209600 # 14 days, time to inspect failures
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "this" {
  name                       = var.name
  visibility_timeout_seconds = var.visibility_timeout_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
}

# --- Schedule ---

resource "aws_scheduler_schedule_group" "this" {
  count = local.create_schedule ? 1 : 0
  name  = var.name
}

resource "aws_scheduler_schedule" "sync" {
  count = local.create_schedule ? 1 : 0

  name                = "${var.name}-scheduled"
  group_name          = aws_scheduler_schedule_group.this[0].name
  schedule_expression = var.schedule_expression

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.this.arn
    role_arn = local.create_role ? aws_iam_role.scheduler[0].arn : var.scheduler_role_arn
    input    = var.schedule_message
  }
}

# Only when no role is passed in (not allowed in CAB432)
resource "aws_iam_role" "scheduler" {
  count = local.create_role ? 1 : 0
  name  = "${var.name}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  count = local.create_role ? 1 : 0
  role  = aws_iam_role.scheduler[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.this.arn
    }]
  })
}

output "queue_url" {
  value = aws_sqs_queue.this.url
}

output "queue_arn" {
  value = aws_sqs_queue.this.arn
}

output "queue_name" {
  value = aws_sqs_queue.this.name
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "dlq_arn" {
  value = aws_sqs_queue.dlq.arn
}

output "dlq_name" {
  value = aws_sqs_queue.dlq.name
}

output "schedule_arn" {
  value = local.create_schedule ? aws_scheduler_schedule.sync[0].arn : null
}
