#!/usr/bin/env bash
# Start Citigems ERPNext stack and wait for create-site.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_docker_env.sh"
# shellcheck disable=SC1090
set -a; source "${ENV_FILE}"; set +a

IMAGE="${CUSTOM_IMAGE:-citigems/erpnext}:${CUSTOM_TAG:-15}"
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "Image ${IMAGE} not found locally on this Docker host. Run ./scripts/build.sh first." >&2
  exit 1
fi

echo "Starting compose project '${PROJECT_NAME}' (HTTP :${HTTP_PUBLISH_PORT:-8080}) ..."
compose up -d

echo "Waiting for create-site to finish ..."
# create-site is a oneshot; wait until exited
for i in $(seq 1 180); do
  status="$(compose ps -a --format '{{.Service}} {{.Status}}' | awk '/^create-site /{print; exit}')" || true
  if echo "${status}" | grep -qi 'exited (0)'; then
    echo "create-site completed successfully."
    break
  fi
  if echo "${status}" | grep -qiE 'exited \([1-9]'; then
    echo "create-site failed: ${status}" >&2
    compose logs create-site | tail -80 >&2
    exit 1
  fi
  if [[ "$i" -eq 180 ]]; then
    echo "Timed out waiting for create-site. Current: ${status:-unknown}" >&2
    compose logs create-site | tail -80 >&2
    exit 1
  fi
  sleep 10
done

compose ps
SITE="${SITE_NAME:-citigems.localhost}"
PORT="${HTTP_PUBLISH_PORT:-8080}"
echo ""
echo "Site:     http://${SITE}:${PORT}/  (or http://127.0.0.1:${PORT}/ with Host header)"
echo "Admin:    Administrator / (see secrets/admin_password.txt or docker/.env ADMIN_PASSWORD)"
echo "Add hosts: echo '127.0.0.1 ${SITE}' | sudo tee -a /etc/hosts"
