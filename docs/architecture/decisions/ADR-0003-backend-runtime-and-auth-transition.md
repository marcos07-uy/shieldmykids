# ADR-0003: Backend Runtime And Auth Transition

## Status

Accepted for the narrow Phase 1 minimal backend slice.

## Context

The Phase 1 minimal backend slice currently uses a Python Lambda behind API Gateway HTTP API. It supports the narrow development workflow for pairing codes, policy storage, device enrollment, device heartbeat, usage event ingestion, usage summary, command polling, manual lock/unlock command queueing, command acknowledgements, audit event recording, audit event listing, and device policy fetch.

The broader product direction prefers TypeScript for backend and shared contracts, but replacing the current Lambda immediately would slow validation of the existing minimal slice.

Parent authentication is currently represented by `X-Dev-Parent-Token`. That header is a development-only placeholder and is not acceptable for a parent dashboard or deployed family use.

## Decision

Keep the current Python minimal API Lambda for the existing Phase 1 slice while it remains limited to:

- Creating short-lived pairing codes.
- Storing or updating a child policy.
- Enrolling a device with a pairing code.
- Accepting device heartbeats.
- Accepting raw usage events.
- Returning a basic parent usage summary.
- Queueing manual lock/unlock commands.
- Returning and acknowledging device commands.
- Recording and listing audit events.
- Returning the current policy to an enrolled device.

Before expanding the backend beyond this slice, make a separate implementation decision for the broader backend runtime and shared contract strategy. The preferred direction remains TypeScript for backend services and shared API contracts unless a later ADR changes that.

Keep `X-Dev-Parent-Token` only as a local and dev-review mechanism. Replace parent authentication with Cognito JWT validation before any real parent dashboard workflow, multi-family data access, or family-usable deployment.

Do not run `terraform apply` or mutate AWS resources until a Terraform plan has been reviewed and the user explicitly approves deployment.

## Rationale

This keeps the current working backend slice testable without a runtime migration that does not yet add user value.

It also prevents the temporary development auth path from becoming product architecture by accident. Parent identity, family ownership checks, and audit-sensitive changes need Cognito-backed authorization before the API is used outside controlled development.

## Consequences

Positive:

- Preserves momentum on the validated minimal slice.
- Avoids rewriting working code before the backend contract is stable.
- Keeps the long-term TypeScript/shared-contract direction explicit.
- Makes the temporary parent token boundary clear.

Negative:

- The repository temporarily contains Python backend code while the preferred broader direction is TypeScript.
- A later migration or service split may be needed if the backend expands beyond the current Lambda slice.
- Cognito integration remains deferred and must be completed before real parent use.

## Follow-Up

- Review Terraform plan output before any deployment.
- Decide the broader backend runtime and shared-contract approach before adding substantial new backend APIs.
- Replace `X-Dev-Parent-Token` with Cognito JWT validation before dashboard integration or family-usable deployment.
- Add authorization tests when Cognito-backed parent APIs are implemented.
