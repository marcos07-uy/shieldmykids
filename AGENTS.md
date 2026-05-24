# Agent Instructions

This file provides repository-level instructions for coding agents working on Shield My Kids.

## Repository

- Local path: `/home/marcos/shared/repos/shieldMyKids`
- GitHub SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- GitHub web URL: `https://github.com/marcos07-uy/shieldmykids`
- Default branch: `main`

## Current Phase

The project has completed the initial **Phase 0 documentation baseline** and has moved into a narrow **Phase 1 minimal backend slice**.

Existing implementation is limited to the minimal backend Lambda and Terraform dev environment already present in the repository.

Do not expand implementation beyond that slice without explicit user approval. Do not deploy infrastructure or mutate AWS resources without explicit user approval.

## Primary Source Documents

Read these files before making changes:

1. [codex.md](codex.md)
2. [README.md](README.md)
3. [docs/agent-context/codex-context.md](docs/agent-context/codex-context.md)
4. [docs/product/roadmap.md](docs/product/roadmap.md)
5. [docs/architecture/overview.md](docs/architecture/overview.md)
6. [docs/security/threat-model.md](docs/security/threat-model.md)

## Documentation Rules

- Keep planning documentation clear about what is implemented, planned, deferred, or intentionally out of scope.
- Prefer explicit tradeoffs over vague recommendations.
- Document limitations honestly.
- Keep security, privacy, and child transparency visible in every major design decision.
- Use Mermaid diagrams when a flow or boundary is easier to understand visually.
- Add architecture decision records for material decisions.

## Current Engineering Boundary

Allowed in the current minimal backend slice:

- Maintain the existing Python minimal API Lambda.
- Maintain the existing Terraform dev environment and `minimal_backend` module.
- Run local validation and Terraform formatting, init, validate, and plan when tooling is available.
- Maintain the approved Terraform PR validation GitHub Actions workflow.
- Add focused tests and documentation for the current slice.

Not allowed without explicit user approval:

- `terraform apply` or any AWS deployment.
- Production infrastructure.
- New CI/CD workflows beyond the approved Terraform PR validation workflow.
- Parent dashboard implementation.
- Windows or Android agent implementation.
- New package manifests or build scripts outside the approved slice.

Engineering direction for later approved implementation:

- Prefer TypeScript for backend/shared contracts unless a later ADR changes this.
- Prefer a serverless AWS MVP using API Gateway HTTP API, Lambda, DynamoDB, Cognito, and static hosting.
- Prefer Terraform for all cloud infrastructure.
- Avoid always-on services for MVP.
- Avoid NAT Gateway, RDS, ECS, EKS, and public databases unless an ADR justifies them.
- Use explicit API versioning for device protocols.
- Keep agents resilient offline with policy cache and local event queue.
- Never implement covert surveillance features.

## Current Handoff

Last updated: 2026-05-24.

Completed in the current session:

- Initialized the local Git repository and pushed it to `git@github.com:marcos07-uy/shieldmykids.git`.
- Set the repository-local Git author email to `marcos.s.lucas@gmail.com`.
- Pushed the initial project baseline on `main`.
- Added GitHub repository metadata to the main agent and documentation context files.
- Added the approved Terraform PR validation workflow at `.github/workflows/terraform-pr.yml`.
- Committed the Terraform provider lock file at `infrastructure/terraform/environments/dev/.terraform.lock.hcl`.
- Updated `.gitignore` so Terraform lock files are tracked.
- Verified locally with Terraform `v1.15.4`:
  - `terraform fmt -check -recursive infrastructure/terraform`
  - `terraform init -backend=false -input=false` from `infrastructure/terraform/environments/dev`
  - `terraform validate -no-color` from `infrastructure/terraform/environments/dev`
- Pushed commit `aedfacf Add Terraform pull request validation` to `origin/main`.

Remaining next step before continuing implementation:

- Configure GitHub branch protection for `main` so Terraform checks must pass before merge. This was not completed because this environment has SSH Git access only, no `gh` CLI, and no GitHub API token.

Branch protection target:

- Repository: `https://github.com/marcos07-uy/shieldmykids`
- Branch: `main`
- Required check: `Terraform PR Checks / Terraform fmt and validate`

Manual GitHub setup path:

1. Open `https://github.com/marcos07-uy/shieldmykids/settings/branches`.
2. Add a branch rule or ruleset targeting `main`.
3. Enable pull requests before merging.
4. Enable required status checks before merging.
5. Select `Terraform PR Checks / Terraform fmt and validate`.
6. Save the rule.

If the status check is not listed yet, create a small test pull request that changes a file under `infrastructure/terraform/**` so the workflow runs once, then return to branch protection and select the check.

After branch protection is configured, the next useful engineering tasks are:

1. Add focused tests for `backend/lambda/minimal_api/app.py`.
2. Decide whether to keep Python for this Lambda slice or record an ADR for a TypeScript/shared-contract backend direction.
3. Review the Terraform plan before any `terraform apply`.
4. Replace temporary `X-Dev-Parent-Token` authentication with Cognito when approved.

## Safety Constraints

The product is for parent/guardian-managed devices. Agents must not help implement spyware behavior.

Disallowed features:

- Keylogging.
- Silent screenshots.
- Hidden installation.
- Stealth persistence.
- Camera or microphone collection.
- Credential theft.
- Browser password capture.
- Private message content capture.

Allowed product behavior:

- Transparent screen-time tracking.
- Visible child-facing status.
- Usage aggregation.
- Policy enforcement using documented OS capabilities.
- Parent-controlled lock/unlock and limit configuration.

