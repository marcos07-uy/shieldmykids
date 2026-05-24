# AWS Cost Model

## Cost Principles

The infrastructure should remain near zero or very low while idle.

Avoid MVP services with meaningful fixed monthly cost:

- NAT Gateway.
- RDS.
- ECS services.
- EKS.
- Always-on EC2.
- Always-on Fargate.

Prefer pay-per-use:

- Lambda.
- API Gateway HTTP API.
- DynamoDB on-demand.
- S3.
- CloudFront.
- SES.
- EventBridge.

## Assumptions

MVP polling assumptions:

- Device heartbeat every 5 minutes.
- Device command polling included in heartbeat or adjacent request.
- Usage events batched.
- Parent dashboard usage is light.
- Logs are retained for a limited period.
- No AWS IoT Core in MVP.

## Scale Estimate

### 1 Family, 5 Devices

Approximate monthly API calls:

- 5 devices.
- 12 polls per hour.
- 24 hours per day.
- 30 days.
- About 43,200 heartbeat calls per month.
- Usage event batches add a smaller number of requests.

Expected cost:

- Likely $0 to $5/month, depending on logs, hosting, and free-tier eligibility.

### 100 Families, 500 Devices

Approximate monthly API calls:

- 500 devices.
- 12 polls per hour.
- 24 hours per day.
- 30 days.
- About 4.32 million heartbeat calls per month.
- Additional usage ingestion and dashboard calls.

Expected cost:

- Likely $10 to $60/month for MVP patterns, depending on API volume, DynamoDB writes, CloudWatch logs, and free-tier status.

## Major Cost Drivers

API Gateway:

- Request count.
- HTTP API is preferred over REST API for lower cost.

Lambda:

- Invocation count.
- Duration.
- Memory allocation.

DynamoDB:

- Write request units.
- Read request units.
- Storage.
- Streams if enabled later.

CloudWatch:

- Log ingestion.
- Log retention.

Hosting:

- CloudFront bandwidth.
- S3 storage and requests.
- Amplify build minutes if used.

SES:

- Email volume.

## Cost Controls

Required:

- AWS Budget alert.
- Log retention set explicitly.
- Batch usage events.
- Avoid overly frequent polling.
- Use DynamoDB TTL for temporary records.
- Avoid NAT Gateway.

Recommended:

- Start with 5-minute polling.
- Increase polling frequency only for devices actively nearing or exceeding limits.
- Use dashboard refresh sparingly.
- Monitor CloudWatch log volume early.

## Future IoT Core Cost Consideration

AWS IoT Core may be worthwhile later for real-time command delivery.

Before adding it, estimate:

- MQTT connection minutes.
- Message volume.
- Rules engine actions.
- Device Shadow operations if used.

Decision trigger:

- Manual lock/unlock latency is unacceptable with polling.
- Number of devices grows enough that polling becomes inefficient.
- Device state synchronization becomes complex.

