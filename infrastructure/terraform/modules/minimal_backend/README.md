# Minimal Backend Module

This module provisions the first backend slice for Shield My Kids:

- DynamoDB table for current child policies.
- DynamoDB table for enrolled devices.
- DynamoDB table for short-lived pairing codes.
- DynamoDB table for raw usage events.
- DynamoDB table for queued device commands.
- Python Lambda implementing minimal parent and device APIs.
- API Gateway HTTP API exposing the Lambda, including pairing, usage summary, manual lock/unlock command queueing, enrollment, heartbeat, usage event ingestion, command polling, command acknowledgement, and policy fetch routes.
- CloudWatch log groups with explicit retention.

## Development Auth Boundary

Parent routes use `X-Dev-Parent-Token`. This is temporary and should be replaced by Cognito JWT authorization before any real user deployment.

Device routes use:

```text
Authorization: Device <token>
X-Device-Id: <deviceId>
```

The Lambda stores SHA-256 hashes of pairing codes and device credentials.
