# API Contract

## API Principles

- Version all APIs.
- Separate parent APIs from device APIs.
- Validate authentication on every request.
- Validate ownership on every parent request.
- Validate device scope on every device request.
- Use idempotency keys for device event ingestion.
- Return explicit error codes suitable for agents.

Base paths:

- `/v1/parent/*`
- `/v1/device/*`

## Parent Authentication

Parent APIs use Cognito JWTs.

Required checks:

- JWT signature is valid.
- Token has not expired.
- Parent account exists or can be provisioned.
- Parent has access to the target family.

## Device Authentication

Device APIs use device credentials issued during enrollment.

Recommended request headers:

- `Authorization: Device <token>`
- `X-Device-Id: <deviceId>`
- `X-Protocol-Version: 1`

Required checks:

- Device exists.
- Credential is valid.
- Credential is not revoked.
- Device status allows sync.
- Request device ID matches credential scope.

## Parent API Surface

### Create Child

`POST /v1/parent/families/{familyId}/children`

Purpose:

- Create a child profile.

### List Children

`GET /v1/parent/families/{familyId}/children`

Purpose:

- Return children for a family with high-level usage and status.

### Get Child Detail

`GET /v1/parent/families/{familyId}/children/{childId}`

Purpose:

- Return child profile, devices, policy summary, and current usage.

### Create Pairing Code

`POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes`

Purpose:

- Generate a short-lived code for device enrollment.

### Get Usage Summary

`GET /v1/parent/families/{familyId}/children/{childId}/usage?date=YYYY-MM-DD`

Purpose:

- Return total child usage, per-device usage, and per-app usage.

### Update Policy

`PUT /v1/parent/families/{familyId}/children/{childId}/policy`

Purpose:

- Replace or update child policy.

### Manual Lock

`POST /v1/parent/families/{familyId}/devices/{deviceId}/lock`

Purpose:

- Queue a lock command.

### Manual Unlock

`POST /v1/parent/families/{familyId}/devices/{deviceId}/unlock`

Purpose:

- Queue an unlock command or update manual lock state.

### List Audit Events

`GET /v1/parent/families/{familyId}/audit-events`

Purpose:

- Return audit events for the family.

## Device API Surface

### Enroll Device

`POST /v1/device/enroll`

Purpose:

- Exchange pairing code for device identity and credential.

Request includes:

- Pairing code.
- Platform.
- Device name.
- Agent version.
- Public metadata.

Response includes:

- Device ID.
- Device credential.
- Initial policy.
- Sync interval.

### Heartbeat

`POST /v1/device/heartbeat`

Purpose:

- Report device status and receive current policy metadata.

Request includes:

- Device ID.
- Agent version.
- Local time.
- Current policy version.
- Enforcement state.
- Queue depth.

Response includes:

- Server time.
- Effective policy version.
- Desired enforcement state.
- Pending command count.
- Recommended sync interval.

### Submit Usage Events

`POST /v1/device/usage-events`

Purpose:

- Submit one or more usage events.

Request includes:

- Device ID.
- Batch ID.
- Events.

Response includes:

- Accepted event IDs.
- Duplicate event IDs.
- Rejected event IDs with reasons.

### Fetch Policy

`GET /v1/device/policy`

Purpose:

- Fetch current effective policy for the authenticated device.

### Fetch Commands

`GET /v1/device/commands`

Purpose:

- Fetch pending commands for the authenticated device.

### Acknowledge Command

`POST /v1/device/commands/{commandId}/ack`

Purpose:

- Report command execution result.

Request includes:

- Status.
- Applied timestamp.
- Error code.
- Diagnostics summary.

### Upload Diagnostics

`POST /v1/device/diagnostics`

Purpose:

- Upload non-sensitive operational diagnostics.

Diagnostics must not include:

- Keystrokes.
- Screenshots.
- Message contents.
- Passwords.
- Browser contents.

## Error Model

Recommended error shape:

```json
{
  "error": {
    "code": "DEVICE_CREDENTIAL_REVOKED",
    "message": "Device credential is no longer valid.",
    "requestId": "request-id"
  }
}
```

Device-relevant error codes:

- `DEVICE_CREDENTIAL_INVALID`
- `DEVICE_CREDENTIAL_REVOKED`
- `DEVICE_DISABLED`
- `POLICY_VERSION_UNSUPPORTED`
- `RATE_LIMITED`
- `PAIRING_CODE_INVALID`
- `PAIRING_CODE_EXPIRED`
- `PAIRING_CODE_CONSUMED`
- `VALIDATION_FAILED`

Parent-relevant error codes:

- `UNAUTHENTICATED`
- `FORBIDDEN`
- `FAMILY_NOT_FOUND`
- `CHILD_NOT_FOUND`
- `DEVICE_NOT_FOUND`
- `VALIDATION_FAILED`

