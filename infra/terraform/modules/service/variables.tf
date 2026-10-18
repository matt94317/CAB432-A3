variable "name" {
  description = "Service, task family, container and log group name"
  type        = string
}

variable "cluster_name" {
  type = string
}

variable "cluster_arn" {
  type = string
}

variable "image" {
  description = "Full image URI including tag"
  type        = string
}

variable "cpu" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "cpu_architecture" {
  description = "ARM64 matches images built on Apple Silicon"
  type        = string
  default     = "ARM64"
}

variable "container_port" {
  description = "null = no port (e.g. the worker)"
  type        = number
  default     = null
}

variable "command" {
  description = "Overrides the image CMD. null = image default."
  type        = list(string)
  default     = null
}

variable "environment" {
  type    = map(string)
  default = {}
}

variable "secrets" {
  description = "Env var name -> Secrets Manager valueFrom (\"<arn>:KEY::\")"
  type        = map(string)
  default     = {}
}

variable "task_role_arn" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "assign_public_ip" {
  type    = bool
  default = false
}

variable "desired_count" {
  description = "Initial count; autoscaling owns it afterwards"
  type        = number
  default     = 1
}

variable "target_group_arn" {
  description = "null = not behind the ALB"
  type        = string
  default     = null
}

variable "health_check_grace_period_seconds" {
  type    = number
  default = 60
}

variable "log_retention_days" {
  type    = number
  default = 14
}

# --- Autoscaling (all optional) ---

variable "autoscaling" {
  description = "null = fixed desired_count"
  type = object({
    min_capacity        = number
    max_capacity        = number
    cpu_target          = optional(number) # ECS average CPU %
    requests_per_target = optional(number) # ALBRequestCountPerTarget
    alb_resource_label  = optional(string) # "<alb suffix>/<tg suffix>", needed with requests_per_target
    scale_in_cooldown   = optional(number, 120)
    scale_out_cooldown  = optional(number, 60)
  })
  default = null
}

variable "queue_scaling" {
  description = "Step scaling on SQS depth (worker-pull pattern). Needs autoscaling set."
  type = object({
    queue_name = string
    # Scale out while messages are waiting: +adjustment tasks per step,
    # lower/upper are message counts above 0
    steps = optional(list(object({
      lower      = number
      upper      = optional(number)
      adjustment = number
      })), [
      { lower = 0, upper = 10, adjustment = 1 },
      { lower = 10, upper = 50, adjustment = 2 },
      { lower = 50, adjustment = 3 },
    ])
    # Scale in to min_capacity after the queue is empty this long
    idle_minutes = optional(number, 5)
  })
  default = null
}
