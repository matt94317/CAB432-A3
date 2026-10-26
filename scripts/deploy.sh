#!/usr/bin/env bash
# Build images for linux/arm64, push them to ECR and roll the ECS services.
# Names come from `terraform output`, so run `terraform apply` first.
#
#   aws sso login --profile CAB432
#   scripts/deploy.sh              # all services
#   scripts/deploy.sh api web      # just these
#
# Env: TF_DIR (default infra/terraform/envs/cab432), IMAGE_TAG (default latest).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tf_dir="${TF_DIR:-$root/infra/terraform/envs/cab432}"
tag="${IMAGE_TAG:-latest}"
if (($#)); then services=("$@"); else services=(api worker mcp web); fi

out="$(terraform -chdir="$tf_dir" output -json)"
tf() { jq -r "$1" <<<"$out"; }

profile="$(tf .aws_profile.value)"
region="$(tf .aws_region.value)"
cluster="$(tf .ecs_cluster_name.value)"
registry="$(tf .ecr_repository_urls.value.api)"
registry="${registry%%/*}"
sha="$(git -C "$root" rev-parse --short HEAD)"

aws() { command aws --profile "$profile" --region "$region" "$@"; }

echo "Logging in to $registry"
aws ecr get-login-password | docker login --username AWS --password-stdin "$registry"

for svc in "${services[@]}"; do
  repo="$(tf ".ecr_repository_urls.value.$svc")"
  args=()
  if [[ "$svc" == web ]]; then
    # Vite bakes these into the bundle; /api stays same-origin
    args+=(--build-arg "VITE_COGNITO_USER_POOL_ID=$(tf .cognito_user_pool_id.value)")
    args+=(--build-arg "VITE_COGNITO_APP_CLIENT_ID=$(tf .cognito_client_id.value)")
    # Stock photos go with mock data only, never with real creators
    if [[ "$(tf .tiktok_mode.value)" == mock ]]; then
      args+=(--build-arg "VITE_DEMO_IMAGES=true")
    fi
  fi

  echo "Building $svc -> $repo:$tag"
  docker buildx build \
    --platform linux/arm64 \
    -f "$root/apps/$svc/Dockerfile" \
    -t "$repo:$tag" -t "$repo:$sha" \
    ${args[@]+"${args[@]}"} \
    --push "$root"
done

for svc in "${services[@]}"; do
  name="$(tf ".ecs_service_names.value.$svc")"
  echo "Redeploying $name"
  aws ecs update-service --cluster "$cluster" --service "$name" \
    --force-new-deployment --query 'service.serviceName' --output text
done

echo "Done. App: $(tf .app_url.value)"
