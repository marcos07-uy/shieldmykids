# Codex Context

This repository is a planning-first restart of Shield My Kids with an initial minimal backend slice now present.

## Repository

- Local path: `/home/marcos/shared/repos/shieldMyKids`
- GitHub SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- GitHub web URL: `https://github.com/marcos07-uy/shieldmykids`
- Default branch: `main`

## Non-Negotiable Instruction

The Phase 0 documentation baseline is complete. Existing implementation is limited to the minimal backend Lambda and Terraform dev environment already present in the repository.

Do not expand implementation beyond that slice, deploy infrastructure, or mutate AWS resources unless the user explicitly approves it.

## Mission

Create a transparent parental-control system that helps parents understand and manage child screen time across devices.

The MVP should prioritize:

- Low cloud cost.
- Clear architecture.
- Secure parent and device identity.
- Honest platform limitations.
- Transparent monitoring.
- Incremental delivery.

## Recommended MVP Direction

- Backend: AWS serverless API.
- Auth: Amazon Cognito.
- API: API Gateway HTTP API plus Lambda.
- Data: DynamoDB.
- Dashboard: static parent web app.
- Windows agent: service plus visible tray/status process.
- Android agent: monitoring-first app using Usage Access.
- Device communication: polling first, AWS IoT Core later if needed.
- Infrastructure: Terraform, modular, least-privilege, no always-on compute.

## Completed Phase 0 Deliverables

- Product documentation.
- Roadmap.
- Architecture documents.
- Data model.
- API contract.
- Terraform strategy.
- Security and privacy docs.
- Operations runbook.
- Agent instructions.
- ADRs.

## Repository Workflow

- `main` is protected and changes should go through pull requests.
- Required approving reviews are intentionally not enabled while this is a solo repository.
- Terraform-impacting PRs must pass the `Terraform fmt and validate` check from the `Terraform PR Checks` workflow before merge.
- PR #1 registered that status check and was merged after the workflow passed.
- Local SSH push initially failed because Git was not selecting the non-default `~/.ssh/github` key. The repository now sets `core.sshCommand` to `ssh -i ~/.ssh/github -o IdentitiesOnly=yes`, and SSH fetch plus dry-run push have succeeded.

## Guardrails

- Keep documentation synchronized with the actual repository state.
- Current backend implementation scope is the minimal API Lambda for pairing codes, policy storage, device enrollment, and policy fetch.
- Current infrastructure implementation scope is the Terraform dev environment and `minimal_backend` module.
- No AWS deployment without explicit approval.
- No parent dashboard, Windows agent, Android agent, production infrastructure, package manifests, build scripts, or CI workflows beyond the approved Terraform PR validation workflow without explicit approval.
- Keep architecture diagrams as Markdown/Mermaid unless a later approved implementation needs generated assets.
