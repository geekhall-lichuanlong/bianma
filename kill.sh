#!/usr/bin/env bash
set -u -o pipefail

QUIET=0
if [[ "${1:-}" == "--quiet" ]]; then
  QUIET=1
fi

log() {
  if [[ "$QUIET" != "1" ]]; then
    echo "$@"
  fi
}

BASE_DIR="/opt/qianyi"
SESSIONS=(
  surgery
  no_surgery_v2_20261020_113250
  sagent1 sagent2 sagent3 sagent4 no_surgery_screening no_surgery_name surgery_reason sicd ocr
  elastic kibana qy_backend qy_web agent1 agent2 agent3 agent4 agent_external dicd disease_reason
)

# Never kill this script, its caller, or the SSH/bash parent chain. This matters when
# kill.sh is invoked from run.sh or from a non-interactive SSH command whose command line
# contains the same text patterns we use for cleanup.
declare -A PROTECTED_PIDS=()
pid="$$"
while [[ -n "$pid" && "$pid" != "0" ]]; do
  PROTECTED_PIDS["$pid"]=1
  pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ' || true)
done

is_protected_pid() {
  local candidate="$1"
  [[ -n "${PROTECTED_PIDS[$candidate]:-}" ]]
}

log "== qianyi one-click stop =="

for sess in "${SESSIONS[@]}"; do
  if tmux has-session -t "$sess" 2>/dev/null; then
    log "Stopping tmux session: $sess"
    tmux kill-session -t "$sess" 2>/dev/null || true
  fi
done

# Some services (swift/Ray/Java/Node/Python) may spawn child process groups that survive
# after their tmux shell exits. Limit cleanup to commands rooted in this project path or
# known project ports so unrelated VS Code/Codex sessions are left alone.
patterns=(
  "$BASE_DIR/3090"
  "$BASE_DIR/4090"
  "--port 8000"
  "--port 8001"
  "--port 8003"
  "--port 8004"
  "--port 8005"
  "--port 8006"
  "--port 8007"
  "--port 8008"
  "--port 8009"
  "--port 8010"
  "--port 8011"
  "--port 8020"
  "--port 8021"
  "runserver 0.0.0.0:8088"
  "npm run dev"
  "elasticsearch-9.2.3"
  "kibana-9.2.3"
)

terminate_matches() {
  local signal="$1"
  local label="$2"
  local pattern pid
  for pattern in "${patterns[@]}"; do
    mapfile -t pids < <(pgrep -u "$USER" -f -- "$pattern" 2>/dev/null || true)
    for pid in "${pids[@]}"; do
      [[ -z "$pid" ]] && continue
      if is_protected_pid "$pid"; then
        continue
      fi
      if kill -0 "$pid" 2>/dev/null; then
        log "$label process $pid matching: $pattern"
        kill "$signal" "$pid" 2>/dev/null || true
      fi
    done
  done
}

terminate_matches -TERM "Terminating leftover"
sleep 2
terminate_matches -KILL "Force killing leftover"

remaining_sessions=$(tmux ls 2>/dev/null | grep -E '^(surgery|sagent1|sagent2|sagent3|sagent4|no_surgery_screening|no_surgery_name|surgery_reason|sicd|ocr|elastic|kibana|qy_backend|qy_web|agent1|agent2|agent3|agent4|agent_external|dicd|disease_reason):' || true)
if [[ -n "$remaining_sessions" ]]; then
  log "WARNING: these project tmux sessions remain:"
  log "$remaining_sessions"
  exit 1
fi

log "All qianyi managed services stopped."
