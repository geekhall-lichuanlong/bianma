#!/bin/bash

# 创建 4 个 tmux 会话（sagent1-sagent4），每个激活 conda 环境后执行指定命令
# tmux new-session -d -s sagent1 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=0 CUDA_VISIBLE_DEVICES=1 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/surgeryAgent/agent1_standardized/v0-20250916-123528/checkpoint-897 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.05 --port 8000; exec bash'"

# tmux new-session -d -s sagent2 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=0 CUDA_VISIBLE_DEVICES=1 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/surgeryAgent/agent2_additional_new/v0-20251009-175139/checkpoint-201 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.05 --port 8001; exec bash'"
tmux new-session -d -s sagent1 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=0 CUDA_VISIBLE_DEVICES=1 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/ceshiwenjian/hunhe/surgery/model/v0-20251026-210144/checkpoint-4355 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.05 --port 8000; exec bash'"

tmux new-session -d -s sagent2 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=1 CUDA_VISIBLE_DEVICES=1 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/surgeryAgent/agent2_additional_new/v0-20251009-175139/checkpoint-201 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.05 --port 8001; exec bash'"

tmux new-session -d -s sagent3 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=1 CUDA_VISIBLE_DEVICES=2 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/surgeryAgent/agent3_anotherCoding/v0-20250916-123600/checkpoint-300 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8002; exec bash'"

# tmux new-session -d -s sagent4 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=1 CUDA_VISIBLE_DEVICES=2 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/old/agent4/agent4_2916/v0-20250910-084106/checkpoint-1041 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8003; exec bash'"

# tmux new-session -d -s sagent5 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=1 CUDA_VISIBLE_DEVICES=2 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/surgeryAgent/agent5_screening/v1-20251013-171112/checkpoint-1035 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8009; exec bash'"

echo "Created tmux sessions: sagent1 to sagent4, all activating conda environment 'qianfoshan' and starting corresponding swift deploy commands."

# 进入命令监听循环
while true; do
    read -p "请输入命令（输入 quit 关闭并删除 sagent1-sagent5）： " CMD
    if [[ "$CMD" == "quit" ]]; then
        echo "Closing and killing tmux sessions: sagent1 to sagent5..."
        for i in {1..3}
        do
            tmux kill-session -t sagent$i 2>/dev/null
        done
        echo "Selected tmux sessions closed and deleted."
        break
    else
        echo "无效命令，请重新输入。"
    fi
done