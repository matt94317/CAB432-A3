# Infrastructure

Infrastructure as code for AWS (plan section 9): VPC, RDS, ElastiCache, Cognito, SQS + DLQ,
EventBridge Scheduler, ECR, ECS Fargate services (api, worker, mcp), ALB, CloudFront + S3,
Route 53, ACM, Secrets Manager, CloudWatch alarms and autoscaling policies.

Tool not chosen yet (Terraform or AWS CDK Python). Put the code in `infra/terraform/` or `infra/cdk/`.

`local/` holds config for local development only (docker compose).

## Cognito (Epic 1: Account)

Until the IaC is written, create the user pool with the AWS CLI. The app expects
email sign-in, a required `name` attribute, and a public app client (no secret)
using SRP with token revocation on.

```bash
aws cognito-idp create-user-pool \
  --pool-name hookd-tracker \
  --username-attributes email \
  --auto-verified-attributes email \
  --schema Name=name,AttributeDataType=String,Required=true,Mutable=true \
  --policies 'PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}' \
  --query UserPool.Id --output text

aws cognito-idp create-user-pool-client \
  --user-pool-id <pool-id> \
  --client-name hookd-web \
  --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --enable-token-revocation \
  --prevent-user-existence-errors ENABLED \
  --access-token-validity 60 --id-token-validity 60 --refresh-token-validity 30 \
  --token-validity-units AccessToken=minutes,IdToken=minutes,RefreshToken=days \
  --query UserPoolClient.ClientId --output text
```

Put the two IDs in `.env` (`COGNITO_*`, for the API) and `apps/web/.env` (`VITE_COGNITO_*`).

Sessions: access tokens last 60 minutes and are refreshed silently; the refresh
token keeps a manager signed in for 30 days. Logging out revokes the refresh token.
