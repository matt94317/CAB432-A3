#!/usr/bin/env bash
# Regenerate apps/web/src/api/schema.d.ts from the running FastAPI OpenAPI schema.
set -euo pipefail
npm run gen:api -w apps/web
