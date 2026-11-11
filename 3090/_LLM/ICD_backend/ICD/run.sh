# python3 run.py \
#     --disease_standardized_url "http://localhost:8004/v1/chat/completions" \
#     --disease_standardized_model checkpoint-5855 \
#     --disease_potential_verify_url "http://localhost:8005/v1/chat/completions" \
#     --disease_potential_verify_model checkpoint-1086 \
#     --disease_potential_url "http://localhost:8006/v1/chat/completions" \
#     --disease_potential_model checkpoint-820 \
#     --disease_potential_standardized_url "http://localhost:8007/v1/chat/completions" \
#     --disease_potential_standardized_model checkpoint-804 \
#     --disease_main_diagnosis_url "http://localhost:8004/v1/chat/completions" \
#     --disease_main_diagnosis_model checkpoint-5855 \
#     --flask_url "http://localhost:5000/" \
#     --output_dir "output"

# checkpoint-3000
# checkpoint-2875
# checkpoint-804
# checkpoint-804
# checkpoint-625

python3 run.py \
    --disease_standardized_url "http://localhost:8004/v1/chat/completions" \
    --disease_standardized_model disease_agent1_v20260113 \
    --disease_main_diagnosis_url "http://localhost:8005/v1/chat/completions" \
    --disease_main_diagnosis_model disease_agent5_v20260113 \
    --disease_screening_url "http://localhost:8006/v1/chat/completions" \
    --disease_screening_model disease_agent6_v20260113 \
    --disease_bingli_url "http://localhost:8007/v1/chat/completions" \
    --disease_bingli_model disease_agent7_v20260205 \
    --disease_external_url "http://localhost:8021/v1/chat/completions" \
    --disease_external_model disease_external_cause_agent_v20260727 \
    --flask_url "http://localhost:5511/" \
    --output_dir "output"
# --disease_potential_verify_url "http://localhost:8005/v1/chat/completions" \
# --disease_potential_verify_model checkpoint-1086 \
# --disease_potential_url "http://localhost:8006/v1/chat/completions" \
# --disease_potential_model checkpoint-820 \
# --disease_potential_standardized_url "http://localhost:8017/v1/chat/completions" \
# --disease_potential_standardized_model checkpoint-804 \
