#!/usr/bin/env bash
# Shared by the mac and linux scripts, which differ only in name — they are
# kept separate because CLAUDE.md names both, and because a future platform
# difference has somewhere to go.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="http://localhost:8000"
# Generous: the first run builds the frontend and installs both toolchains.
STARTUP_TIMEOUT_SECONDS=300

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required but was not found on PATH." >&2
    echo "Install Docker Desktop: https://docs.docker.com/get-docker/" >&2
    exit 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    echo "This needs Docker Compose v2 ('docker compose', not 'docker-compose')." >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but not running. Start it and try again." >&2
    exit 1
  fi
}

start_prelegal() {
  require_docker
  cd "$REPO_ROOT"

  echo "Building and starting Prelegal…"
  docker compose up --build --detach

  echo -n "Waiting for $URL to come up"
  local waited=0
  until curl --silent --fail "$URL/api/health" >/dev/null 2>&1; do
    if [ "$waited" -ge "$STARTUP_TIMEOUT_SECONDS" ]; then
      echo
      echo "Gave up after ${STARTUP_TIMEOUT_SECONDS}s. Recent logs:" >&2
      docker compose logs --tail 40 >&2
      exit 1
    fi
    sleep 2
    waited=$((waited + 2))
    echo -n "."
  done

  echo
  echo "Prelegal is running at $URL"
}

stop_prelegal() {
  require_docker
  cd "$REPO_ROOT"
  echo "Stopping Prelegal…"
  docker compose down
  echo "Stopped."
}
