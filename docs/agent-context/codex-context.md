# Codex Agent Context

## Repository

- Local path: `/home/marcos/shared/repos/shieldMyKids`
- GitHub SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- GitHub web URL: `https://github.com/marcos07-uy/shieldmykids`
- Default branch: `main`

## Project Summary

Shield My Kids is a personal parental-control and family screen-time management system.

It should help parents:

- Monitor screen time per child across multiple devices.
- Understand app and device usage.
- Configure daily limits and schedules.
- Enforce limits where operating systems allow it.
- Register and manage Windows and Android child devices.
- Use a parent web dashboard.

The product must avoid spyware-like behavior and be transparent to the child.

## Current Project Phase

The Phase 0 documentation baseline is complete. The repository has moved into a narrow Phase 1 minimal backend slice.

Current implemented slice:

- Python minimal API Lambda.
- Terraform dev environment.
- Terraform `minimal_backend` module.

Current backend capabilities:

- Create short-lived pairing codes.
- Store or update a child policy.
- Enroll a device by exchanging a pairing code for a device credential.
- Accept device heartbeats and raw usage event batches.
- Queue manual lock/unlock commands, return queued commands to authenticated devices, and accept command acknowledgements.
- Return a basic parent usage summary from raw usage events.
- Record and list audit events for enrollment, policy updates, command queueing, and command acknowledgements.
- Let an enrolled device fetch its current effective policy.

Current local tests:

- `tests/backend/lambda/minimal_api/test_app.py`
- `python3 -m unittest tests/backend/lambda/minimal_api/test_app.py`
- 35 tests passed locally after PR #12 merged.

Agents may create or update:

- Documentation and ADRs.
- Existing minimal backend Lambda code.
- Existing minimal backend Terraform.
- Focused local tests for the current backend slice.

Agents must not create without explicit user approval:

- Android source files.
- Windows source files.
- Parent dashboard source files.
- Production infrastructure.
- CI/CD workflow files.
- Package manager manifests.
- Build scripts.

Agents must not deploy infrastructure or mutate AWS resources without explicit user approval.

## Repository Workflow

- `main` is protected and changes should be proposed through pull requests.
- Required approving reviews are intentionally not enabled while this remains a solo repository.
- Terraform-related PRs must pass the `Terraform fmt and validate` check from the `Terraform PR Checks` workflow.
- PR #1 registered the Terraform status check and was merged after it passed.
- Local Git SSH access is configured repo-locally with `core.sshCommand` using `~/.ssh/github`; SSH fetch and dry-run push have succeeded.
- Local sandboxed file edits were fixed by setting `kernel.apparmor_restrict_unprivileged_userns = 0`; avoid reverting that workstation setting unless an alternative sandbox configuration is available.

## Current Recommended Next Step

After audit events merge, review a Terraform plan from the separate AWS-credentialed deployment machine before any apply. ADR-0004 keeps the current Python Lambda for local hardening of the existing minimal slice until that deployment decision is made; broader TypeScript/shared-contract work remains deferred.

Keep command execution/enforcement behavior in agents out of scope until explicitly approved.

## Recommended Technical Direction

The current recommended MVP direction is:

- AWS API Gateway HTTP API.
- AWS Lambda.
- Amazon DynamoDB.
- Amazon Cognito.
- Static parent web app hosted with S3/CloudFront or Amplify Hosting.
- Amazon SES for email notifications.
- EventBridge for scheduled aggregation and cleanup jobs.
- Terraform for infrastructure.

Device communication should start with polling because it is simple and cheap. AWS IoT Core can be added later when lower-latency command delivery is needed.

## Platform Direction

Windows MVP:

- Windows service for persistence.
- Visible tray/status app for child transparency and interactive-desktop actions.
- Foreground app tracking.
- Idle detection.
- Local policy cache.
- Local event queue.
- Session lock enforcement.

Android MVP:

- Standard app using Usage Access.
- Enrollment screen.
- Permission guidance.
- Usage reporting.
- Local warnings.
- Limited enforcement.

Later Android enforcement may use Device Owner or Android Management API.

## Security Priorities

- Parent JWT validation on every parent API.
- Device-token validation on every device API.
- Parent ownership checks for all family data.
- Device scoping so devices cannot submit usage for other devices.
- Revocable device credentials.
- Minimal personal data.
- No content capture.
- No covert monitoring.
- Explicit audit logs.

## Architecture Principles

- Keep the MVP small.
- Prefer low idle cost.
- Prefer serverless.
- Keep the backend as source of truth.
- Keep device protocol explicit and versioned.
- Prefer simple DynamoDB access patterns over premature relational modeling.
- Document every major tradeoff in an ADR.
