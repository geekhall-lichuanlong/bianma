#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/qianyi"
cd "$BASE_DIR"

echo "== qianyi one-click start =="
echo "Base: $BASE_DIR"

# Start from a clean project state so re-running run.sh is predictable.
if [[ -x "$BASE_DIR/kill.sh" ]]; then
  "$BASE_DIR/kill.sh" --quiet || true
else
  bash "$BASE_DIR/kill.sh" --quiet || true
fi

start_script() {
  local name="$1"
  local script="$2"

  if [[ ! -f "$script" ]]; then
    echo "ERROR: missing $name script: $script" >&2
    return 1
  fi

  echo "Starting $name: $script"
  bash "$script"
}

start_script "surgery" "$BASE_DIR/4090/s.sh"
start_script "disease" "$BASE_DIR/3090/run.sh"

echo
echo "Started tmux sessions:"
tmux ls 2>/dev/null | grep -E '^(sagent1|sagent2|sagent3|sagent4|no_surgery_screening|no_surgery_name|surgery_reason|sicd|ocr|elastic|kibana|qy_backend|qy_web|agent1|agent2|agent3|agent4|agent_external|dicd|disease_reason):' || true

echo
echo "Use: tmux attach -t <session> to inspect logs."
echo "Use: $BASE_DIR/kill.sh to stop all qianyi services."
