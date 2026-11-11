#!/bin/bash

# 创建 5 个 tmux 会话（agent1-agent5），每个激活 conda 环境
#!/bin/bash

# 创建 5 个 tmux 会话（agent1-agent5），每个激活 conda 环境后执行指定命令
tmux new-session -d -s agent1 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=2 CUDA_VISIBLE_DEVICES=3 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/ceshiwenjian/hunhe/disease/model/v0-20251028-103203/checkpoint-5855 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.1 --port 8004; exec bash'"

tmux new-session -d -s agent2 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=2 CUDA_VISIBLE_DEVICES=3 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/output/model_1.7B/agent2_all_model/13_agent2_1200_empty_shuffle_0_and_1/v0-20250728-111309/checkpoint-1086 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8005; exec bash'"

tmux new-session -d -s agent3 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=2 CUDA_VISIBLE_DEVICES=3 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/output/model_1.7B/agent2_all_model/second_1_agent2_374_epoch_10/v0-20250728-141919/checkpoint-820 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8006; exec bash'"

tmux new-session -d -s agent4 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=3 CUDA_VISIBLE_DEVICES=0 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/output/model_1.7B/agent3/v1-20250718-013619/checkpoint-804 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.05 --port 8007; exec bash'"

tmux new-session -d -s agent5 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=3 CUDA_VISIBLE_DEVICES=0 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/SFT_model/disease/agent4_sorting/v1-20250919-133341/checkpoint-2247 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8008; exec bash'"

echo "Created tmux sessions: agent1 to agent5, all activating conda environment 'qianfoshanICD' and starting corresponding swift deploy commands."

# 进入命令监听循环
while true; do
    read -p "请输入命令（输入 quit 删除并关闭 agent1-agent5）： " CMD
    if [[ "$CMD" == "quit" ]]; then
        echo "Closing and killing tmux sessions: agent1 to agent5..."
        for i in {1..5}
        do
            tmux kill-session -t agent$i 2>/dev/null
        done
        echo "Selected tmux sessions closed and deleted."
        break
    else
        echo "无效命令，请重新输入。"
    fi
done