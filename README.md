# Shield My Kids

Shield My Kids is a personal parental-control and family screen-time management project.

The project has completed the initial documentation baseline and is moving into the first implementation slice.

## Repository

- GitHub: [https://github.com/marcos07-uy/shieldmykids](https://github.com/marcos07-uy/shieldmykids)
- SSH remote: `git@github.com:marcos07-uy/shieldmykids.git`
- Default branch: `main`

## Current Status

- Product strategy: drafted in [codex.md](codex.md)
- Phase 0 documentation: complete
- Minimal backend infrastructure: started
- Production application and agents: not started

## Documentation Map

- [Product vision](docs/product/vision.md)
- [Functional requirements](docs/product/functional-requirements.md)
- [Roadmap](docs/product/roadmap.md)
- [Architecture overview](docs/architecture/overview.md)
- [Architecture options](docs/architecture/options.md)
- [Data model](docs/architecture/data-model.md)
- [API contract](docs/architecture/api-contract.md)
- [Terraform strategy](docs/infrastructure/terraform-strategy.md)
- [AWS cost model](docs/infrastructure/aws-cost-model.md)
- [Threat model](docs/security/threat-model.md)
- [Privacy principles](docs/security/privacy.md)
- [Operations runbook](docs/operations/runbook.md)
- [Agent context](docs/agent-context/codex-context.md)
- [Terraform](infrastructure/terraform/README.md)

## Current Implementation Boundary

The first implementation slice is limited to the minimal backend needed to:

- Store or update a child policy.
- Create a short-lived pairing code.
- Enroll a device.
- Accept device heartbeats and raw usage event batches.
- Return an empty authenticated device command list for the polling contract.
- Return a basic parent usage summary from raw usage events.
- Let that device fetch its current effective policy.

Parent authentication is temporarily represented by a development header token. Cognito remains the intended production parent authentication path.

## Ethical Boundary

Shield My Kids must be designed as a transparent parental-control product, not as covert monitoring software.

The system must not include:

- Keylogging.
- Hidden screen capture.
- Covert camera or microphone access.
- Credential capture.
- Hidden installation.
- Attempts to bypass operating-system security controls.

Child devices must clearly show that monitoring and policy enforcement are enabled.
