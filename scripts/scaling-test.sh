#!/usr/bin/env bash
# Load the deployed app and watch the ECS services auto scale.
#
#   worker: fill the sync queue with fake sync_creator jobs -> worker 0 -> N -> 0
#   api:    hammer /api/health on the ALB with ab            -> api 1 -> N (scales in ~15 min later)
#
# The fake jobs point at an organisation that doesn't exist, so the worker finds
# nothing to sync and just deletes them (no TikTok calls, no data written).
# Prints running/desired tasks, queue depth and firing alarms every 30s.
#
#   aws sso login --profile CAB432
#   scripts/scaling-test.sh            # worker, then api (~25 min)
#   scripts/scaling-test.sh api        # just one of them
#   scripts/scaling-test.sh status     # one status line, no load
#
# Env: TF_DIR (default infra/terraform/envs/cab432), JOBS (600),
#      API_SECONDS (480), CONCURRENCY (50). Needs jq, ab and uuidgen.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
tf_dir="${TF_DIR:-$root/infra/terraform/envs/cab432}"
if (($#)); then parts=("$@"); else parts=(worker api); fi
jobs="${JOBS:-600}"
api_seconds="${API_SECONDS:-480}"
concurrency="${CONCURRENCY:-50}"

out="$(terraform -chdir="$tf_dir" output -json)"
tf() { jq -r "$1" <<<"$out"; }

profile="$(tf .aws_profile.value)"
region="$(tf .aws_region.value)"
cluster="$(tf .ecs_cluster_name.value)"
api="$(tf .ecs_service_names.value.api)"
worker="$(tf .ecs_service_names.value.worker)"
queue_url="$(tf .sync_queue_url.value)"
prefix="${api%-api}"
target="$(tf .domain_url.value)/api/health" # straight to the ALB, not CloudFront

aws() { command aws --profile "$profile" --region "$region" "$@"; }

status() {
  local services queue alarms
  services="$(aws ecs describe-services --cluster "$cluster" --services "$api" "$worker" \
    --query 'services[].[serviceName,runningCount,desiredCount]' --output text |
    awk -v p="$prefix-" '{ sub(p, "", $1); printf "%s %s/%s  ", $1, $2, $3 }')"
  queue="$(aws sqs get-queue-attributes --queue-url "$queue_url" \
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
    --query 'Attributes.[ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible]' \
    --output text | awk '{ printf "queue waiting=%s inflight=%s", $1, $2 }')"
  # Target tracking alarms are named TargetTracking-service/<cluster>/<service>-AlarmHigh-<uuid>
  alarms="$(aws cloudwatch describe-alarms --state-value ALARM \
    --query "MetricAlarms[?contains(AlarmName, '$prefix')].AlarmName" --output text |
    tr '\t' '\n' | sed -E "s#TargetTracking-service/[^/]+/##; s/$prefix-//; s/-[0-9a-f]{8}-.*//" |
    sort -u | tr '\n' ' ')"
  printf '%s  %s %s  ALARM: %s\n' "$(date +%H:%M:%S)" "$services" "$queue" "${alarms:-none}"
}

watch_for() {
  local end=$((SECONDS + $1))
  while ((SECONDS < end)); do
    status
    sleep 30
  done
}

fill_queue() {
  local org sent=0 n entries failed
  org="$(uuidgen | tr '[:upper:]' '[:lower:]')"
  while ((sent < jobs)); do
    n=$((jobs - sent < 10 ? jobs - sent : 10)) # SendMessageBatch takes at most 10
    entries="$(for ((i = 0; i < n; i++)); do
      jq -cn --arg id "$i" --arg org "$org" --arg creator "$(uuidgen | tr '[:upper:]' '[:lower:]')" \
        '{Id: $id, MessageBody: ({type: "sync_creator", organisation_id: $org, creator_id: $creator} | tojson)}'
    done | jq -cs .)"
    failed="$(aws sqs send-message-batch --queue-url "$queue_url" --entries "$entries" \
      --query 'length(Failed || `[]`)' --output text)"
    if ((failed)); then
      echo "SQS rejected $failed jobs" >&2
      exit 1
    fi
    sent=$((sent + n))
  done
  echo "Sent $sent fake jobs"
}

if [[ "${parts[*]}" == status ]]; then
  status
  exit
fi

echo "Tasks shown as running/desired"
echo
echo "== Baseline"
status

for part in "${parts[@]}"; do
  case "$part" in
  worker)
    echo
    echo "== Worker: $jobs jobs on the queue"
    fill_queue
    # ~4 min for the backlog alarm, drain, then 5 idle minutes back to 0
    watch_for 660
    ;;
  api)
    echo
    echo "== API: $concurrency connections for ${api_seconds}s at $target"
    result="$(mktemp)"
    ab -k -q -t "$api_seconds" -n 100000000 -c "$concurrency" "$target" >"$result" 2>&1 &
    load=$!
    watch_for "$api_seconds"
    wait "$load" || true
    grep -E "Complete requests|Failed requests|Requests per second|Time per request.*\(mean\)" "$result"
    rm -f "$result"
    echo
    echo "== After the load (target tracking waits ~15 min before scaling in)"
    watch_for 300
    ;;
  *)
    echo "Unknown part '$part' (worker, api or status)" >&2
    exit 1
    ;;
  esac
done

echo
echo "Done. Scaling history:"
for svc in "$api" "$worker"; do
  aws application-autoscaling describe-scaling-activities --service-namespace ecs \
    --resource-id "service/$cluster/$svc" --max-items 5 \
    --query 'ScalingActivities[].[StartTime,Description]' --output text |
    sed "s/^/  ${svc#"$prefix"-}  /"
done
