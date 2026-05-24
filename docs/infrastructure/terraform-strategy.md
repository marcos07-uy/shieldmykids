# Terraform Strategy

## Current Boundary

The Phase 0 documentation baseline is complete.

The repository now contains a Terraform dev environment and `minimal_backend` module for the first backend slice. This document remains the broader Terraform strategy for future environments and modules.

Do not deploy infrastructure, run `terraform apply`, or mutate AWS resources without explicit user approval.

## Goals

Terraform must provide:

- Repeatable environments.
- Secure defaults.
- Low-cost AWS resources.
- Least-privilege IAM.
- Clear module boundaries.
- No always-on compute for MVP.
- No NAT Gateway for MVP.
- No public database access.
- Cost alarms.

## Recommended Layout

```text
infrastructure/
  terraform/
    environments/
      dev/
      prod/
    modules/
      auth/
      api/
      database/
      hosting/
      notifications/
      observability/
      security_baseline/
```

## Module Pattern

Each module should follow this pattern:

```text
modules/<module-name>/
  main.tf
  variables.tf
  outputs.tf
  versions.tf
  README.md
```

Module rules:

- No hard-coded environment names.
- No hard-coded account IDs.
- Variables must have types.
- Sensitive variables must be marked sensitive.
- Outputs must avoid leaking secrets.
- IAM policies must be scoped to required resources.
- Use tags consistently.

## Environment Pattern

Each environment should compose modules.

```text
environments/dev/
  main.tf
  providers.tf
  backend.tf
  variables.tf
  terraform.tfvars.example
  outputs.tf
```

Environment rules:

- Remote state must be configured.
- State bucket must have encryption and versioning.
- State locking should be enabled.
- Production and development must use separate state.
- Production must not reuse development resources.

## AWS Account Baseline

Before application infrastructure:

- Enable IAM account alias.
- Enforce MFA for human users.
- Use least-privilege deployment role.
- Enable CloudTrail where practical.
- Configure AWS Budgets.
- Configure default encryption where practical.
- Avoid long-lived access keys for automation.

## MVP Modules

### `auth`

Resources:

- Cognito User Pool.
- Cognito App Client.
- Optional hosted UI domain.

Security requirements:

- Strong password policy.
- MFA optional for MVP, recommended for parent accounts.
- Token lifetimes documented.
- No client secret in browser app.

### `api`

Resources:

- API Gateway HTTP API.
- Lambda functions.
- Lambda execution roles.
- Log groups.
- API routes.

Security requirements:

- Parent routes validate Cognito JWTs.
- Device routes validate device credentials in Lambda.
- CORS restricted to known dashboard origins.
- Structured logs without secrets.
- Least-privilege Lambda IAM.

### `database`

Resources:

- DynamoDB tables.

Security requirements:

- Encryption at rest.
- Point-in-time recovery for important tables where cost is acceptable.
- Deletion protection for production.
- Narrow IAM access by table and action.
- TTL for pairing codes, old commands, and temporary records.

### `hosting`

Resources:

- S3 bucket.
- CloudFront distribution or Amplify Hosting.
- TLS certificate if using a custom domain.

Security requirements:

- S3 bucket private.
- CloudFront origin access control.
- HTTPS only.
- Secure response headers where possible.

### `notifications`

Resources:

- SES identities.
- Optional notification templates.

Security requirements:

- Verified sender domain.
- Least-privilege send permissions.
- No sensitive child data in email body.

### `observability`

Resources:

- CloudWatch log groups.
- Metric filters.
- Alarms.
- Dashboard.

Security requirements:

- Log retention set explicitly.
- Avoid indefinite retention for development logs.
- Do not log device credentials or pairing codes.

### `security_baseline`

Resources:

- Budget alerts.
- KMS keys if needed.
- Account-level guardrails where practical.

Security requirements:

- Production resources tagged.
- Destructive changes reviewed.
- Budget alarms enabled before wider testing.

## State Management

Recommended backend:

- S3 remote state.
- DynamoDB state lock table or Terraform-supported locking pattern.
- Server-side encryption.
- Bucket versioning.

State security:

- State bucket private.
- Access limited to deployment role.
- No application secrets stored in plain Terraform variables.

## IAM Strategy

Principles:

- One execution role per Lambda group or function.
- Policies scoped by resource ARN.
- No wildcard admin policies.
- Separate deployment role from runtime roles.
- Avoid IAM users for automation.

Policy examples to avoid:

- `Action: "*"`
- `Resource: "*"` unless an AWS service requires it and the reason is documented.

## Network Strategy

MVP should not place Lambda inside a VPC.

Reasons:

- DynamoDB, Cognito, API Gateway, and SES do not require private VPC access for this MVP.
- Avoids NAT Gateway cost.
- Reduces operational complexity.

Use VPC only if a future dependency requires private networking.

## Secrets Strategy

Avoid static secrets where possible.

If secrets are needed:

- Use AWS Secrets Manager or SSM Parameter Store.
- Do not store raw secrets in Git.
- Do not expose secrets through Terraform outputs.
- Rotate credentials.

Device credentials are application data and should be stored hashed in DynamoDB, not in Terraform.

## Secure Defaults Checklist

- S3 public access blocked.
- CloudFront HTTPS only.
- DynamoDB encryption enabled.
- Production DynamoDB deletion protection considered.
- Lambda logs retained for a defined period.
- CORS restricted.
- Cognito app client has no browser-exposed secret.
- IAM policies least-privilege.
- Pairing code TTL enabled.
- Device command TTL enabled.
- Budget alerts enabled.
- No NAT Gateway in MVP.

