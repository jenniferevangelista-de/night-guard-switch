#!/usr/bin/env bash
# Start a local Switch v0.31.0 (Postgres, Mattermost, switch-core, gateway) from its published images.
#
#   scripts/switch-up.sh            clones Switch into ./switch on first run, then starts it
#
# Needs Docker with Compose, git and openssl. Mattermost: http://localhost:8065
set -euo pipefail
SWITCH_VERSION="${SWITCH_VERSION:-0.31.0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$HERE/switch"
if [ ! -d "$DIR" ]; then
  git clone --quiet --depth 1 --branch "switch-v$SWITCH_VERSION" https://github.com/sandbox-quantum/switch "$DIR"
fi
cd "$DIR"
if [ ! -f .env ]; then
  cp .env.example .env
  deploy/local/generate-env-secrets.sh .env local
  sed -i.bak "s|^SWITCH_VERSION=.*|SWITCH_VERSION=$SWITCH_VERSION|" .env
  rm -f .env.bak
fi
docker compose -f deploy/local/standalone-docker-compose.yml --project-directory . \
  --profile collab --profile gateway up -d
echo "Waiting for Switch and Mattermost…"
for _ in $(seq 180); do
  if curl -sf localhost:8000/health >/dev/null && curl -sf localhost:8065/api/v4/system/ping >/dev/null; then
    break
  fi
  sleep 2
done
curl -sf localhost:8000/health >/dev/null || { echo "switch-core did not come up"; docker compose -f deploy/local/standalone-docker-compose.yml --project-directory . logs --tail 80 switch; exit 1; }
for _ in $(seq 90); do
  docker compose -f deploy/local/standalone-docker-compose.yml --project-directory . --profile collab logs setup 2>&1 | grep -qi "complete" && break
  sleep 2
done
echo "Switch is up: API http://localhost:8000, Mattermost http://localhost:8065"
