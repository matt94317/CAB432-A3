#!/usr/bin/env bash
# Build the Gradescope A3 submission: submission/{app/,submission-a3-infra.yml} and submission.zip.
# app/ is the tracked git files plus untracked non-ignored ones, so .env, node_modules,
# .venv, .terraform and state files are left out.
set -euo pipefail
cd "$(dirname "$0")/.."

out=submission
rm -rf "$out" submission.zip
mkdir -p "$out/app"

git ls-files -z --cached --others --exclude-standard \
  | grep -zv -e '^submission-a3-infra\.yml$' -e '\.tsbuildinfo$' -e '^\.github/' -e '^\.claude/' \
  | rsync -a --from0 --files-from=- ./ "$out/app/"

cp submission-a3-infra.yml "$out/"
(cd "$out" && zip -qr ../submission.zip . -x '*.DS_Store')

echo "app files: $(find "$out/app" -type f | wc -l)"
echo "zip: $(du -h submission.zip | cut -f1)"
