export RAY_memory_monitor_refresh_ms=10 
export CUDA_VISIBLE_DEVICES=0
swift deploy \
    --model_type qwen3 \
    --model /opt/qianyi/3090/_LLM/models/disease_agent1_v20260113 \
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.05 \
    --max_new_tokens 4096 \
    --port 8004
