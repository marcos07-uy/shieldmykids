variable "aws_region" {
  description = "AWS region for the dev environment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource names."
  type        = string
  default     = "shield-my-kids"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "dev_parent_token" {
  description = "Temporary token required by parent API routes in dev."
  type        = string
  sensitive   = true
}

variable "allowed_cors_origins" {
  description = "Allowed CORS origins for the dev API."
  type        = list(string)
  default     = ["*"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "pairing_code_ttl_seconds" {
  description = "Pairing code lifetime in seconds."
  type        = number
  default     = 900
}

variable "default_sync_interval_seconds" {
  description = "Recommended device sync interval returned by the API."
  type        = number
  default     = 60
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
