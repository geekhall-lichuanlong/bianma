# 第一步先启动es库
#创建tmux会话 es_el
#启动命令为 conda activate qianfoshan; /mnt/bigdisk/icdproject/es/elasticsearch-8.17.2/bin/elasticsearch
#第二步启动kibana
#创建tmux会话 kb
#启动命令为 conda activate qianfoshan; /mnt/bigdisk/icdproject/es/kibana-8.17.2/bin/kibana

#第三步启动疾病agent
#创建tmux会话 disease_agent
#启动命令为 conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/disease_agent.sh
#第四步启动手术agent
#创建tmux会话 surgery_agent
#启动命令为 conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/surgery_agent.sh

#第五步启动icd系统
#创建tmux会话 dicd
#启动命令为 conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/p3/ICD/run.sh

#第六步启动手术icd
#创建tmux会话 sicd
#启动命令为 conda activate qianfoshan; /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/run.sh

#当输入quit时，删除所有tmux会话 包括上述六个和disease_agent创建的agent1-agent5和surgery_agent创建的sagent1-sagent5


#!/bin/bash

# Step 1: Start Elasticsearch
tmux new-session -d -s es_el "bash --login -c 'conda activate qianfoshan; /mnt/bigdisk/icdproject/es/elasticsearch-8.17.2/bin/elasticsearch; exec bash'"

# Step 2: Start Kibana
tmux new-session -d -s kb "bash --login -c 'conda activate qianfoshan; /mnt/bigdisk/icdproject/es/kibana-8.17.2/bin/kibana; exec bash'"

# Step 3: Start Disease Agent
tmux new-session -d -s disease_agent "bash --login -c 'conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/sh/disease_agent.sh; exec bash'"

# Step 4: Start Surgery Agent
# tmux new-session -d -s surgery_agent "bash --login -c 'conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/sh/surgery_agent.sh; exec bash'"
tmux new-session -d -s Allsurgery_agent "bash --login -c 'conda activate qianfoshan; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/sh/Allsurgery_agent.sh; exec bash'"


# Step 5: Start ICD System
tmux new-session -d -s dicd "bash --login -c 'conda activate qianfoshan;cd /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/p3/ICD; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital/p3/ICD/run.sh; exec bash'"

# Step 6: Start Surgery ICD
tmux new-session -d -s sicd "bash --login -c 'conda activate qianfoshan;cd /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD; bash /mnt/bigdisk/icdproject/ICD_code_of_Qianfoshan_Hospital_surgeries/Surgeries_code/Surgeries_ICD/run.sh; exec bash'"

# Quit function: Kill all tmux sessions (main six + agent1-5 + sagent1-5)
while true; do
    read -p "请输入命令（输入 quit 关闭并删除所有会话）： " CMD
    if [[ "$CMD" == "quit" ]]; then
        # Kill main six sessions
        for sess in es_el kb disease_agent surgery_agent dicd sicd; do
            tmux kill-session -t $sess 2>/dev/null
        done

        # Kill agent1-5 and sagent1-5 sessions
        for i in {1..5}; do
            tmux kill-session -t agent$i 2>/dev/null
            tmux kill-session -t sagent$i 2>/dev/null
        done

        echo "All tmux sessions killed."
        break
    else
        echo "无效命令，请重新输入。"
    fi
done