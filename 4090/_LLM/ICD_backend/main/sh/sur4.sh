RAY_memory_monitor_refresh_ms=0 
CUDA_VISIBLE_DEVICES=0klkjjkhkkkkkkik

swift deploy \
    --model_type qwen3 \
    --model /home/gminig/qy_llm/surgery_models/agent5/surgery_agent5_v20260113\
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.00 \
    --port 8009