locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  )
}

data "archive_file" "minimal_api" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.root}/${local.name_prefix}-minimal-api.zip"
}

resource "aws_dynamodb_table" "policies" {
  name         = "${local.name_prefix}-policies"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "childId"

  attribute {
    name = "childId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "devices" {
  name         = "${local.name_prefix}-devices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "deviceId"

  attribute {
    name = "deviceId"
    type = "S"
  }

  attribute {
    name = "childId"
    type = "S"
  }

  global_secondary_index {
    name            = "childId-index"
    hash_key        = "childId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "pairing_codes" {
  name         = "${local.name_prefix}-pairing-codes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "codeHash"

  attribute {
    name = "codeHash"
    type = "S"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "usage_events" {
  name         = "${local.name_prefix}-usage-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "deviceEventId"

  attribute {
    name = "deviceEventId"
    type = "S"
  }

  attribute {
    name = "childId"
    type = "S"
  }

  global_secondary_index {
    name            = "childId-index"
    hash_key        = "childId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "device_commands" {
  name         = "${local.name_prefix}-device-commands"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "commandId"

  attribute {
    name = "commandId"
    type = "S"
  }

  attribute {
    name = "deviceId"
    type = "S"
  }

  global_secondary_index {
    name            = "deviceId-index"
    hash_key        = "deviceId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "audit_events" {
  name         = "${local.name_prefix}-audit-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "auditId"

  attribute {
    name = "auditId"
    type = "S"
  }

  attribute {
    name = "familyId"
    type = "S"
  }

  global_secondary_index {
    name            = "familyId-index"
    hash_key        = "familyId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_iam_role" "minimal_api_lambda" {
  name = "${local.name_prefix}-minimal-api-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "minimal_api" {
  name              = "/aws/lambda/${local.name_prefix}-minimal-api"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_iam_role_policy" "minimal_api_lambda" {
  name = "${local.name_prefix}-minimal-api-lambda"
  role = aws_iam_role.minimal_api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "WriteLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.minimal_api.arn}:*"
      },
      {
        Sid    = "UseMinimalBackendTables"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.policies.arn,
          aws_dynamodb_table.devices.arn,
          aws_dynamodb_table.pairing_codes.arn,
          aws_dynamodb_table.usage_events.arn,
          "${aws_dynamodb_table.usage_events.arn}/index/*",
          aws_dynamodb_table.device_commands.arn,
          "${aws_dynamodb_table.device_commands.arn}/index/*",
          aws_dynamodb_table.audit_events.arn,
          "${aws_dynamodb_table.audit_events.arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "minimal_api" {
  function_name    = "${local.name_prefix}-minimal-api"
  role             = aws_iam_role.minimal_api_lambda.arn
  handler          = "app.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.minimal_api.output_path
  source_code_hash = data.archive_file.minimal_api.output_base64sha256
  timeout          = 10
  memory_size      = 256

  environment {
    variables = {
      POLICIES_TABLE_NAME           = aws_dynamodb_table.policies.name
      DEVICES_TABLE_NAME            = aws_dynamodb_table.devices.name
      PAIRING_CODES_TABLE_NAME      = aws_dynamodb_table.pairing_codes.name
      USAGE_EVENTS_TABLE_NAME       = aws_dynamodb_table.usage_events.name
      DEVICE_COMMANDS_TABLE_NAME    = aws_dynamodb_table.device_commands.name
      AUDIT_EVENTS_TABLE_NAME       = aws_dynamodb_table.audit_events.name
      DEV_PARENT_TOKEN              = var.dev_parent_token
      PAIRING_CODE_TTL_SECONDS      = tostring(var.pairing_code_ttl_seconds)
      DEFAULT_SYNC_INTERVAL_SECONDS = tostring(var.default_sync_interval_seconds)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.minimal_api,
    aws_iam_role_policy.minimal_api_lambda
  ]

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "minimal" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = [
      "Authorization",
      "Content-Type",
      "X-Device-Id",
      "X-Dev-Parent-Token"
    ]
    allow_methods = ["GET", "POST", "PUT", "OPTIONS"]
    allow_origins = var.allowed_cors_origins
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "minimal_api" {
  api_id                 = aws_apigatewayv2_api.minimal.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.minimal_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_pairing_code" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "put_policy" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "PUT /v1/parent/families/{familyId}/children/{childId}/policy"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "get_usage_summary" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "GET /v1/parent/families/{familyId}/children/{childId}/usage"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "list_audit_events" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "GET /v1/parent/families/{familyId}/audit-events"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "lock_device" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/parent/families/{familyId}/devices/{deviceId}/lock"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "unlock_device" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/parent/families/{familyId}/devices/{deviceId}/unlock"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "enroll_device" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/device/enroll"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "device_heartbeat" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/device/heartbeat"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "submit_usage_events" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/device/usage-events"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "get_device_commands" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "GET /v1/device/commands"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "ack_device_command" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "POST /v1/device/commands/{commandId}/ack"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_apigatewayv2_route" "get_device_policy" {
  api_id    = aws_apigatewayv2_api.minimal.id
  route_key = "GET /v1/device/policy"
  target    = "integrations/${aws_apigatewayv2_integration.minimal_api.id}"
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${local.name_prefix}-api"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.minimal.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "allow_http_api" {
  statement_id  = "AllowExecutionFromHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.minimal_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.minimal.execution_arn}/*/*"
}
