variable "project_name" {
  description = "Project name used for resource names."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "lambda_source_dir" {
  description = "Path to the minimal API Lambda source directory."
  type        = string
}

variable "dev_parent_token" {
  description = "Temporary development token required by parent routes."
  type        = string
  sensitive   = true
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

variable "allowed_cors_origins" {
  description = "Allowed CORS origins for the HTTP API."
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Tags applied to created resources."
  type        = map(string)
  default     = {}
}
