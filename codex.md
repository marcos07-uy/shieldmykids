# Shield My Kids — Functional Strategy & Planning Specification for Codex CLI

## Purpose

This document is a **planning and functionality-first specification** for restarting the **Shield My Kids** personal project.

The goal is not to prescribe the implementation in detail. The goal is to give Codex CLI enough product context to analyze the problem, compare implementation strategies, and propose the best technical approach.

Codex should first produce a strategy and option comparison before generating production code.

---

## Project Vision

Shield My Kids is a parental-control and family screen-time management system that helps parents that helps parents understand kids behavior and digital devices usage, not just cold statistics:

- Monitor child device usage across multiple devices.
- Track total screen time per child, not only per device.
- Enforce limits when the child reaches allowed usage.
- Manage schedules, blocked apps, allowed apps, and device rules.
- Support at minimum:
  - Windows devices.
  - Android devices.
  - Parent web dashboard.
  - Backend/API.
  - Cheapest possible AWS infrastructure, preferably serverless.

The system should be designed as a complete product, but implemented incrementally.

---

## Primary Goal for Codex

Codex must prepare a **technical strategy first**, then implement only after the user chooses the preferred option.

Codex should produce:

1. A comparison of feasible architecture options.
2. A recommended MVP approach.
3. A phased delivery plan.
4. A clear breakdown of components.
5. Functional requirements for each component.
6. Key technical risks and limitations.
7. Cost-aware AWS infrastructure strategy.
8. A proposed repository structure.
9. A prioritized implementation backlog.

Codex should not immediately start coding the entire system.

---

## Product Scope

### Included in the full product

The complete project should include:

- Parent web application.
- Backend API.
- Authentication.
- Parent account management.
- Child profile management.
- Device registration.
- Windows child agent.
- Android child agent.
- Screen-time tracking.
- Usage aggregation across multiple devices.
- Daily and weekly limits.
- Schedule-based rules.
- App-level monitoring.
- App-level restrictions where technically feasible.
- Device lock/block behavior.
- Parent dashboard.
- Audit logs.
- Basic notifications.
- Infrastructure as Code for AWS.
- CI/CD pipeline.
- Security-first design.

### Out of scope for the first MVP unless Codex recommends otherwise

The first MVP should not try to implement everything at once.

The following can be deferred:

- iOS support.
- macOS support.
- Advanced AI recommendations.
- Payment/subscription system.
- Public app store deployment.
- Enterprise multi-family tenancy.
- Real-time chat with child.
- Location tracking.
- Browser history capture.
- Screenshot capture.
- Keystroke logging.
- Any invasive surveillance feature.

---

## Important Ethical and Safety Constraints

This project is for parental control of devices owned or managed by the parent/guardian.

The system must avoid spyware-like behavior.

The product should be transparent:

- The child device should clearly show that monitoring is enabled.
- The agent should identify itself.
- The parent should not be able to silently install hidden surveillance.
- No keylogging.
- No covert microphone/camera access.
- No stealth screenshots.
- No credential theft.
- No bypassing operating system security boundaries.

Codex must design this as a legitimate parental-control product, not as malware or covert monitoring software.

---

## Functional Requirements

## 1. Parent Web Dashboard

The parent dashboard should allow parents to:

- Create an account.
- Log in securely.
- Create child profiles.
- Register devices to child profiles.
- View today’s usage per child.
- View usage by device.
- View usage by app/category if available.
- Configure daily screen-time limits.
- Configure schedules.
- Configure blocked apps or app groups.
- Configure allowed apps.
- Trigger a manual lock/block action.
- Trigger an unlock action.
- View enforcement status.
- View device last-seen status.
- View audit events.

### Dashboard Views

Required screens:

1. Login / signup.
2. Family overview.
3. Child profile detail.
4. Device detail.
5. Rule editor.
6. Usage report.
7. Audit log.
8. Device pairing screen.

---

## 2. Backend API

The backend should provide core business functionality:

