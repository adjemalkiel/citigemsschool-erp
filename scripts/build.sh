#!/usr/bin/env bash
# Build citigems/erpnext:16
# Default: lightweight extend of frappe/erpnext:v16 (safer on ~8GB RAM).
#   ./scripts/build.sh
# Full layered bench init (needs more RAM; reduce parallelism if OOM):
#   ./scripts/build.sh --layered
# Also exports APPS_JSON_BASE64 for docs/compat (BuildKit secret is used for the build).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_docker_env.sh"

LAYERED=0
NO_CACHE=()
for arg in "$@"; do
  case "$arg" in
    --layered) LAYERED=1 ;;
    --no-cache) NO_CACHE=(--no-cache) ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
  esac
done

APPS_JSON="${ROOT}/apps.json"
if [[ ! -f "${APPS_JSON}" ]]; then
  echo "Missing ${APPS_JSON}" >&2
  exit 1
fi

# Compat: write base64 (gitignored) for older docs / CI that expect APPS_JSON_BASE64
APPS_JSON_BASE64="$(base64 -w0 < "${APPS_JSON}")"
export APPS_JSON_BASE64
printf '%s' "${APPS_JSON_BASE64}" > "${ROOT}/apps.json.b64"
echo "APPS_JSON_BASE64 written to apps.json.b64 (gitignored)"

# shellcheck disable=SC1090
set -a; source "${ENV_FILE}"; set +a
IMAGE="${CUSTOM_IMAGE:-citigems/erpnext}:${CUSTOM_TAG:-16}"

# Reduce BuildKit / yarn parallelism on small hosts
export DOCKER_BUILDKIT=1
export BUILDKIT_STEP_LOG_MAX_SIZE=10485760

if [[ "${LAYERED}" -eq 1 ]]; then
  echo "Building LAYERED image ${IMAGE} (FRAPPE_BRANCH=version-16) ..."
  echo "If the build OOMs, re-run without --layered (default extend build) or close other apps."
  docker build \
    "${NO_CACHE[@]}" \
    --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
    --build-arg=FRAPPE_BRANCH=version-16 \
    --build-arg=FRAPPE_IMAGE_PREFIX=frappe \
    --secret=id=apps_json,src="${APPS_JSON}" \
    --tag="${IMAGE}" \
    --file="${DOCKER_DIR}/images/layered/Containerfile" \
    "${DOCKER_DIR}"
else
  echo "Building lightweight (extend) image ${IMAGE} from frappe/erpnext:v16 ..."
  # Ensure base is present
  docker pull frappe/erpnext:v16
  docker build \
    "${NO_CACHE[@]}" \
    --build-arg=BASE_IMAGE=frappe/erpnext:v16 \
    --secret=id=apps_json,src="${APPS_JSON}" \
    --tag="${IMAGE}" \
    --file="${DOCKER_DIR}/Containerfile.citigems" \
    "${DOCKER_DIR}"
fi

echo "Built ${IMAGE}"
docker images "${CUSTOM_IMAGE:-citigems/erpnext}" --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.ID}}'
