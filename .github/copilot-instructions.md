# Copilot Instructions

This repository has completed the initial Phase 0 documentation baseline and now contains a narrow Phase 1 minimal backend slice.

Repository metadata:

- GitHub SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- GitHub web URL: `https://github.com/marcos07-uy/shieldmykids`
- Default branch: `main`

Existing implementation is limited to the minimal backend Lambda and Terraform dev environment already present in the repository.

Do not suggest or generate without explicit user approval:

- Parent dashboard implementation.
- Windows agent source code.
- Android agent source code.
- Production infrastructure.
- New CI/CD workflows beyond the approved Terraform PR validation workflow.
- Package manifests.
- Build scripts.

Do not deploy infrastructure or mutate AWS resources without explicit user approval.

Project constraints:

- AWS infrastructure must eventually be Terraform-managed.
- MVP architecture should be serverless and low-cost.
- Security and privacy are core product requirements.
- Device agents must be transparent to children.
- No spyware-like features are allowed.

Read [AGENTS.md](../AGENTS.md) and [CODEX.md](../CODEX.md) for full guidance.

