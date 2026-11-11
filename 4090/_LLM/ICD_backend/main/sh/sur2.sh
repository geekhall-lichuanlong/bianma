RAY_memory_monitor_refresh_ms=0 
CUDA_VISIBLE_DEVICES=0 
swift deploy \
    --model_type qwen3 \
    --model /home/gminig/qy_llm/surgery_models/agent2/surgery_agent2_v20260113\
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.00 \
    --port 8001