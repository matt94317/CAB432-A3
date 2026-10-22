# ALB (HTTPS, path routing) + Route 53 alias + optional CloudFront in front

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

locals {
  routed = { for k, s in var.services : k => s if length(s.paths) > 0 }
}

resource "aws_lb" "this" {
  name               = var.name
  load_balancer_type = "application"
  internal           = false
  subnets            = var.subnet_ids
  security_groups    = var.security_group_ids

  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "this" {
  for_each = var.services

  name        = "${var.name}-${each.key}"
  vpc_id      = var.vpc_id
  port        = each.value.port
  protocol    = "HTTP"
  target_type = "ip" # Fargate awsvpc

  deregistration_delay = 30

  health_check {
    path                = each.value.health_path
    matcher             = each.value.health_matcher
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[var.default_service].arn
  }
}

resource "aws_lb_listener_rule" "this" {
  for_each = local.routed

  listener_arn = aws_lb_listener.https.arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[each.key].arn
  }

  condition {
    path_pattern {
      values = each.value.paths
    }
  }
}

# --- DNS ---

data "aws_route53_zone" "this" {
  count        = var.zone_name == null ? 0 : 1
  name         = var.zone_name
  private_zone = false
}

resource "aws_route53_record" "alb" {
  count = var.zone_name == null ? 0 : 1

  zone_id         = data.aws_route53_zone.this[0].zone_id
  name            = var.domain_name
  type            = "A"
  allow_overwrite = var.dns_allow_overwrite

  alias {
    name                   = aws_lb.this.dns_name
    zone_id                = aws_lb.this.zone_id
    evaluate_target_health = true
  }
}
