# ADR-0004: Phase 1 Runtime Continuity

## Status

Accepted for the remainder of the local Phase 1 backend work before the first dev deployment.

## Context

ADR-0003 kept the existing Python Lambda for the narrow minimal backend slice and deferred the broader backend runtime decision.

Since then, the minimal slice has grown to include the main backend plumbing needed before a first dev deployment review:

- Pairing code creation.
- Device enrollment.
- Device credential validation.
- Heartbeats.
- Usage event ingestion.
- Basic usage summary.
- Policy storage and fetch.
- Manual command queueing.
- Device command polling and acknowledgement.
- Audit event recording and listing.

The repository still has no AWS deployment. The next operational gate is a Terraform plan on the separate AWS-credentialed machine, followed by an explicit apply decision.

Switching this working slice to TypeScript before that gate would add migration churn without improving the deployment review. At the same time, continuing to add broad product APIs in Python would make the preferred TypeScript/shared-contract direction harder to recover later.

## Decision

Keep the current Python Lambda for local-only completion and hardening of the existing Phase 1 minimal backend slice until after:

- The Terraform plan has been reviewed on the AWS-credentialed machine.
- The user explicitly decides whether to perform the first dev deployment.
- The deployed or planned backend shape has been validated enough to justify the next product slice.

Allowed Python work before that point:

- Bug fixes in the current Lambda.
- Focused tests for existing routes.
- Small hardening changes for the existing route set.
- Documentation and Terraform maintenance for the current dev environment.

Do not add substantial new parent dashboard APIs, child profile management APIs, or agent implementation in Python before a separate runtime/shared-contract decision.

Keep TypeScript as the preferred direction for the broader backend and shared API contracts once the project moves beyond the minimal backend slice.

## Rationale

This keeps the first dev deployment review focused on infrastructure, IAM, DynamoDB shape, route wiring, and the already-tested minimal flows.

It avoids rewriting stable local code before it has been planned or deployed once. It also limits Python from becoming the default for the full product by inertia.

## Consequences

Positive:

- The current local test suite remains useful.
- Terraform plan review is not blocked by a runtime migration.
- The repository has a clear stop point before broader API expansion.

Negative:

- TypeScript/shared contracts remain deferred.
- Some Python code may later be migrated or wrapped by a new backend service.
- Parent auth is still represented by the temporary development token until Cognito work is explicitly started.

## Follow-Up

- Review `terraform plan` from the AWS-credentialed machine before any `terraform apply`.
- After the first dev deployment decision, choose one of:
  - Continue hardening the Python minimal Lambda only.
  - Start Cognito-backed parent auth in the existing Lambda.
  - Begin a TypeScript/shared-contract backend slice and migrate deliberately.
- Do not start Windows or Android agent implementation until the backend deployment and runtime boundary are clearer.
