#!/usr/bin/env bash
# Shared docker/compose helpers for Citigems stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="${ROOT}/docker"
ENV_FILE="${DOCKER_DIR}/.env"
COMPOSE_FILE="${DOCKER_DIR}/pwd.yml"
BIND_OVERRIDE="${DOCKER_DIR}/compose.bind-citigems-custom.yaml"
BIND_OVERRIDE_REMOTE="${DOCKER_DIR}/compose.bind-citigems-custom.remote.yaml"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-citigems}"
USING_REMOTE_DOCKER=0

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy docker/.env.example to docker/.env and set secrets." >&2
  exit 1
fi

# Prefer local docker socket; fall back to DOCKER_HOST from env or .env
if [[ -z "${DOCKER_HOST:-}" ]]; then
  if docker info >/dev/null 2>&1; then
    :
  elif grep -qE '^DOCKER_HOST=' "${ENV_FILE}" 2>/dev/null; then
    # shellcheck disable=SC1090
    set -a; source "${ENV_FILE}"; set +a
    USING_REMOTE_DOCKER=1
  elif docker -H ssh://devops-docker info >/dev/null 2>&1; then
    export DOCKER_HOST=ssh://devops-docker
    USING_REMOTE_DOCKER=1
    echo "NOTE: local docker socket unavailable; using DOCKER_HOST=${DOCKER_HOST}" >&2
    echo "Add this user to the docker group for a true local stack:" >&2
    echo "  sudo usermod -aG docker \$USER && newgrp docker" >&2
  else
    echo "Cannot reach Docker. Add user to docker group, then re-login:" >&2
    echo "  sudo usermod -aG docker \$USER && newgrp docker" >&2
    exit 1
  fi
else
  USING_REMOTE_DOCKER=1
fi

compose() {
  local args=(--env-file "${ENV_FILE}" -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}")
  # Local Docker: relative bind from this workspace. Remote Docker: absolute path on remote host
  # (rsync apps/citigems_custom to /home/devopserp/citigemsschool-erp/apps/ first).
  if [[ "${USING_REMOTE_DOCKER}" -eq 0 ]] && [[ -d "${ROOT}/apps/citigems_custom" ]] && [[ -f "${BIND_OVERRIDE}" ]]; then
    args+=(-f "${BIND_OVERRIDE}")
  elif [[ "${USING_REMOTE_DOCKER}" -eq 1 ]] && [[ -f "${BIND_OVERRIDE_REMOTE}" ]]; then
    args+=(-f "${BIND_OVERRIDE_REMOTE}")
  fi
  docker compose "${args[@]}" "$@"
}

export ROOT DOCKER_DIR ENV_FILE COMPOSE_FILE PROJECT_NAME USING_REMOTE_DOCKER
