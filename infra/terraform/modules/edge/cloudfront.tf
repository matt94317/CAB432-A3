# CloudFront in front of the ALB: caches the SPA at the edge,
# passes /api and /mcp straight through.

locals {
  # AWS managed policy ids (global, fixed)
  caching_optimized             = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  caching_disabled              = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  all_viewer_except_host_header = "b689b0a8-53d0-40ab-baf2-68738e2966ac"

  origin_id = "alb"
}

resource "aws_cloudfront_distribution" "this" {
  count = var.enable_cloudfront ? 1 : 0

  enabled             = true
  comment             = var.name
  price_class         = var.cloudfront_price_class
  http_version        = "http2and3"
  is_ipv6_enabled     = true
  wait_for_deployment = false

  # Origin is the custom domain so the ALB's ACM cert matches
  origin {
    origin_id   = local.origin_id
    domain_name = var.domain_name

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      # The assistant's /mcp/chat can take several model calls; 60 s is the max
      # without a quota increase (and the ALB's idle timeout)
      origin_read_timeout = 60
    }
  }

  # SPA (web service)
  default_cache_behavior {
    target_origin_id       = local.origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = local.caching_optimized
  }

  # API and MCP: no caching, all methods, all headers (incl. Authorization)
  dynamic "ordered_cache_behavior" {
    for_each = var.cloudfront_uncached_paths
    content {
      path_pattern             = ordered_cache_behavior.value
      target_origin_id         = local.origin_id
      viewer_protocol_policy   = "redirect-to-https"
      allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      cached_methods           = ["GET", "HEAD"]
      compress                 = true
      cache_policy_id          = local.caching_disabled
      origin_request_policy_id = local.all_viewer_except_host_header
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
