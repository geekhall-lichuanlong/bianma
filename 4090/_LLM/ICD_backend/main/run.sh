# python3 run.py \
#     --surgery_standardized_url "http://localhost:8000/v1/chat/completions" \
#     --surgery_standardized_model checkpoint-4355 \
#     --surgery_additional_url "http://localhost:8001/v1/chat/completions" \
#     --surgery_additional_model checkpoint-201 \
#     --surgery_another_coding_url "http://localhost:8002/v1/chat/completions" \
#     --surgery_another_coding_model checkpoint-300 \
#     --surgery_sorting_url "http://localhost:8000/v1/chat/completions" \
#     --surgery_sorting_model checkpoint-4355 \
#     --surgery_screening_url "http://localhost:8000/v1/chat/completions" \
#     --surgery_screening_model checkpoint-4355 \
#     --flask_url "http://localhost:6000/" \
#     --output_dir "output"
python3 run.py \
    --no_surgery_standardized_url "http://localhost:8020/v1/chat/completions" \
    --no_surgery_standardized_model Qwen3.5-4B \
    --surgery_another_coding_url "http://localhost:8020/v1/chat/completions" \
    --surgery_another_coding_model Qwen3.5-4B \
    --surgery_standardized_url "http://localhost:8000/v1/chat/completions" \
    --surgery_standardized_model surgery_agent1_v20260327 \
    --surgery_additional_url "http://localhost:8001/v1/chat/completions" \
    --surgery_additional_model surgery_agent2_v20260113 \
    --surgery_sorting_url "http://localhost:8003/v1/chat/completions" \
    --surgery_sorting_model surgery_agent4_v20260113 \
    --surgery_screening_url "http://localhost:8009/v1/chat/completions" \
    --surgery_screening_model surgery_agent5_v20260113 \
    --no_surgery_name_url "http://localhost:8010/v1/chat/completions" \
    --no_surgery_name_model no_surgery_name_V20260604 \
    --no_surgery_screening_url "http://localhost:8011/v1/chat/completions" \
    --no_surgery_screening_model no_surgery_screening_V2026011 \
    --flask_url "http://localhost:6000/" \
    --output_dir "output"
    #--no_surgery_standardized_url "http://localhost:8010/v1/chat/completions" \
    #  --no_surgery_standardized_model no_surgery_agent1_v2026011_8B \

# surgery_screening_url 填 3060 的地址


# --surgery_another_coding_url "http://localhost:8002/v1/chat/completions" \
# --surgery_another_coding_model checkpoint-300 \
# checkpoint-897
# checkpoint-282
# checkpoint-300
# checkpoint-1041