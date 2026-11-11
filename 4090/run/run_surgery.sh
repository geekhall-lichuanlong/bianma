#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/qianyi"
CONDA_SH_PATH="/opt/miniconda3/etc/profile.d/conda.sh"

if [[ ! -f "$CONDA_SH_PATH" ]]; then
  echo "ERROR: conda init script not found: $CONDA_SH_PATH" >&2
  exit 1
fi

source "$CONDA_SH_PATH"
conda activate qy

start_session() {
  local sess="$1"
  local env_name="$2"
  local command="$3"

  tmux has-session -t "$sess" 2>/dev/null && tmux kill-session -t "$sess" || true
  tmux new-session -d -s "$sess" "bash -lc 'source "$CONDA_SH_PATH" && conda activate "$env_name" && $command; exec bash'"
}

# 4 surgery agents
start_session sagent1 qy "cd /opt/qianyi/4090/run && bash sur1.sh"
start_session sagent2 qy "cd /opt/qianyi/4090/run && bash sur2.sh"
start_session sagent3 qy "cd /opt/qianyi/4090/run && bash sur3.sh"
start_session sagent4 qy "cd /opt/qianyi/4090/run && bash sur4.sh"

# ????(4.9)
start_session no_surgery_screening qy "cd /opt/qianyi/4090/run && bash sur2_4_9.sh"

# ?????
start_session no_surgery_name qy "cd /opt/qianyi/4090/run && bash sur_0604.sh"

# reason

# surgery ICD backend
start_session sicd qy "cd /opt/qianyi/4090/_LLM/ICD_backend/main && bash run.sh"

echo "Created surgery tmux sessions."

# ocr service
# start_session ocr Pocr "python /opt/qianyi/4090/OCR/PaddleOCR-main/ppstructure/app_929.py"
start_session ocr Pocr "CUDA_VISIBLE_DEVICES=1 python /opt/qianyi/4090/OCR/PaddleOCR-main/ppstructure/app_929_serial_gpu1.py"

echo "Created OCR service."
