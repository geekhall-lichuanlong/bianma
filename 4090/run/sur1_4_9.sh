export RAY_memory_monitor_refresh_ms=10 
export CUDA_VISIBLE_DEVICES=1
swift deploy \
    --model_type qwen3 \
    --model /opt/qianyi/4090/_LLM/models/no_surgery_agent1_v2026011_8B \
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.05 \
    --port 8010