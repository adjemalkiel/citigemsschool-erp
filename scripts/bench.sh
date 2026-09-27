#!/usr/bin/env bash
# Run bench in the backend container.
#   ./scripts/bench.sh --site citigems.localhost list-apps
#   ./scripts/bench.sh console
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_docker_env.sh"

if [[ $# -eq 0 ]]; then
  compose exec backend bench --help
  exit 0
fi

compose exec backend bench "$@"
