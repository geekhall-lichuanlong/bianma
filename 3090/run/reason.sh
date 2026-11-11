export RAY_memory_monitor_refresh_ms=10 
export CUDA_VISIBLE_DEVICES=3
swift deploy \
    --model_type qwen3_5 \
    --model /opt/qianyi/3090/_LLM/models/Qwen3.5-4B \
    --response_prefix "<think>\n\n</think>\n\n" \
    --repetition_penalty=1.05 \
    --vllm_gpu_memory_utilization 0.75 \
    --vllm_max_model_len 65536 \
    --vllm_max_num_seqs 2 \
    --port 8020
