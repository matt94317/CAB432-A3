#!/usr/bin/env bash
# Regenerate apps/web/src/api/schema.d.ts from the FastAPI app (no server needed).
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
uv run python scripts/export_openapi.py "$tmp/openapi.json"
npx --workspace apps/web openapi-typescript "$tmp/openapi.json" -o "$root/apps/web/src/api/schema.d.ts"
