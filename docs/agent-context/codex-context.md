# Codex Agent Context

## Project Summary

Shield My Kids is a personal parental-control and family screen-time management system.

It should help parents:

- Monitor screen time per child across multiple devices.
- Understand app and device usage.
- Configure daily limits and schedules.
- Enforce limits where operating systems allow it.
- Register and manage Windows and Android child devices.
- Use a parent web dashboard.

The product must avoid spyware-like behavior and be transparent to the child.

## Current Project Phase

The Phase 0 documentation baseline is complete. The repository has moved into a narrow Phase 1 minimal backend slice.

Current implemented slice:

- Python minimal API Lambda.
- Terraform dev environment.
- Terraform `minimal_backend` module.

Current backend capabilities:

- Create short-lived pairing codes.
- Store or update a child policy.
- Enroll a device by exchanging a pairing code for a device credential.
- Let an enrolled device fetch its current effective policy.

Agents may create or update:

- Documentation and ADRs.
- Existing minimal backend Lambda code.
- Existing minimal backend Terraform.
- Focused local tests for the current backend slice.

Agents must not create without explicit user approval:

- Android source files.
- Windows source files.
- Parent dashboard source files.
- Production infrastructure.
- CI/CD workflow files.
- Package manager manifests.
- Build scripts.

Agents must not deploy infrastructure or mutate AWS resources without explicit user approval.

## Recommended Technical Direction

The current recommended MVP direction is:

- AWS API Gateway HTTP API.
- AWS Lambda.
- Amazon DynamoDB.
- Amazon Cognito.
- Static parent web app hosted with S3/CloudFront or Amplify Hosting.
- Amazon SES for email notifications.
- EventBridge for scheduled aggregation and cleanup jobs.
- Terraform for infrastructure.

Device communication should start with polling because it is simple and cheap. AWS IoT Core can be added later when lower-latency command delivery is needed.

## Platform Direction

Windows MVP:

- Windows service for persistence.
- Visible tray/status app for child transparency and interactive-desktop actions.
- Foreground app tracking.
- Idle detection.
- Local policy cache.
- Local event queue.
- Session lock enforcement.

Android MVP:

- Standard app using Usage Access.
- Enrollment screen.
- Permission guidance.
- Usage reporting.
- Local warnings.
- Limited enforcement.

Later Android enforcement may use Device Owner or Android Management API.

## Security Priorities

- Parent JWT validation on every parent API.
- Device-token validation on every device API.
- Parent ownership checks for all family data.
- Device scoping so devices cannot submit usage for other devices.
- Revocable device credentials.
- Minimal personal data.
- No content capture.
- No covert monitoring.
- Explicit audit logs.

## Architecture Principles

- Keep the MVP small.
- Prefer low idle cost.
- Prefer serverless.
- Keep the backend as source of truth.
- Keep device protocol explicit and versioned.
- Prefer simple DynamoDB access patterns over premature relational modeling.
- Document every major tradeoff in an ADR.

