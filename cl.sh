#!/bin/bash

echo "🚀 正在注入 DeepSeek 环境变量..."

# 指向本地 LiteLLM 代理
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=""
export ANTHROPIC_MODEL=deepseek-v4-flash
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-flash
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-flash
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
echo "✅ 环境就绪！正在启动 Claude Code..."

# 启动 Claude Code
claude

#  
# 现在同目录下备份/opt/qianyi/3090/_LLM/ICD_backend/ICD/icd/disease/GetICD.py和/opt/qianyi/4090/_LLM/ICD_backend/main/icd/GetICD.py /opt/qianyi/4090/_LLM/ICD_backend/main/icd/
#   GetICD_noSurgery.py，备份后修改这三个文件，实现的效果如下/opt/qianyi/deploy_backups/tools 调用这个文件下面的函数，当输入指定的病历的时候，即病历的标识号为json文件里面的，则最后输出到前端table修
#   改成json提前指定的