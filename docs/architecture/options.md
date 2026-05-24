# Architecture Options

## Backend Architecture Options

### Option 1: API Gateway HTTP API + Lambda + DynamoDB

Summary:

- Serverless REST-style API.
- Parent dashboard and device agents call HTTPS endpoints.
- DynamoDB stores families, devices, usage, policies, commands, and audit events.

Pros:

- Very low idle cost.
- Simple deployment model.
- Works well for MVP scale.
- Avoids always-on servers.
- Easy to secure with IAM, Cognito JWT validation, and scoped Lambda permissions.

Cons:

- Device commands require polling.
- Lambda boundaries require careful code organization.
- DynamoDB access patterns must be designed upfront.

Recommendation:

- Use this for MVP.

### Option 2: Lambda + AWS IoT Core + DynamoDB

Summary:

- Child agents connect over MQTT.
- Commands and policy updates can be pushed more directly.
- Device identity can use IoT certificates.

Pros:

- Better real-time device communication.
- MQTT is a natural fit for agents.
- Device Shadows can represent desired/reported device state.

Cons:

- More AWS concepts.
- More infrastructure.
- More complex local development.
- Cost model is still low but less obvious.

Recommendation:

- Add later if polling creates poor UX or command latency.

### Option 3: AppSync + DynamoDB

Summary:

- GraphQL API for dashboard and possible subscriptions.

Pros:

- Good dashboard integration.
- Strong typed API model.
- Realtime subscriptions for parent UI.

Cons:

- Device agents benefit less from GraphQL.
- Resolver complexity can grow.
- Adds learning curve.

Recommendation:

- Do not use for MVP.

### Option 4: Container Backend

Summary:

- API service deployed to ECS Fargate, App Runner, or similar.

Pros:

- Familiar long-running API service model.
- Easier request lifecycle for some teams.
- Simpler local parity.

Cons:

- Higher idle cost.
- More operational responsibility.
- Less aligned with cheapest-serverless requirement.

Recommendation:

- Avoid for MVP.

## Windows Options

### W1: User-Mode App Only

Pros:

- Fastest to build.
- No service installer.
- Easier debugging.

Cons:

- Weak persistence.
- Easy to close or bypass.
- Poor enforcement after reboot.

Verdict:

- Acceptable only for a prototype, not the MVP.

### W2: Windows Service With Admin Install

Pros:

- Starts on boot.
- Better persistence.
- Can sync and maintain local state.
- Works with a visible helper/tray process for child transparency.

Cons:

- Requires admin install.
- Requires installer.
- Interactive user actions may need a per-user process.

Verdict:

- Recommended Windows MVP.

### W3: Service Plus OS-Level Policies

Pros:

- Stronger app restrictions.
- Can integrate with Windows-native controls.

Cons:

- Windows edition and account-type differences.
- More testing required.
- Higher risk of locking users out incorrectly.

Verdict:

- Later hardening phase.

## Android Options

### A1: Standard App With Usage Access

Pros:

- Consumer-friendly.
- No factory reset.
- Simple setup.
- Can report app usage with user-granted permission.

Cons:

- Permission can be revoked.
- Enforcement is weak.
- Background restrictions vary by Android version and vendor.

Verdict:

- Recommended Android MVP for monitoring.

### A2: Device Owner App

Pros:

- Stronger controls.
- Better enforcement.
- Appropriate for fully managed child devices.

Cons:

- Enrollment friction.
- Often requires factory reset or special provisioning.
- Harder for normal family setup.

Verdict:

- Later enforcement path.

### A3: Android Management API

Pros:

- Mature Android Enterprise management model.
- Cloud-managed policies.
- Strong restrictions.

Cons:

- Enterprise-style setup.
- May not fit casual family-owned devices.
- More account and enrollment complexity.

Verdict:

- Evaluate after MVP if strong Android enforcement becomes critical.

## Final Recommendation

Use:

- API Gateway HTTP API.
- Lambda.
- DynamoDB.
- Cognito.
- Static web hosting.
- Windows service plus visible helper.
- Android Usage Access monitoring.
- Polling device protocol.

Add later:

- AWS IoT Core.
- Windows OS policy integration.
- Android Device Owner or Android Management API.

