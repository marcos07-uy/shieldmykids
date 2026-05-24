output "api_endpoint" {
  description = "Dev HTTP API endpoint."
  value       = module.minimal_backend.api_endpoint
}

output "policies_table_name" {
  description = "Dev policies table name."
  value       = module.minimal_backend.policies_table_name
}

output "devices_table_name" {
  description = "Dev devices table name."
  value       = module.minimal_backend.devices_table_name
}

output "pairing_codes_table_name" {
  description = "Dev pairing codes table name."
  value       = module.minimal_backend.pairing_codes_table_name
}

output "lambda_function_name" {
  description = "Dev minimal API Lambda function name."
  value       = module.minimal_backend.lambda_function_name
}
