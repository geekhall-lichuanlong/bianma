#!/bin/bash

# 创建 5 个 tmux 会话（agent1-agent5），每个激活 conda 环境
#!/bin/bash

# 创建 5 个 tmux 会话（agent1-agent5），每个激活 conda 环境后执行指定命令
tmux new-session -d -s agent1 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=2 CUDA_VISIBLE_DEVICES=3 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/all_disease/model/agent1/v0-20251211-103553/checkpoint-25776 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.1 --port 8004; exec bash'"

tmux new-session -d -s agent5 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=3 CUDA_VISIBLE_DEVICES=0 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/all_disease/model/agent5/v1-20251207-184113/checkpoint-26379 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1 --port 8008; exec bash'"

tmux new-session -d -s agent6 "bash --login -c 'conda activate qianfoshan; RAY_memory_monitor_refresh_ms=2 CUDA_VISIBLE_DEVICES=2 swift deploy --model_type qwen3 --tensor_parallel_size 2 --model /mnt/bigdisk/all_disease/model/agent6/v0-20260104-110513/checkpoint-25608 --response_prefix \"<think>\n\n</think>\n\n\" --repetition_penalty=1.1 --port 8007; exec bash'"

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