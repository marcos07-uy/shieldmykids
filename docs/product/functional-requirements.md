# Functional Requirements

## Parent Dashboard

Required MVP screens:

1. Login and signup.
2. Family dashboard.
3. Child detail.
4. Device enrollment.
5. Policy settings.
6. Usage summary.
7. Audit log.

Parent capabilities:

- Create a parent account.
- Log in securely.
- Create child profiles.
- Register devices to child profiles.
- View today's usage per child.
- View usage by device.
- View app usage where platform data is available.
- Configure daily limits.
- Configure simple schedules.
- Configure manual lock and unlock.
- Grant bonus time.
- View device last-seen status.
- View enforcement status.
- View audit events.

## Backend API

Backend responsibilities:

- Authenticate parents.
- Authenticate devices.
- Authorize data access.
- Manage families.
- Manage child profiles.
- Manage devices.
- Generate pairing codes.
- Exchange pairing codes for device credentials.
- Ingest heartbeats.
- Ingest usage events.
- Store policies.
- Evaluate policy state.
- Generate device commands.
- Track command acknowledgement.
- Aggregate usage.
- Record audit events.

The backend is the source of truth for:

- Family membership.
- Child profile ownership.
- Device identity.
- Policy versions.
- Daily usage totals.
- Current enforcement state.
- Audit history.

## Child Profiles

A child profile represents one child and may have multiple devices.

Required fields:

- Child ID.
- Family ID.
- Display name.
- Time zone.
- Status.
- Created timestamp.
- Current policy version.
- Current usage summary.

Optional fields:

- Age range.
- Avatar color or display hint.

## Device Enrollment

MVP pairing flow:

1. Parent opens the dashboard.
2. Parent selects a child.
3. Dashboard generates a short-lived pairing code.
4. Parent enters code in the child agent setup screen.
5. Agent exchanges code with backend.
6. Backend binds device to child profile.
7. Backend returns device ID, device credential, and initial policy.
8. Agent starts heartbeat and usage reporting.

Pairing requirements:

- Pairing codes expire.
- Pairing codes are single-use.
- Pairing codes reveal no permanent credential.
- Audit event is recorded for code generation and enrollment.

## Screen-Time Tracking

MVP tracking:

- Active usage intervals.
- Idle intervals where detectable.
- Foreground application on Windows.
- Android app usage from approved Usage Access APIs.
- Periodic usage summaries.

Events:

- Device heartbeat.
- Session started.
- Session ended.
- Foreground app changed.
- Usage interval summary.
- Policy applied.
- Lock state changed.
- Error or diagnostic event.

Cross-device aggregation:

- MVP should count overlapping active intervals once per child.
- Raw per-device usage should still be retained for reporting.
- Aggregation should be recomputable from raw events where practical.

## Rules And Policies

MVP policy rules:

- Daily screen-time limit.
- Allowed schedule.
- Manual lock.
- Manual unlock.
- Bonus time.
- Warning threshold.

Deferred rules:

- Weekly limits.
- App category budgets.
- Complex school-night/weekend schedules.
- Emergency override.
- Child request workflow.
- Advanced app allowlists and blocklists.

## Enforcement

Windows MVP:

- Show warning near limit.
- Lock session when blocked.
- Re-lock after unlock if still blocked.
- Continue local fallback enforcement using cached policy.
- Queue events offline.

Android MVP:

- Show status and warnings.
- Report usage.
- Cache policy.
- Queue events offline.
- Clearly disclose enforcement limitations.

## Notifications

MVP:

- Dashboard notifications.
- Email notifications through SES where useful.

Events:

- Device enrolled.
- Limit nearly reached.
- Limit reached.
- Device offline too long.
- Policy failed to apply.
- Manual lock/unlock completed.

