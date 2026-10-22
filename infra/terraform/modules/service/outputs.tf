output "service_name" {
  value = aws_ecs_service.this.name
}

output "service_arn" {
  value = aws_ecs_service.this.id
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.this.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.this.arn
}

output "autoscaling_target_id" {
  value = local.scaling ? aws_appautoscaling_target.this[0].id : null
}

output "scaling_alarm_arns" {
  description = "Queue-depth alarms that drive step scaling (empty for services without a queue)"
  value       = concat(aws_cloudwatch_metric_alarm.queue_backlog[*].arn, aws_cloudwatch_metric_alarm.queue_idle[*].arn)
}
