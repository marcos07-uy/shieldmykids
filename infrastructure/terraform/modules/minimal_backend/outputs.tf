output "api_endpoint" {
  description = "HTTP API endpoint."
  value       = aws_apigatewayv2_api.minimal.api_endpoint
}

output "policies_table_name" {
  description = "DynamoDB table storing current child policies."
  value       = aws_dynamodb_table.policies.name
}

output "devices_table_name" {
  description = "DynamoDB table storing enrolled devices."
  value       = aws_dynamodb_table.devices.name
}

output "pairing_codes_table_name" {
  description = "DynamoDB table storing short-lived pairing codes."
  value       = aws_dynamodb_table.pairing_codes.name
}

output "lambda_function_name" {
  description = "Minimal API Lambda function name."
  value       = aws_lambda_function.minimal_api.function_name
}
