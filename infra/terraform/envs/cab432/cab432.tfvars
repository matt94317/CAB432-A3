# CAB432 shared account. The account blocks creating IAM roles, security
# groups and RDS, so those are reused (see infra/README.md).

aws_profile  = "CAB432"
aws_region   = "ap-southeast-2"
account_id   = "901444280953"
name_prefix  = "n12191434-a3-hookd"
qut_username = "n12191434@qut.edu.au"
purpose      = "assessment 3"

# Shared VPC
vpc_id             = "vpc-007bab53289655834"
public_subnet_ids  = ["subnet-05a3b8177138c8b14", "subnet-075811427d5564cf9", "subnet-04ca053dcbe5f49cc"]
private_subnet_ids = ["subnet-04cc288ea3b2e1e53", "subnet-08e89ff0d9b49c9ae", "subnet-05d0352bb15852524"]

# CAB432SG: 80, 443, 8080, 3000-3010 from anywhere
alb_security_group_ids     = ["sg-032bd1ff8cf77dbb9"]
service_security_group_ids = ["sg-032bd1ff8cf77dbb9"]

# CAB432MemcachedSG: 11211 from CAB432SG. 6379 is open nowhere, so Valkey runs on 11211.
cache_security_group_ids = ["sg-07707a36aa1599475"]
cache_port               = 11211

# Reused (can't create these here)
existing_ecs_cluster_name     = "n12191434-a2-cluster"
existing_cognito_user_pool_id = "ap-southeast-2_ZvcLlofqW"
task_role_arn                 = "arn:aws:iam::901444280953:role/Task-Role-CAB432-ECS"
execution_role_arn            = "arn:aws:iam::901444280953:role/Execution-Role-CAB432-ECS"
scheduler_role_arn            = "arn:aws:iam::901444280953:role/CAB432-EventBridge-scheduler-Role"

# Domain
domain_name     = "n12191434.cab432.com"
zone_name       = "cab432.com"
certificate_arn = "arn:aws:acm:ap-southeast-2:901444280953:certificate/dd11cb64-3e67-466f-b78c-441aab10e389"
# The A2 API Gateway alias still owns n12191434.cab432.com; set true to take it over
dns_allow_overwrite = false

enable_cloudfront = true
tiktok_mode       = "mock"
