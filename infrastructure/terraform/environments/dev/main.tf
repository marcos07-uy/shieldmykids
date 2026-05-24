module "minimal_backend" {
  source = "../../modules/minimal_backend"

  project_name                  = var.project_name
  environment                   = var.environment
  lambda_source_dir             = "${path.root}/../../../../backend/lambda/minimal_api"
  dev_parent_token              = var.dev_parent_token
  allowed_cors_origins          = var.allowed_cors_origins
  log_retention_days            = var.log_retention_days
  pairing_code_ttl_seconds      = var.pairing_code_ttl_seconds
  default_sync_interval_seconds = var.default_sync_interval_seconds

  tags = var.tags
}
