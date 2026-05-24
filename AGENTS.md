# Agent Instructions

This file provides repository-level instructions for coding agents working on Shield My Kids.

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
- Add focused tests and documentation for the current slice.

Not allowed without explicit user approval:

- `terraform apply` or any AWS deployment.
- Production infrastructure.
- CI/CD workflows.
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