- Authentication integration.
- Parent account management.
- Child profile management.
- Device registration.
- Device heartbeat ingestion.
- Usage event ingestion.
- Rule storage.
- Policy evaluation.
- Aggregated usage calculation.
- Device command generation.
- Command acknowledgement tracking.
- Audit logging.
- Notification hooks.

### Backend responsibilities

The backend is responsible for determining:

- How much time each child has used today.
- Whether a child has exceeded a limit.
- Which rules apply to a device.
- Whether a device should be locked, restricted, or allowed.
- Which commands must be sent to agents.
- What status should be shown in the dashboard.

The backend should be treated as the source of truth.

---

## 3. Child Profiles

A child profile represents a real child and can have multiple devices.

Each child profile should include:

- Child ID.
- Parent account ID.
- Display name.
- Optional age range.
- Time zone.
- Daily screen-time limit.
- Weekly limits if implemented.
- Schedule rules.
- Linked devices.
- Current usage summary.
- Current enforcement status.

---

## 4. Device Registration

A device represents an enrolled Windows or Android device.

Each device should include:

- Device ID.
- Child ID.
- Platform: Windows or Android.
- Device name.
- Agent version.
- Last seen timestamp.
- Enrollment status.
- Public device metadata.
- Policy version.
- Current policy state.
- Current enforcement state.

### Pairing Flow

The dashboard should generate a pairing code.

The child agent should allow the parent to enter the pairing code during setup.

After pairing:

- The agent receives a device identity.
- The backend associates the device with a child profile.
- The device starts reporting usage.
- The device starts receiving policy.

---

## 5. Screen-Time Tracking

The system should track child device usage.

### Minimum tracking model

For MVP:

- Track active usage time.
- Track idle time separately if possible.
- Track foreground application on Windows.
- Track app usage on Android if available through approved APIs.
- Report usage periodically to backend.
- Aggregate usage by child across all devices.

### Required reporting events

Agents should send:

- Device heartbeat.
- Session started.
- Session ended.
- Foreground app changed.
- Usage interval summary.
- Policy applied.
- Lock state changed.
- Error/diagnostic event.

### Aggregation behavior

The backend should consolidate usage across all devices for the same child.

If two devices are active at the same time, Codex should propose a strategy.

Possible strategies:

1. Count overlapping usage once per child.
2. Count usage per device independently.
3. Count the maximum active usage among overlapping intervals.
4. Make overlap behavior configurable.

Codex should recommend the best MVP approach.

---

## 6. Rules and Policies

The product should support rules such as:

- Daily screen-time limit.
- Allowed usage schedule.
- Bedtime schedule.
- App blocklist.
- App allowlist.
- Temporary bonus time.
- Manual lock.
- Manual unlock.
- Grace period before lock.
- Emergency override.

### Example rules

- Child can use devices from 07:00 to 21:00.
- Child has 2 hours of total screen time per day.
- Educational apps are always allowed.
- Games are blocked after daily time is consumed.
- Parent can grant 30 minutes of bonus time.

---

## 7. Enforcement

Enforcement differs by platform.

Codex must evaluate the best approach for each platform.

## Windows enforcement

The Windows agent should support, where feasible:

- Monitoring active foreground application.
- Reporting usage to backend.
- Receiving policy updates.
- Showing local status to the child.
- Warning before time expires.
- Locking the child session.
- Blocking or closing restricted applications.
- Preventing app launch where feasible.
- Applying local fallback policy if offline.
- Running as a background service or scheduled process.
- Starting automatically after reboot.

Codex should compare Windows enforcement options:

### Option W1 — User-mode agent only

Pros:

- Easier to build.
- Lower risk.
- Faster MVP.
- No driver required.

Cons:

- Weaker enforcement.
- Easier for local admin users to bypass.
- App blocking may be limited.

### Option W2 — Windows service with admin install

Pros:

- Better persistence.
- Better local enforcement.
- Can monitor and act even when dashboard app is closed.

Cons:

- Requires installer.
- Requires admin permissions.
- More complex.

### Option W3 — Windows service plus OS-level policies

Pros:

- Stronger restrictions.
- Can use Windows-native controls where available.

Cons:

- More complex.
- May depend on Windows edition and user account type.

