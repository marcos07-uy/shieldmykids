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

## Pull Request Validation

Terraform changes are validated by the `Terraform PR Checks` GitHub Actions workflow on pull requests to `main`.
This workflow is the required merge gate for Terraform changes once branch protection is fully configured.

The workflow runs:

- `terraform fmt -check -recursive infrastructure/terraform`
- `terraform init -backend=false -input=false` from `infrastructure/terraform/environments/dev`
- `terraform validate -no-color` from `infrastructure/terraform/environments/dev`

To block merges until these checks pass, configure branch protection for `main` and require the `Terraform PR Checks / Terraform fmt and validate` status check.
