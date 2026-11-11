#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/qianyi"
SCRIPT="$BASE_DIR/4090/run/run_surgery.sh"

if [[ ! -f "$SCRIPT" ]]; then
  echo "ERROR: missing surgery startup script: $SCRIPT" >&2
  exit 1
fi

# Detached orchestrator: the old -A form attached to tmux and blocked top-level run.sh,
# so disease services in 3090/run.sh never started.
tmux has-session -t surgery 2>/dev/null && tmux kill-session -t surgery || true
tmux new-session -d -s surgery "bash -lc 'bash "$SCRIPT"; echo surgery bootstrap finished; exec bash'"

echo "surgery bootstrap session started"