Codex should recommend the best Windows MVP approach.

---

## 8. Android Enforcement

Android is more restricted than Windows.

Codex must analyze realistic Android options before implementation.

### Android option A1 — Standard Android app using Usage Access

Possible capabilities:

- App usage visibility with user-granted permission.
- Foreground app detection depending on Android version and permission.
- Local notifications.
- Basic local warnings.
- Reporting usage to backend.

Limitations:

- Enforcement may be weak.
- Child may revoke permissions.
- App blocking may be limited.
- Strong restrictions are hard without device owner privileges.

### Android option A2 — Device Owner / Android Enterprise style app

Possible capabilities:

- Stronger device policy control.
- Better app restrictions.
- Better enforcement.
- More suitable for managed child devices.

Limitations:

- Enrollment is more complex.
- May require factory reset or special provisioning.
- Harder for casual consumer setup.
- More friction for parents.

### Android option A3 — Use Android Management API

Possible capabilities:

- Cloud-managed policies.
- Mature Android Enterprise management model.
- Strong device-level restrictions.

Limitations:

- More complex architecture.
- May not fit all personal/family use cases.
- Requires understanding Android Enterprise enrollment model.
- Some functionality may depend on managed Google Play / enterprise setup.

Codex should compare these options and recommend the best MVP strategy.

---

## 9. Notifications

The product should support notifications such as:

- Child is near daily limit.
- Child reached daily limit.
- Device has been offline for too long.
- New device paired.
- Policy failed to apply.
- Manual lock/unlock action completed.
- Child requested more time.

For MVP, email notifications or dashboard notifications are enough.

Push notifications can be deferred.

---

## 10. Parent Approval / Bonus Time

The system should eventually support:

- Child requests more time.
- Parent receives request.
- Parent approves or denies.
- Approved bonus time is applied immediately or at next sync.
- Audit entry is recorded.

For MVP, bonus time can be applied manually in the dashboard.

---

## 11. Offline Behavior

Agents must handle temporary backend unavailability.

Required offline behavior:

- Cache last known policy.
- Continue local tracking.
- Continue local enforcement if policy says the child is blocked.
- Queue usage events locally.
- Sync queued events when online.
- Avoid data loss.
- Avoid duplicate usage counting.

Codex should propose the simplest reliable offline sync model.

---

## 12. Security Requirements

The system must be secure by design.

### Authentication and authorization

- Parents must authenticate.
- Parent can only access their own family data.
- Agents authenticate as registered devices.
- Device tokens must be revocable.
- APIs must validate ownership.
- Admin APIs must not be exposed publicly without authorization.

### Data protection

- Store minimal personal data.
- Encrypt sensitive data at rest where possible.
- Use TLS for all communication.
- Do not store child passwords.
- Do not capture private message contents.
- Do not capture keystrokes.
- Do not capture screenshots.

### Device identity

Each device should have:

- A unique device ID.
- A device credential.
- Token rotation strategy.
- Revocation flow.

---

## 13. AWS Infrastructure Requirement

Infrastructure must be the cheapest practical AWS option.

Prefer serverless.

Codex should compare at least these AWS options:

## Option AWS-1 — Simple serverless API

Possible services:

- Amazon Cognito for parent authentication.
- Amazon API Gateway HTTP API.
- AWS Lambda for backend functions.
- Amazon DynamoDB for data.
- Amazon S3 for static web hosting or Amplify Hosting.
- Amazon CloudWatch Logs.
- Amazon EventBridge for scheduled jobs.
- Amazon SES for email notifications.

Pros:

- Very low idle cost.
- Mostly pay-per-use.
- Good for MVP.
- Simple operational model.

Cons:

- Real-time device communication is limited.
- Agents may need polling.
- API Gateway and Lambda design must be clean.

## Option AWS-2 — Serverless with AWS IoT Core for devices

Possible services:

- Cognito.
- API Gateway.
- Lambda.
- DynamoDB.
- AWS IoT Core MQTT.
- IoT Device Shadows or custom topics.
- S3/Amplify for dashboard.

