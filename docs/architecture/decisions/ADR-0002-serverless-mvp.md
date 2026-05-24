# ADR-0002: Serverless Polling MVP

## Status

Proposed.

## Context

The project needs the cheapest practical AWS infrastructure for a small initial deployment.

The backend must support:

- Parent dashboard APIs.
- Device enrollment.
- Device heartbeat.
- Usage ingestion.
- Policy evaluation.
- Command queue.

Device commands could be delivered through polling, WebSockets, MQTT, or push-notification systems.

## Decision

Use a serverless polling architecture for the MVP:

- API Gateway HTTP API.
- Lambda.
- DynamoDB.
- Cognito.
- Static web hosting.
- EventBridge scheduled jobs.
- SES for email notifications.

Do not use AWS IoT Core in the MVP unless command latency becomes a practical problem.

## Rationale

Polling is:

- Simple.
- Cheap.
- Easy to debug.
- Compatible with Windows and Android agents.
- Good enough for early family-scale usage.

The MVP does not need second-level command delivery.

## Consequences

Positive:

- Lower complexity.
- Lower idle cost.
- Faster implementation path after Phase 0.

Negative:

- Manual lock/unlock commands are not instant.
- Polling interval must balance latency and request volume.
- Agents need robust retry behavior.

## Future Evolution

AWS IoT Core can later support:

- MQTT command delivery.
- Device shadows.
- Stronger device identity.
- Lower-latency policy updates.

