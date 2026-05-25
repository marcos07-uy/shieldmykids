# Dev Terraform Environment

This environment deploys the minimal backend slice:

- `POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes`
- `PUT /v1/parent/families/{familyId}/children/{childId}/policy`
- `POST /v1/device/enroll`
- `POST /v1/device/heartbeat`
- `POST /v1/device/usage-events`
- `GET /v1/device/policy`

## Review First

Before deployment, review the generated plan:

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
```

Set `dev_parent_token` to a long random value before planning or applying.

## Minimal Flow

Create a pairing code:

```bash
curl -X POST "$API/v1/parent/families/fam-dev/children/child-dev/pairing-codes"   -H "X-Dev-Parent-Token: $DEV_PARENT_TOKEN"
```

Store a policy:

```bash
curl -X PUT "$API/v1/parent/families/fam-dev/children/child-dev/policy"   -H "Content-Type: application/json"   -H "X-Dev-Parent-Token: $DEV_PARENT_TOKEN"   -d '{
    "rules": {
      "dailyLimitMinutes": 120,
      "allowedSchedule": [
        { "days": ["mon", "tue", "wed", "thu"], "start": "16:00", "end": "20:00" },
        { "days": ["fri"], "start": "16:00", "end": "21:30" },
        { "days": ["sat", "sun"], "start": "09:00", "end": "21:30" }
      ],
      "warningThresholdMinutes": 10,
      "bonusMinutes": 0,
      "manualLock": { "enabled": false, "reason": null, "expiresAt": null }
    }
  }'
```

Enroll a device:

```bash
curl -X POST "$API/v1/device/enroll"   -H "Content-Type: application/json"   -d '{
    "pairingCode": "123456",
    "platform": "windows",
    "deviceName": "Child Windows Laptop",
    "agentVersion": "0.1.0"
  }'
```

Send a heartbeat as a device:

```bash
curl -X POST "$API/v1/device/heartbeat"   -H "Authorization: Device $DEVICE_CREDENTIAL"   -H "X-Device-Id: $DEVICE_ID"   -H "Content-Type: application/json"   -d '{
    "agentVersion": "0.1.0",
    "platformVersion": "Windows 11",
    "policyVersion": 1,
    "enforcementState": "allowed",
    "queueDepth": 0
  }'
```

Submit usage events as a device:

```bash
curl -X POST "$API/v1/device/usage-events"   -H "Authorization: Device $DEVICE_CREDENTIAL"   -H "X-Device-Id: $DEVICE_ID"   -H "Content-Type: application/json"   -d '{
    "batchId": "batch-001",
    "events": [
      {
        "eventId": "evt-001",
        "startedAt": "2026-05-25T16:00:00Z",
        "endedAt": "2026-05-25T16:15:00Z",
        "activityType": "screen",
        "appName": "Browser"
      }
    ]
  }'
```

Fetch policy as a device:

```bash
curl "$API/v1/device/policy"   -H "Authorization: Device $DEVICE_CREDENTIAL"   -H "X-Device-Id: $DEVICE_ID"
```