Pros:

- Better device messaging.
- MQTT fits agents well.
- More real-time command delivery.
- Device identity model is strong.

Cons:

- More AWS complexity.
- Cost is still low at small scale but harder to estimate.
- More concepts to learn.

## Option AWS-3 — AppSync / GraphQL serverless

Possible services:

- Cognito.
- AWS AppSync.
- DynamoDB.
- Lambda resolvers where needed.
- S3/Amplify hosting.

Pros:

- Good for dashboard data.
- Real-time subscriptions possible.
- Strong frontend integration.

Cons:

- More GraphQL learning.
- Device agents may not benefit as much.
- Can become complex.

## Option AWS-4 — Minimal container backend

Possible services:

- ECS Fargate or App Runner.
- DynamoDB or PostgreSQL.
- Cognito.
- S3/CloudFront.

Pros:

- Simpler backend programming model.
- Easier long-running API service.
- May be easier if backend grows.

Cons:

- Not completely serverless from a cost perspective.
- Higher idle cost than Lambda-first design.

### Codex must recommend

Codex should recommend the best architecture for:

- Cheapest MVP.
- Best long-term architecture.
- Best balance of learning, cost, and maintainability.

The recommendation should include why.

---

## 14. Expected Cost Strategy

The design should assume:

- Very small number of users initially.
- One family first.
- A few devices first.
- Cost should stay near zero or very low while idle.
- Avoid always-on servers.
- Avoid managed databases with fixed monthly cost.
- Avoid NAT Gateway unless absolutely necessary.
- Avoid EKS.
- Avoid RDS for MVP unless strongly justified.
- Avoid Fargate for always-on services in MVP unless strongly justified.

Codex should generate an estimated cost model after choosing the architecture.

---

## 15. Data Model — Conceptual

Codex should propose a final schema, but the conceptual entities are:

### ParentAccount

- parentId
- email
- displayName
- createdAt
- status

### Family

- familyId
- ownerParentId
- name
- createdAt

### ChildProfile

- childId
- familyId
- displayName
- timezone
- createdAt
- status

### Device

- deviceId
- childId
- platform
- name
- agentVersion
- lastSeenAt
- enrollmentStatus
- policyVersion
- status

### UsageEvent

- eventId
- deviceId
- childId
- timestamp
- eventType
- appId
- appName
- category
- durationSeconds
- metadata

### UsageAggregate

- childId
- date
- totalSeconds
- byDevice
- byApp
- updatedAt

### Policy

- policyId
- childId
- version
- rules
- createdAt
- updatedAt

### DeviceCommand

- commandId
- deviceId
- commandType
- payload
- status
- createdAt
- acknowledgedAt

### AuditEvent

- auditId
- familyId
- actorType
- actorId
- action
- targetType
- targetId
- timestamp
- metadata

---

## 16. API Capabilities

Codex should propose final API details, but the system needs APIs for:

### Parent APIs

- Create child profile.
- List child profiles.
- Get child usage summary.
- Get device list.
- Get device detail.
- Create/update policy.
- Grant bonus time.
- Lock device.
- Unlock device.
- View audit events.

### Device APIs

- Enroll device.
- Refresh device credentials.
- Send heartbeat.
- Send usage events.
- Fetch current policy.
- Fetch pending commands.
- Acknowledge command.
- Upload diagnostics.

---

## 17. Windows Agent Functional Specification

The Windows agent should include:

### Local components

- Installer.
- Background service.
- Optional tray app or small child-facing UI.
- Local configuration file.
- Local event queue.
- Local policy cache.
- Local logs.

### Behavior

- Start automatically on boot.
- Identify current logged-in user.
- Track active app/window.
- Detect idle time.
- Send usage events.
- Pull policy updates or receive commands.
- Apply enforcement.
- Show warning before lock.
- Lock device/session when needed.
- Queue events while offline.
- Recover cleanly after reboot.

### MVP Windows enforcement

Codex should propose the simplest viable implementation.

Potential MVP enforcement:

- Warn the user when limit is near.
- Lock Windows session when limit is reached.
- Continue to lock again if child unlocks and limit is still exceeded.
- Allow parent override from dashboard.

