#!/usr/bin/env bash
# The whole thing in one go: Switch up, family and agents set up, family-helper running,
# then the end-to-end check plays the parents. Transcript in out/transcript.md.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"
scripts/switch-up.sh
python -m pip install -q -e .
SWITCH_ENV=switch/.env python -m family_room.setup
mkdir -p out
python -m family_room.helper > out/helper.log 2>&1 &
HELPER=$!
trap 'kill $HELPER 2>/dev/null || true' EXIT
sleep 4
python -m family_room.e2e
