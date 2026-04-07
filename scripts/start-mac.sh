#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="pm-mvp:local"
CONTAINER_NAME="pm-mvp"
HOST_PORT="${PORT:-8000}"

cd "${ROOT_DIR}"

echo "Building Docker image ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" .

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
  echo "Removing existing container ${CONTAINER_NAME}..."
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

echo "Starting container ${CONTAINER_NAME} on port ${HOST_PORT}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --env-file "${ROOT_DIR}/.env" \
  -p "${HOST_PORT}:8000" \
  "${IMAGE_NAME}" >/dev/null

echo "App is starting. Open http://localhost:${HOST_PORT}"