---

## 18. Android Agent Functional Specification

The Android agent should include:

### Local components

- Android app.
- Setup/enrollment screen.
- Permission guidance flow.
- Local policy cache.
- Local usage tracker.
- Local status screen.
- Background sync job.

### Behavior

- Enroll device using pairing code.
- Request necessary permissions.
- Track app usage where technically feasible.
- Send usage events.
- Fetch policy.
- Show warnings.
- Apply restrictions where feasible.
- Queue events while offline.

### MVP Android enforcement

Codex should propose one of these MVP directions:

1. Monitoring-first standard Android app.
2. Device Owner managed-device approach.
3. Android Management API approach.

Codex must explain tradeoffs clearly before coding.

---

## 19. Parent Dashboard Functional Specification

The dashboard should be simple and clean.

### MVP dashboard

Required MVP pages:

1. Login.
2. Family dashboard.
3. Child detail page.
4. Device enrollment page.
5. Policy settings page.
6. Usage summary page.

### UX priorities

- Show how much time each child used today.
- Show whether the child is allowed or blocked.
- Make it easy to add a device.
- Make it easy to change daily limit.
- Make manual lock/unlock obvious.
- Keep advanced settings hidden initially.

---

## 20. Implementation Strategy Required from Codex

Before writing code, Codex must generate a planning report with:

# Codex Planning Report

## 1. Recommended MVP

Describe the smallest useful version.

## 2. Architecture Options

Compare:

- Lambda + API Gateway + DynamoDB.
- Lambda + AWS IoT Core + DynamoDB.
- AppSync + DynamoDB.
- Container backend.

## 3. Android Strategy Options

Compare:

- Usage Access app.
- Device Owner app.
- Android Management API.

## 4. Windows Strategy Options

Compare:

- User-mode app.
- Windows service.
- Windows service + OS policies.

## 5. Recommended Final Direction

Choose one direction for MVP and explain:

- Why it is cheapest.
- Why it is realistic.
- What it can enforce.
- What it cannot enforce yet.
- How it can evolve.

## 6. Phased Roadmap

Include:

- Phase 0: Project skeleton and local development.
- Phase 1: Backend MVP.
- Phase 2: Parent dashboard MVP.
- Phase 3: Windows agent MVP.
- Phase 4: Android monitoring MVP.
- Phase 5: Enforcement improvements.
- Phase 6: Packaging, CI/CD, and hardening.

## 7. Repository Structure

Propose the repo layout.

## 8. Infrastructure Plan

Propose AWS resources and IaC approach.

## 9. Security Model

Explain auth, device identity, permissions, and data isolation.

## 10. Cost Estimate

Estimate expected monthly cost for:

- 1 family.
- 5 devices.
- 100 families.
- 500 devices.

Use conservative assumptions.

---

## 21. Suggested Repository Structure

Codex can change this if it has a better recommendation.

```text
shield-my-kids/
  README.md
  docs/
    product/
      vision.md
      functional-requirements.md
      roadmap.md
    architecture/
      options.md
      decisions/
    security/
      threat-model.md
      privacy.md
    operations/
      runbook.md

  apps/
    parent-web/
    android-agent/
    windows-agent/

  services/
    api/
    policy-engine/
    usage-aggregator/

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
        iot/

  packages/
    shared-types/
    shared-auth/
    shared-protocol/

  scripts/
  .github/
    workflows/
```

---

## 22. Preferred Engineering Principles

Codex should follow these principles:

- Keep MVP small.
- Favor simple serverless architecture.
- Favor low idle cost.
- Avoid premature microservices.
- Use infrastructure as code.
- Use strong typing where possible.
- Keep agents resilient offline.
- Keep device protocol explicit and versioned.
- Keep data model simple.
- Avoid invasive monitoring.
- Document limitations honestly.
- Build testable components.
- Separate policy decision from policy enforcement.
- Avoid hardcoding AWS credentials.
- Use least privilege IAM.

---

## 23. Deliverables Codex Should Produce First

