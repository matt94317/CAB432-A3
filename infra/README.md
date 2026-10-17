# Infrastructure

Infrastructure as code for AWS (plan section 9): VPC, RDS, ElastiCache, Cognito, SQS + DLQ,
EventBridge Scheduler, ECR, ECS Fargate services (api, worker, mcp), ALB, CloudFront + S3,
Route 53, ACM, Secrets Manager, CloudWatch alarms and autoscaling policies.

Tool not chosen yet (Terraform or AWS CDK Python). Put the code in `infra/terraform/` or `infra/cdk/`.

`local/` holds config for local development only (docker compose).
