# Terraform

Terraform is organized as:

```text
infrastructure/terraform/
  environments/
    dev/
  modules/
    minimal_backend/
```

The first implemented module provides the backend needed to store a child policy, enroll a device, and let that device fetch its effective policy.

Production concerns still deferred:

- Cognito parent authentication.
- Remote Terraform state.
- Budget alarms.
- WAF or stricter edge controls.
- CI/CD.
