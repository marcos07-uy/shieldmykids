# Minimal API Lambda

This Lambda implements the first backend slice:

- Create a short-lived pairing code for a child.
- Store or update the current child policy.
- Enroll a device by exchanging a pairing code for a device credential.
- Accept authenticated device heartbeats with lightweight status metadata.
- Let an enrolled device fetch its effective policy.

Parent routes use a temporary `X-Dev-Parent-Token` header. This is a development bridge until Cognito parent authentication is implemented.

Device routes use:

```text
Authorization: Device <deviceCredential>
X-Device-Id: <deviceId>
```
