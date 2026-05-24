# Roadmap

## Phase 0: Documentation And Planning

Status: complete as the initial documentation baseline.

Goal: establish the product, architecture, security, infrastructure, and delivery plan before implementation.

Deliverables:

- Product vision.
- Functional requirements.
- Architecture overview.
- Architecture option comparison.
- Data model.
- API contract.
- Terraform strategy.
- Cost model.
- Security threat model.
- Privacy document.
- Operations runbook.
- Agent guidance files.
- Architecture decision records.

Exit criteria:

- Documentation reviewed.
- MVP direction approved.
- Terraform strategy accepted.
- Security constraints accepted.
- Initial backlog accepted.

Originally out of scope:

- Application code.
- Backend code.
- Agent code.
- Terraform implementation.
- CI/CD implementation.

Current note:

- The repository now contains a narrow minimal backend Lambda and Terraform dev environment for the first implementation slice.
- Wider application, agent, production infrastructure, and CI/CD implementation remain out of scope until explicitly approved.

## Phase 1: Backend MVP

Status: started, limited to the minimal backend slice.

Goal: create the minimum backend required for family, child, device, policy, and usage workflows.

Deliverables:

- Minimal backend Lambda for pairing code, policy, enrollment, and policy fetch workflows. Started.
- Terraform dev environment for the minimal backend. Started, not deployed.
- Local backend skeleton.
- Auth integration. Deferred; dev parent token is temporary.
- Child profile APIs.
- Device enrollment APIs.
- Device heartbeat APIs.
- Usage ingestion APIs.
- Policy storage.
- Command queue.
- Audit events.
- Local test fixtures.

Key decisions before continuing beyond the minimal slice:

- Runtime and framework.
- DynamoDB table design.
- API validation library.
- Local development approach.
- Test strategy.

## Phase 2: Parent Dashboard MVP

Goal: provide a usable parent interface.

Deliverables:

- Login/signup.
- Family overview.
- Child detail page.
- Device enrollment page.
- Policy settings.
- Usage summary.
- Device status.
- Manual lock/unlock.
- Audit log.

## Phase 3: Windows Agent MVP

Goal: deliver the first enforceable child-device agent.

Deliverables:

- Installer plan.
- Windows service.
- Visible tray/status process.
- Enrollment UI.
- Foreground app tracker.
- Idle detector.
- Local queue.
- Policy cache.
- Backend sync.
- Warning UI.
- Session lock behavior.

## Phase 4: Android Monitoring MVP

Goal: add Android usage visibility with transparent limitations.

Deliverables:

- Android app skeleton.
- Enrollment flow.
- Usage Access permission flow.
- Usage reporting.
- Policy cache.
- Local status.
- Warning notifications.
- Offline queue.

## Phase 5: Enforcement Improvements

Goal: strengthen policy enforcement without crossing ethical or OS security boundaries.

Potential deliverables:

- Windows app block/close behavior.
- Windows OS policy integration.
- Android Device Owner prototype.
- Android Management API evaluation.
- More robust bonus time.
- Child request workflow.
- Better offline reconciliation.

## Phase 6: Packaging, CI/CD, And Hardening

Goal: make the system maintainable and repeatable.

Deliverables:

- Terraform dev environment.
- Terraform prod environment.
- GitHub Actions.
- Release packaging.
- Windows installer signing plan.
- Android release process.
- Security review checklist.
- Backup and recovery plan.
- Cost alarms.

## Prioritized Backlog

1. Keep documentation synchronized with the current implementation boundary.
2. Initialize source control and commit the documentation plus minimal backend baseline.
3. Install Terraform or use a toolchain with Terraform available.
4. Run `terraform fmt`, `terraform init`, `terraform validate`, and `terraform plan` for the dev environment.
5. Review the Terraform plan before any deployment.
6. Add focused tests for the minimal Lambda handler.
7. Create implementation ADRs for backend runtime and authentication transition.
8. Replace temporary parent token auth with Cognito when approved.
9. Implement remaining backend MVP APIs.
10. Implement usage ingestion.
11. Implement policy evaluation.
12. Implement command polling.
13. Implement dashboard MVP.
14. Implement Windows agent MVP.
15. Implement Android monitoring MVP.
16. Add production Terraform, CI/CD, and hardening.

