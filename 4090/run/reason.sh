export RAY_memory_monitor_refresh_ms=10 
export CUDA_VISIBLE_DEVICES=0
swift deploy \
    --model_type qwen3_5 \
    --model /opt/qianyi/3090/_LLM/models/Qwen3.5-4B \
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.05 \
    --port 8022