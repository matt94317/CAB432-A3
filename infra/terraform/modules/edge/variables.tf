variable "name" {
  description = "ALB name (max 32 chars); target groups are <name>-<service>"
  type        = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  description = "Public subnets for the ALB"
  type        = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "certificate_arn" {
  description = "ACM cert (same region as the ALB) for domain_name"
  type        = string
}

variable "domain_name" {
  description = "Custom domain pointing at the ALB, e.g. n12191434.cab432.com"
  type        = string
}

variable "zone_name" {
  description = "Public Route 53 zone for domain_name. null = manage DNS elsewhere."
  type        = string
  default     = null
}

variable "dns_allow_overwrite" {
  description = "Take over an existing record with the same name"
  type        = bool
  default     = false
}

variable "services" {
  description = "Target group per service. Empty paths = the listener's default action."
  type = map(object({
    port           = optional(number, 8080)
    health_path    = string
    health_matcher = optional(string, "200")
    paths          = optional(list(string), [])
    priority       = optional(number, 100)
  }))
}

variable "default_service" {
  description = "Service that gets requests no rule matches"
  type        = string
}

variable "enable_cloudfront" {
  type    = bool
  default = true
}

variable "cloudfront_price_class" {
  description = "PriceClass_All is the only class with Australian edges"
  type        = string
  default     = "PriceClass_All"
}

variable "cloudfront_uncached_paths" {
  description = "Path patterns passed straight through to the ALB (no caching, all methods)"
  type        = list(string)
  default     = ["/api/*", "/mcp*"]
}
