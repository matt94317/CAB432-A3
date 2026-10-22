# Application Auto Scaling for the service:
# - target tracking on CPU and/or ALB requests per task (API)
# - step scaling on SQS queue depth (worker), including scale to zero

locals {
  scaling  = var.autoscaling != null
  cpu      = local.scaling && try(var.autoscaling.cpu_target, null) != null
  requests = local.scaling && try(var.autoscaling.requests_per_target, null) != null
  queue    = local.scaling && var.queue_scaling != null
}

resource "aws_appautoscaling_target" "this" {
  count = local.scaling ? 1 : 0

  service_namespace  = "ecs"
  scalable_dimension = "ecs:service:DesiredCount"
  resource_id        = "service/${var.cluster_name}/${aws_ecs_service.this.name}"
  min_capacity       = var.autoscaling.min_capacity
  max_capacity       = var.autoscaling.max_capacity
}

resource "aws_appautoscaling_policy" "cpu" {
  count = local.cpu ? 1 : 0

  name               = "${var.name}-cpu"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  resource_id        = aws_appautoscaling_target.this[0].resource_id

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling.cpu_target
    scale_in_cooldown  = var.autoscaling.scale_in_cooldown
    scale_out_cooldown = var.autoscaling.scale_out_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

resource "aws_appautoscaling_policy" "requests" {
  count = local.requests ? 1 : 0

  name               = "${var.name}-requests"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  resource_id        = aws_appautoscaling_target.this[0].resource_id

  target_tracking_scaling_policy_configuration {
    target_value       = var.autoscaling.requests_per_target
    scale_in_cooldown  = var.autoscaling.scale_in_cooldown
    scale_out_cooldown = var.autoscaling.scale_out_cooldown

    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = var.autoscaling.alb_resource_label
    }
  }
}

# --- Queue depth ---

resource "aws_appautoscaling_policy" "queue_out" {
  count = local.queue ? 1 : 0

  name               = "${var.name}-queue-out"
  policy_type        = "StepScaling"
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  resource_id        = aws_appautoscaling_target.this[0].resource_id

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = var.autoscaling.scale_out_cooldown
    metric_aggregation_type = "Maximum"

    dynamic "step_adjustment" {
      for_each = var.queue_scaling.steps
      content {
        metric_interval_lower_bound = step_adjustment.value.lower
        metric_interval_upper_bound = step_adjustment.value.upper
        scaling_adjustment          = step_adjustment.value.adjustment
      }
    }
  }
}

resource "aws_appautoscaling_policy" "queue_in" {
  count = local.queue ? 1 : 0

  name               = "${var.name}-queue-in"
  policy_type        = "StepScaling"
  service_namespace  = aws_appautoscaling_target.this[0].service_namespace
  scalable_dimension = aws_appautoscaling_target.this[0].scalable_dimension
  resource_id        = aws_appautoscaling_target.this[0].resource_id

  step_scaling_policy_configuration {
    adjustment_type         = "ExactCapacity"
    cooldown                = var.autoscaling.scale_in_cooldown
    metric_aggregation_type = "Maximum"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = var.autoscaling.min_capacity
    }
  }
}

# Messages waiting -> add workers
resource "aws_cloudwatch_metric_alarm" "queue_backlog" {
  count = local.queue ? 1 : 0

  alarm_name          = "${var.name}-queue-backlog"
  alarm_description   = "Messages waiting on ${var.queue_scaling.queue_name}: scale workers out"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = var.queue_scaling.queue_name }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_appautoscaling_policy.queue_out[0].arn]
}

# Nothing waiting or in flight for idle_minutes -> back to min (0)
resource "aws_cloudwatch_metric_alarm" "queue_idle" {
  count = local.queue ? 1 : 0

  alarm_name          = "${var.name}-queue-idle"
  alarm_description   = "${var.queue_scaling.queue_name} empty: scale workers in"
  evaluation_periods  = var.queue_scaling.idle_minutes
  threshold           = 0.5
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching" # SQS stops reporting when a queue is idle
  alarm_actions       = [aws_appautoscaling_policy.queue_in[0].arn]

  metric_query {
    id          = "total"
    expression  = "visible + inflight"
    label       = "Visible + in flight"
    return_data = true
  }

  metric_query {
    id = "visible"
    metric {
      namespace   = "AWS/SQS"
      metric_name = "ApproximateNumberOfMessagesVisible"
      dimensions  = { QueueName = var.queue_scaling.queue_name }
      stat        = "Maximum"
      period      = 60
    }
  }

  metric_query {
    id = "inflight"
    metric {
      namespace   = "AWS/SQS"
      metric_name = "ApproximateNumberOfMessagesNotVisible"
      dimensions  = { QueueName = var.queue_scaling.queue_name }
      stat        = "Maximum"
      period      = 60
    }
  }
}
