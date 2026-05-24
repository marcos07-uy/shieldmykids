# Architecture Overview

## Recommended MVP Architecture

The MVP should use a serverless AWS backend, a static parent dashboard, and polling child agents.

```mermaid
flowchart LR
  Parent[Parent Browser] --> Web[Static Parent Web App]
  Web --> Cognito[Amazon Cognito]
  Web --> Api[API Gateway HTTP API]

  Win[Windows Agent] --> Api
  Android[Android Agent] --> Api

  Api --> Lambda[AWS Lambda API Handlers]
  Lambda --> Ddb[(DynamoDB)]
  Lambda --> Logs[CloudWatch Logs]
  Lambda --> Ses[Amazon SES]
  EventBridge[EventBridge Schedules] --> Lambda

  WebHost[S3 + CloudFront or Amplify Hosting] --> Web
```

## Core Design Choice

Start with HTTPS polling instead of real-time device messaging.

Reasons:

- Lowest complexity.
- Low idle cost.
- Easy for Windows and Android agents.
- Works through common home networks.
- Avoids adding AWS IoT Core until there is a concrete need.

Possible later evolution:

```mermaid
flowchart LR
  Agents[Child Agents] --> IoT[AWS IoT Core MQTT]
  IoT --> Lambda[AWS Lambda]
  Lambda --> Ddb[(DynamoDB)]
  Dashboard[Parent Dashboard] --> Api[API Gateway]
  Api --> Lambda
```

## Logical Components

```mermaid
flowchart TB
  subgraph Parent
    Dashboard[Parent Dashboard]
  end

  subgraph Backend
    Auth[Auth Boundary]
    Family[Family Service]
    Device[Device Service]
    Usage[Usage Ingestion]
    Policy[Policy Engine]
    Commands[Command Queue]
    Audit[Audit Log]
  end

  subgraph Devices
    Windows[Windows Agent]
    Android[Android Agent]
  end

  Dashboard --> Auth
  Auth --> Family
  Family --> Device
  Family --> Usage
  Family --> Policy
  Family --> Audit
  Device --> Commands
  Windows --> Device
  Windows --> Usage
  Windows --> Commands
  Android --> Device
  Android --> Usage
  Android --> Commands
```

## Trust Boundaries

```mermaid
flowchart LR
  subgraph UntrustedHome["Home Network / Child Devices"]
    W[Windows Agent]
    A[Android Agent]
  end

  subgraph PublicInternet["Public Internet"]
    B[Parent Browser]
  end

  subgraph AWS["AWS Account"]
    C[Cognito]
    G[API Gateway]
    L[Lambda]
    D[(DynamoDB)]
    S[S3/CloudFront]
  end

  B --> S
  B --> C
  B --> G
  W --> G
  A --> G
  G --> L
  L --> D
```

Security implication:

- Parent browser and child agents are untrusted clients.
- API Gateway and Lambda must validate every request.
- DynamoDB is not directly exposed.
- Parent identity and device identity are separate trust models.

## Device Enrollment Flow

```mermaid
sequenceDiagram
  actor Parent
  participant Dashboard
  participant API
  participant DB as DynamoDB
  participant Agent

  Parent->>Dashboard: Select child and request pairing code
  Dashboard->>API: Create pairing code
  API->>DB: Store hashed code with expiry and childId
  API-->>Dashboard: Show pairing code
  Parent->>Agent: Enter pairing code
  Agent->>API: Exchange code with device metadata
  API->>DB: Validate code and create device
  API->>DB: Mark code consumed
  API-->>Agent: deviceId, credential, initial policy
  Agent->>API: Start heartbeat and usage sync
```

## Policy Evaluation Flow

```mermaid
sequenceDiagram
  participant Agent
  participant API
  participant Policy as Policy Engine
  participant DB as DynamoDB

  Agent->>API: Send heartbeat and current state
  API->>DB: Load device, child, current policy, usage aggregate
  API->>Policy: Evaluate effective policy
  Policy-->>API: allowed/warned/blocked + commands
  API->>DB: Persist status and queued commands
  API-->>Agent: policy version and pending commands
```

## Usage Aggregation Model

Agents send raw events and interval summaries. The backend stores raw events and computes child-level daily aggregates.

MVP overlap rule:

- Count overlapping usage once per child.
- Preserve per-device totals separately for reporting.

```mermaid
flowchart TB
  Raw[Raw Usage Events] --> Normalize[Normalize Into Intervals]
  Normalize --> Merge[Merge Overlapping Child Intervals]
  Merge --> Daily[Daily Child Aggregate]
  Normalize --> DeviceTotals[Per-Device Totals]
  Normalize --> AppTotals[Per-App Totals]
```

## Availability Assumptions

- Backend availability is best-effort serverless.
- Agents must continue local tracking when offline.
- Agents must cache last known policy.
- Agents must queue events locally.
- Backend must deduplicate usage events.

## Implementation Boundary

This document describes architecture only. It intentionally does not define source files, Terraform resources, or framework-specific code.

