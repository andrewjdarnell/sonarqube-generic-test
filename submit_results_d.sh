#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not in PATH." >&2
  exit 1
fi

if [[ ! -f ".env" ]]; then
  echo "Error: .env not found in $SCRIPT_DIR" >&2
  echo "Create .env with SONAR_TOKEN=<your_token> or use the Keychain approach." >&2
  exit 1
fi

docker run --rm \
  --env-file .env \
  -v "$PWD:/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=http://host.docker.internal:9000 \
  "$@"