Codex should initially create or update these documents, not full code:

1. `docs/product/vision.md`
2. `docs/product/functional-requirements.md`
3. `docs/architecture/options.md`
4. `docs/architecture/mvp-recommendation.md`
5. `docs/security/privacy-and-safety.md`
6. `docs/security/threat-model.md`
7. `docs/product/roadmap.md`
8. `docs/architecture/aws-cost-strategy.md`

After that, Codex should wait for the user to choose the architecture and MVP direction.

---

## 24. Questions Codex Should Answer in the Planning Report

Codex should explicitly answer:

1. What is the cheapest realistic AWS architecture?
2. Is AWS IoT Core worth it for the first MVP?
3. Should devices poll the backend or use MQTT?
4. What is the simplest Windows enforcement mechanism?
5. What Android approach gives the best balance of usability and enforcement?
6. How should overlapping usage across devices be counted?
7. How should offline events be synced?
8. What data should never be collected?
9. What is the safest way to authenticate devices?
10. What should be built first?

---

## 25. Recommended MVP Hypothesis

Codex should evaluate this hypothesis, but not blindly accept it:

> The first MVP should use a Lambda + API Gateway + DynamoDB backend, Cognito authentication, S3/CloudFront or Amplify Hosting for the parent dashboard, and polling-based device agents. AWS IoT Core should be considered for a later phase unless real-time commands become essential. The Windows agent should be built first because it is more controllable for a personal MVP. Android should start as monitoring-first unless the user accepts Device Owner / Android Enterprise enrollment friction.

Codex should either confirm, improve, or reject this hypothesis with reasoning.

---

## 26. Definition of Done for Planning Phase

The planning phase is complete when:

- Architecture options are compared.
- Android options are compared.
- Windows options are compared.
- MVP recommendation is clear.
- Cost strategy is documented.
- Data model is proposed.
- Security model is documented.
- Roadmap is written.
- The user can choose a direction confidently.

---

## 27. Codex CLI Starting Prompt

Use the following prompt with Codex CLI:

```text
You are working on my personal project called Shield My Kids.

Read this specification carefully. Do not start coding the full system immediately.

Your first task is to create a planning package for the project focused on functionality, architecture options, MVP strategy, and cost-aware AWS infrastructure.

The product is a parental-control and screen-time management system for Windows and Android devices. It needs a parent dashboard, backend API, device enrollment, child profiles, screen-time tracking, cross-device usage aggregation, policy/rule management, and enforcement where technically feasible.

The infrastructure must be the cheapest practical option in AWS, preferably serverless. Compare Lambda + API Gateway + DynamoDB, AWS IoT Core, AppSync, and a minimal container backend. Recommend an MVP architecture.

For Android, compare standard Usage Access app, Device Owner app, and Android Management API. Explain what each can and cannot enforce.

For Windows, compare user-mode app, Windows service, and Windows service plus OS-level policies. Recommend the simplest useful MVP.

Create or update the planning documents under docs/ first:
- docs/product/vision.md
- docs/product/functional-requirements.md
- docs/product/roadmap.md
- docs/architecture/options.md
- docs/architecture/mvp-recommendation.md
- docs/architecture/aws-cost-strategy.md
- docs/security/privacy-and-safety.md
- docs/security/threat-model.md

Do not build the whole application yet. Produce a clear planning report and wait for my decision on the MVP direction.
```

---

## 28. Reference Notes

The following public documentation areas are relevant for Codex to verify during implementation planning:

- AWS Amplify pricing and hosting.
- AWS Lambda pricing and limits.
- Amazon API Gateway HTTP API pricing and limits.
- Amazon DynamoDB on-demand pricing and limits.
- Amazon Cognito pricing and limits.
- AWS IoT Core MQTT and device identity.
- Android `DevicePolicyManager`.
- Android Management API policies.
- Windows foreground application tracking APIs.
- Windows service model.
- Windows Assigned Access / kiosk-style restrictions.
- Windows Filtering Platform, only if deeper network/app blocking is later needed.

Codex should verify current documentation before implementing platform-specific enforcement.

