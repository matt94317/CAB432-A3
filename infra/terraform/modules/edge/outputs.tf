output "alb_arn" {
  value = aws_lb.this.arn
}

output "alb_arn_suffix" {
  value = aws_lb.this.arn_suffix
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "https_listener_arn" {
  value = aws_lb_listener.https.arn
}

# Depends on the listener rules so ECS services are only created once their
# target group is attached to the ALB.
output "target_group_arns" {
  value      = { for k, tg in aws_lb_target_group.this : k => tg.arn }
  depends_on = [aws_lb_listener.https, aws_lb_listener_rule.this]
}

# For ALBRequestCountPerTarget scaling: "<alb suffix>/<tg suffix>"
output "resource_labels" {
  value = { for k, tg in aws_lb_target_group.this : k => "${aws_lb.this.arn_suffix}/${tg.arn_suffix}" }
}

output "target_group_arn_suffixes" {
  value = { for k, tg in aws_lb_target_group.this : k => tg.arn_suffix }
}

output "cloudfront_domain_name" {
  value = var.enable_cloudfront ? aws_cloudfront_distribution.this[0].domain_name : null
}

output "cloudfront_arn" {
  value = var.enable_cloudfront ? aws_cloudfront_distribution.this[0].arn : null
}

output "cloudfront_id" {
  value = var.enable_cloudfront ? aws_cloudfront_distribution.this[0].id : null
}

output "app_url" {
  value = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.this[0].domain_name}" : "https://${var.domain_name}"
}

output "domain_url" {
  value = "https://${var.domain_name}"
}

output "dns_record_fqdn" {
  description = "Route 53 alias record pointing the domain at the ALB (null without a zone)"
  value       = one(aws_route53_record.alb[*].fqdn)
}
