# Operations Runbook

## Current State Note

This is mostly an operational plan. A Terraform dev environment and minimal backend Lambda definition exist in the repository, but infrastructure has not been deployed yet.

## Environments

Planned environments:

- `dev`: personal testing and early agent development.
- `prod`: family use after MVP stabilization.

Environment separation:

- Separate Terraform state.
- Separate Cognito app clients.
- Separate DynamoDB tables.
- Separate API domains or stages.
- Separate budget alerts.

## Deployment Principles

- Infrastructure changes go through Terraform.
- Terraform pull requests are validated by GitHub Actions before merge when branch protection requires the workflow check.
- Application deployments should eventually go through CI/CD.
- Current dev deployment, if approved, is manual Terraform from `infrastructure/terraform/environments/dev`.
- Production deploys require successful tests.
- Secrets are never committed.
- Rollback steps are documented per service.

## Branch Protection

To prevent unvalidated IaC changes from merging, configure GitHub branch protection for `main` to require the `Terraform PR Checks / Terraform fmt and validate` status check.

This repository contains the workflow definition, but GitHub branch protection is enforced in repository settings, not by the workflow file itself.

## Monitoring

Minimum metrics:

- API 4xx errors.
- API 5xx errors.
- Lambda errors.
- Lambda duration.
- DynamoDB throttles.
- Device heartbeat freshness.
- Usage ingestion failures.
- Command acknowledgement latency.
- Pairing failures.

Minimum alarms:

- Elevated 5xx rate.
- Lambda error spike.
- DynamoDB throttling.
- No heartbeat from device over threshold.
- Monthly cost forecast exceeds budget.

## Logging

Logging requirements:

- Include request ID.
- Include family ID only when needed.
- Include device ID for device requests.
- Never log credentials.
- Never log raw pairing codes.
- Never log private content.
- Set explicit retention.

## Incident Response

### Suspected Parent Account Compromise

Steps:

1. Disable or reset the parent account through Cognito.
2. Review audit events.
3. Revoke device commands created during compromise window if possible.
4. Rotate affected device credentials if needed.
5. Notify affected parent.

### Suspected Device Credential Compromise

Steps:

1. Revoke device credential.
2. Mark device as requiring re-enrollment.
3. Review usage and command history.
4. Notify parent dashboard.
5. Reissue credential only through pairing flow.

### Bad Policy Causes Incorrect Locking

Steps:

1. Use parent dashboard or admin recovery procedure to unlock.
2. Disable problematic policy version.
3. Audit affected devices.
4. Add regression test before re-enabling.

### Cost Spike

Steps:

1. Check API Gateway request volume.
2. Check CloudWatch log ingestion.
3. Check DynamoDB consumed capacity.
4. Check polling interval changes.
5. Temporarily increase sync interval if needed.
6. Add rate limits or batching fixes.

## Backup And Recovery

MVP strategy:

- DynamoDB point-in-time recovery for production-critical tables if cost allows.
- Terraform state bucket versioning.
- Source control for all IaC and application code after implementation begins.

Recovery objectives:

- Family configuration should be recoverable.
- Device credentials can be revoked and reissued.
- Raw usage loss is acceptable only within a clearly documented window.

## Manual Recovery Requirements

The system must include a future documented way to:

- Revoke a device.
- Disable a child policy.
- Unlock a device.
- Disable a parent account.
- Export audit events.

