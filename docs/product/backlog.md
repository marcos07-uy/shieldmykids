# Implementation Backlog

## Backlog Policy

This backlog tracks remaining work. The initial documentation baseline is complete, and a minimal backend Lambda/Terraform dev slice has started.

Do not expand implementation beyond the current minimal backend slice or deploy infrastructure without explicit user approval.

## Phase 0 Backlog

- Complete product documentation. Done.
- Complete architecture documentation. Done.
- Complete infrastructure strategy. Done.
- Complete security and privacy documentation. Done.
- Complete agent context files. Done.
- Review documentation with user. In progress.
- Record accepted MVP direction. Done for serverless polling MVP.

## Phase 1 Backend Backlog

1. Select backend runtime and framework. Started with Python Lambda for minimal slice; broader backend choice still needs ADR.
2. Select schema validation approach.
3. Define local development workflow.
4. Create backend project skeleton. Started for minimal Lambda only.
5. Implement health endpoint.
6. Implement Cognito JWT validation.
7. Implement parent account provisioning.
8. Implement family model.
9. Implement child profile APIs.
10. Implement device pairing code APIs. Started.
11. Implement device enrollment. Started.
12. Implement device credential validation. Started.
13. Implement heartbeat endpoint. Started.
14. Implement usage ingestion.
15. Implement idempotency handling.
16. Implement policy storage. Started.
17. Implement policy evaluation.
18. Implement command queue.
19. Implement command acknowledgement.
20. Implement audit events.
21. Implement basic aggregation.
22. Add unit tests.
23. Add authorization tests.

## Phase 2 Dashboard Backlog

1. Select frontend framework and UI stack.
2. Create dashboard skeleton.
3. Implement authentication flow.
4. Implement family overview.
5. Implement child create/edit.
6. Implement child detail.
7. Implement device enrollment screen.
8. Implement policy editor.
9. Implement usage summary.
10. Implement device status.
11. Implement manual lock/unlock.
12. Implement audit log.
13. Add responsive layout.
14. Add accessibility checks.

## Phase 3 Windows Agent Backlog

1. Select Windows agent language and packaging approach.
2. Define service/helper process boundary.
3. Define local queue format.
4. Define local policy cache format.
5. Implement enrollment UI.
6. Implement device credential storage.
7. Implement foreground app tracking.
8. Implement idle detection.
9. Implement usage event batching.
10. Implement heartbeat sync.
11. Implement policy fetch.
12. Implement command polling.
13. Implement warning UI.
14. Implement session lock path.
15. Implement offline behavior.
16. Implement diagnostics.
17. Package installer.

## Phase 4 Android Backlog

1. Select Android language and minimum SDK.
2. Define enrollment screen.
3. Implement Usage Access permission guidance.
4. Implement usage query model.
5. Implement heartbeat sync.
6. Implement usage batching.
7. Implement policy cache.
8. Implement warning notifications.
9. Implement permission revoked detection.
10. Implement local status screen.
11. Implement offline queue.

## Phase 5 Enforcement Backlog

1. Evaluate Windows app block/close strategy.
2. Evaluate AppLocker or Windows policy integration.
3. Evaluate Android Device Owner.
4. Evaluate Android Management API.
5. Add bonus time workflow.
6. Add child request workflow.
7. Add advanced schedule rules.
8. Add app allowlist/blocklist.

## Phase 6 Hardening Backlog

1. Implement Terraform dev environment. Started for minimal backend; not deployed.
2. Implement Terraform prod environment.
3. Add CI for backend.
4. Add CI for dashboard.
5. Add agent build pipelines.
6. Add release versioning.
7. Add operational alarms.
8. Add backup strategy.
9. Add security review checklist.
10. Add cost review checklist.

