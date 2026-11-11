export RAY_memory_monitor_refresh_ms=10 
export CUDA_VISIBLE_DEVICES=2
swift deploy \
    --model_type qwen3 \
    --model /opt/qianyi/4090/_LLM/models/surgery_agent4_v20260113 \
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.1 \
    --port 8003
