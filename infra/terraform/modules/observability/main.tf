# CloudWatch dashboard + alarms

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

variable "alb_arn_suffix" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "service_names" {
  description = "Short label -> ECS service name"
  type        = map(string)
}

variable "queue_name" {
  type = string
}

variable "dlq_name" {
  type = string
}

variable "cache_cluster_ids" {
  description = "ElastiCache node ids"
  type        = list(string)
}

variable "alb_5xx_threshold" {
  description = "5xx responses (ALB + targets) per 5 minutes before alarming"
  type        = number
  default     = 5
}

variable "alarm_actions" {
  description = "e.g. an SNS topic ARN. Empty = alarm shows in the console only."
  type        = list(string)
  default     = []
}

data "aws_region" "current" {}

locals {
  region = data.aws_region.current.region
  alb    = ["LoadBalancer", var.alb_arn_suffix]

  widget_defaults = {
    region = local.region
    view   = "timeSeries"
    period = 60
  }

  widgets = [
    {
      title   = "ALB requests"
      stat    = "Sum"
      metrics = [concat(["AWS/ApplicationELB", "RequestCount"], local.alb)]
    },
    {
      title = "ALB latency (s)"
      metrics = [
        concat(["AWS/ApplicationELB", "TargetResponseTime"], local.alb, [{ stat = "p95", label = "p95" }]),
        concat(["AWS/ApplicationELB", "TargetResponseTime"], local.alb, [{ stat = "Average", label = "avg" }]),
      ]
    },
    {
      title = "ALB 5xx"
      stat  = "Sum"
      metrics = [
        concat(["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count"], local.alb),
        concat(["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count"], local.alb),
      ]
    },
    {
      title   = "ECS CPU % per service"
      stat    = "Average"
      metrics = [for label, svc in var.service_names : ["AWS/ECS", "CPUUtilization", "ClusterName", var.cluster_name, "ServiceName", svc, { label = label }]]
    },
    {
      # Needs Container Insights on the cluster
      title   = "Running tasks"
      stat    = "Average"
      metrics = [for label, svc in var.service_names : ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", var.cluster_name, "ServiceName", svc, { label = label }]]
    },
    {
      title = "Sync queue"
      stat  = "Maximum"
      metrics = [
        ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.queue_name, { label = "visible" }],
        ["AWS/SQS", "ApproximateNumberOfMessagesNotVisible", "QueueName", var.queue_name, { label = "in flight" }],
        ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", var.queue_name, { label = "oldest (s)", yAxis = "right" }],
      ]
    },
    {
      title   = "Dead-letter queue"
      stat    = "Maximum"
      metrics = [["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.dlq_name]]
    },
    {
      title   = "Cache CPU %"
      stat    = "Average"
      metrics = [for id in var.cache_cluster_ids : ["AWS/ElastiCache", "EngineCPUUtilization", "CacheClusterId", id]]
    },
    {
      title = "Cache hits / misses"
      stat  = "Sum"
      # concat(...) joins one level; flatten would collapse the rows into one list of strings
      metrics = concat([for id in var.cache_cluster_ids : [
        ["AWS/ElastiCache", "CacheHits", "CacheClusterId", id],
        ["AWS/ElastiCache", "CacheMisses", "CacheClusterId", id],
      ]]...)
    },
  ]
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.name

  # 3 widgets per row, 8 wide x 6 high
  dashboard_body = jsonencode({
    widgets = [for i, w in local.widgets : {
      type       = "metric"
      x          = (i % 3) * 8
      y          = floor(i / 3) * 6
      width      = 8
      height     = 6
      properties = merge(local.widget_defaults, w)
    }]
  })
}

resource "aws_cloudwatch_metric_alarm" "dlq" {
  alarm_name          = "${var.name}-dlq-not-empty"
  alarm_description   = "Sync jobs failed and landed in ${var.dlq_name}"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = var.dlq_name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_actions
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.name}-alb-5xx"
  alarm_description   = "ALB or targets returned more than ${var.alb_5xx_threshold} 5xx in 5 minutes"
  evaluation_periods  = 1
  threshold           = var.alb_5xx_threshold
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_actions

  metric_query {
    id          = "total"
    expression  = "FILL(elb, 0) + FILL(target, 0)"
    label       = "5xx"
    return_data = true
  }

  metric_query {
    id = "elb"
    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "HTTPCode_ELB_5XX_Count"
      dimensions  = { LoadBalancer = var.alb_arn_suffix }
      stat        = "Sum"
      period      = 300
    }
  }

  metric_query {
    id = "target"
    metric {
      namespace   = "AWS/ApplicationELB"
      metric_name = "HTTPCode_Target_5XX_Count"
      dimensions  = { LoadBalancer = var.alb_arn_suffix }
      stat        = "Sum"
      period      = 300
    }
  }
}

output "dashboard_arn" {
  value = aws_cloudwatch_dashboard.this.dashboard_arn
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.this.dashboard_name
}

output "alarm_arns" {
  value = {
    dlq     = aws_cloudwatch_metric_alarm.dlq.arn
    alb_5xx = aws_cloudwatch_metric_alarm.alb_5xx.arn
  }
}
