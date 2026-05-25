# Current State Handoff

Last updated: 2026-05-25

## Repository Location

```text
/home/marcos/shared/repos/shieldMyKids
```

The folder is under the SMB share path:

```text
/home/marcos/shared
```

GitHub repository:

```text
git@github.com:marcos07-uy/shieldmykids.git
```

Web URL:

```text
https://github.com/marcos07-uy/shieldmykids
```

Default branch:

```text
main
```

## Project Status

Initial documentation baseline is complete. The project has moved into the first implementation slice: minimal backend infrastructure and Lambda API for policy/device enrollment.

The folder is a Git repository. Local `main` tracks `origin/main` at `git@github.com:marcos07-uy/shieldmykids.git`.

Local SSH push initially failed during branch-protection setup with `Permission denied (publickey)` because Git was not selecting the non-default `~/.ssh/github` key. This repository now sets `core.sshCommand` to `ssh -i ~/.ssh/github -o IdentitiesOnly=yes`; `git ls-remote` and `git push --dry-run` have succeeded.

`main` is protected in GitHub. Changes should go through pull requests before merge.

## Implemented Files

Minimal backend Lambda:

```text
backend/lambda/minimal_api/app.py
backend/lambda/minimal_api/README.md
```

Terraform:

```text
infrastructure/terraform/README.md
infrastructure/terraform/environments/dev/README.md
infrastructure/terraform/environments/dev/main.tf
infrastructure/terraform/environments/dev/outputs.tf
infrastructure/terraform/environments/dev/providers.tf
infrastructure/terraform/environments/dev/terraform.tfvars.example
infrastructure/terraform/environments/dev/variables.tf
infrastructure/terraform/modules/minimal_backend/README.md
infrastructure/terraform/modules/minimal_backend/main.tf
infrastructure/terraform/modules/minimal_backend/outputs.tf
infrastructure/terraform/modules/minimal_backend/variables.tf
infrastructure/terraform/modules/minimal_backend/versions.tf
```

Repo hygiene and automation:

```text
.gitignore
.github/workflows/terraform-pr.yml
```

README was updated to mark Phase 0 documentation complete and describe the current implementation boundary.

## Current Backend Scope

The minimal backend supports:

- Create a short-lived pairing code for a child.
- Store or update the current child policy.
- Return a basic parent usage summary from raw usage events.
- Enroll a device by exchanging a pairing code for a device credential.
- Accept authenticated device heartbeats with lightweight status metadata.
- Accept authenticated raw usage event batches with event-level idempotency.
- Queue manual lock/unlock commands and return queued commands to authenticated devices.
- Let an enrolled device fetch its current effective policy.

Routes:

```text
POST /v1/parent/families/{familyId}/children/{childId}/pairing-codes
PUT  /v1/parent/families/{familyId}/children/{childId}/policy
GET  /v1/parent/families/{familyId}/children/{childId}/usage
POST /v1/parent/families/{familyId}/devices/{deviceId}/lock
POST /v1/parent/families/{familyId}/devices/{deviceId}/unlock
POST /v1/device/enroll
POST /v1/device/heartbeat
POST /v1/device/usage-events
GET  /v1/device/commands
GET  /v1/device/policy
```

## Architecture Decisions In This Slice

Infrastructure uses the documented serverless polling MVP direction:

- API Gateway HTTP API
- Lambda
- DynamoDB
- CloudWatch logs
- Terraform

The Lambda is Python. This is only backend Lambda code. The future Windows agent should not be Python by default; use C#/.NET for the Windows Service plus visible tray/status helper.

Parent authentication is temporarily represented by `X-Dev-Parent-Token`. This is for development only. Cognito remains the intended production parent authentication path.

Device authentication uses:

```text
Authorization: Device <deviceCredential>
X-Device-Id: <deviceId>
```

Pairing codes and device credentials are stored as SHA-256 hashes in DynamoDB.

## Repository Workflow

Branch protection has been configured manually in GitHub:

- `main` requires pull requests before merging.
- Required approving reviews are not enabled because this is currently a solo repository and the owner cannot approve their own pull requests.
- Terraform changes are gated by the required `Terraform fmt and validate` status check from the `Terraform PR Checks` workflow.

PR #1, `Register Terraform PR check`, touched `infrastructure/terraform/README.md` so the workflow would run and the check would appear in branch protection. The workflow passed and PR #1 was merged on 2026-05-25.

## Validation Already Performed

No infrastructure was deployed.

Local validation performed:

- Python syntax parse passed.
- Local mocked Lambda flow passed:
  - create pairing code
  - store policy
  - enroll device
  - fetch policy with valid device credential
  - reject invalid device credential
- Generated Python bytecode cache was removed.
- Terraform `v1.15.4` is installed locally.
- Terraform validation passed locally:
  - `terraform fmt -check -recursive infrastructure/terraform`
  - `terraform init -backend=false -input=false` from `infrastructure/terraform/environments/dev`
  - `terraform validate -no-color` from `infrastructure/terraform/environments/dev`
- GitHub Actions PR validation passed in PR #1:
  - `Terraform PR Checks / Terraform fmt and validate`
- Git SSH access was fixed repo-locally with `core.sshCommand` using `~/.ssh/github`.

## User Boundary For Next Session

Do not deploy infrastructure until the user explicitly approves deployment.

Allowed before approval:

- Create/edit code and Terraform.
- Run local validation/static checks.
- Run `terraform fmt`, `terraform init`, `terraform validate`, or `terraform plan` if no resources are applied.

Not allowed before approval:

- `terraform apply`
- Any AWS deployment or resource mutation
- Any production credential setup

## Recommended Next Steps

1. Add tests for the Lambda handler with a proper test harness instead of an inline mock script.
2. Decide whether to keep Python for this Lambda slice or record an ADR for a TypeScript/shared-contract backend direction.
3. Run and review `terraform plan` with the user before any `apply`.
4. Replace temporary parent token auth with Cognito when moving beyond dev review.
5. Start Windows agent design/implementation in C#/.NET only after backend plan review and explicit approval to expand beyond the current backend slice.
