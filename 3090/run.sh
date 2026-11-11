#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/qianyi"
CONDA_SH_PATH="/opt/miniconda3/etc/profile.d/conda.sh"
NODE_BIN="/usr/local/bin"

if [[ ! -f "$CONDA_SH_PATH" ]]; then
  echo "ERROR: conda init script not found: $CONDA_SH_PATH" >&2
  exit 1
fi

source "$CONDA_SH_PATH"
conda activate qy

start_session() {
  local sess="$1"
  local command="$2"

  tmux has-session -t "$sess" 2>/dev/null && tmux kill-session -t "$sess" || true
  tmux new-session -d -s "$sess" "bash -lc 'source "$CONDA_SH_PATH" && conda activate qy && $command; exec bash'"
}

# 1. start elasticsearch
start_session elastic "/opt/qianyi/3090/database/elasticsearch-9.2.3/bin/elasticsearch"

# 2. start kibana
start_session kibana "/opt/qianyi/3090/database/kibana-9.2.3/bin/kibana"

# 3. start qy-web-backend
start_session qy_backend "cd /opt/qianyi/3090/front-back/qy_icd/qy_backend && python manage.py runserver 0.0.0.0:8088" 

# 4. start qy-web_frontend
start_session qy_web "export PATH=\"$NODE_BIN:\$PATH\" && cd /opt/qianyi/3090/front-back/qy_icd/qianyi-web && npm run dev"

# 5. disease model NO.1 ???
start_session agent1 "cd /opt/qianyi/3090/run && bash dis1.sh"

# 6. disease model NO.2 ??
start_session agent2 "cd /opt/qianyi/3090/run && bash dis2.sh"

# 7. disease model NO.3 ??
start_session agent3 "cd /opt/qianyi/3090/run && bash dis3.sh"

# 8. disease model NO.4 ??
start_session agent4 "cd /opt/qianyi/3090/run && bash dis4.sh"

# 9. external-cause model
start_session agent_external "cd /opt/qianyi/3090/run && bash dis5.sh"

# 10. disease ICD backend
start_session dicd "cd /opt/qianyi/3090/_LLM/ICD_backend/ICD && bash run.sh"

# 11. reason
start_session disease_reason "cd /opt/qianyi/3090/run && bash reason.sh"

echo 'disease finished'
