# Claude Context

This repository has completed the initial Phase 0 documentation baseline and now contains a narrow Phase 1 minimal backend slice.

## Repository

- Local path: `/home/marcos/shared/repos/shieldMyKids`
- GitHub SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- GitHub web URL: `https://github.com/marcos07-uy/shieldmykids`
- Default branch: `main`

Follow [AGENTS.md](AGENTS.md), [CODEX.md](CODEX.md), and [docs/agent-context/codex-context.md](docs/agent-context/codex-context.md).

Existing implementation is limited to the minimal backend Lambda and Terraform dev environment already present in the repository.

Do not expand implementation beyond that slice, deploy infrastructure, or mutate AWS resources unless the user explicitly approves it.

The current recommended architecture is:

- AWS serverless backend.
- Terraform-managed infrastructure for the current dev backend slice.
- Cognito for parent auth.
- API Gateway HTTP API and Lambda for APIs.
- DynamoDB for data.
- Static parent dashboard hosting.
- Windows service plus visible helper for the Windows agent.
- Android monitoring-first app using Usage Access.
- Device polling for MVP.

Non-negotiable safety rules:

- No keylogging.
- No hidden screenshots.
- No covert microphone or camera access.
- No hidden installation.
- No credential theft.
- No spyware-like behavior.

