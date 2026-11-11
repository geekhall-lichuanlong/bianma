# 模型与复现资源

模型权重采用独立托管、README 链接下载的方式。计划使用 ModelScope 魔搭模型仓库，按模型分别记录版本与下载地址。当前尚未上传权重，因此这里没有可用下载链接。

## 本地推理文件清单

| 部署目录 | 推理文件大小 | 下载状态 |
| --- | --- | --- |
| `3090/_LLM/models/Qwen3.5-4B` | 8.70 GiB | 待托管 |
| `3090/_LLM/models/disease_agent1_v20260113` | 3.22 GiB | 待托管 |
| `3090/_LLM/models/disease_agent5_v20260113` | 3.22 GiB | 待托管 |
| `3090/_LLM/models/disease_agent6_v20260113` | 3.22 GiB | 待托管 |
| `3090/_LLM/models/disease_external_cause_agent_v20260727` | 3.80 GiB | 待托管 |
| `3090/_LLM/models/disease_pathology_agent_v20260725` | 3.80 GiB | 待托管 |
| `4090/_LLM/models/no_surgery_name_V20260604` | 3.22 GiB | 待托管 |
| `4090/_LLM/models/no_surgery_screening_V2026011` | 3.80 GiB | 待托管 |
| `4090/_LLM/models/surgery_agent1_v20260327` | 4.14 GiB | 待托管 |
| `4090/_LLM/models/surgery_agent2_v20260113` | 3.22 GiB | 待托管 |
| `4090/_LLM/models/surgery_agent4_v20260113` | 3.22 GiB | 待托管 |
| `4090/_LLM/models/surgery_agent5_v20260113` | 3.22 GiB | 待托管 |

逐文件大小及 SHA256 见 [model-manifest.json](model-manifest.json)。大小为选定推理文件的合计，不包含训练文件和日志。

模型托管时每个版本应记录：模型用途、基础模型及其版本、许可、文件校验值、固定下载 revision、适配的代码 commit。先确认自训练权重与基础模型的发布权限，再决定公开范围。基础模型可以链接其原始官方仓库，项目专用权重单独提供。

## 复现准备顺序

1. 固定本仓库代码 commit；参考 [部署说明](deployment.md) 和 `environment/` 安装 Linux / GPU / Python / Node 环境。
2. 等待模型仓库地址发布，按清单下载并恢复到相应目录。`disease_agent7_v20260205` 是疾病病理模型的兼容目录链接，部署时检查对应启动脚本与链接目标。
3. 单独准备 OCR 推理文件、字体、ICD 字典和规则、Elasticsearch 映射与检索数据。只具备 LLM 权重仍不足以启动完整系统。
4. 创建全新业务数据库与账号，导出 `.env.example` 中的环境变量，检查路径、GPU 编号和端口，再按模块启动。
5. 用自行构造的虚拟病例验证 OCR → 编码 → 结果展示。记录输入、输出、硬件、服务版本与耗时，形成复现报告。

原始病历、附件、患者数据库和训练数据不提供下载。当前只有源码静态检查及界面预览验证，尚未完成独立 GPU 环境的端到端复现；不承诺一键复现或相同临床编码结果。

## 发布下载地址后的校验

下载后的目录可用仓库内 `tools/verify_models.py` 验证文件大小与 SHA256。该工具只读取本地文件，不下载、不执行模型代码。

```bash
python tools/verify_models.py --root /opt/qianyi
```

相关平台说明：[魔搭模型上传文档](https://modelscope.cn/docs/models/upload)、[官方 SDK](https://github.com/modelscope/modelscope_hub)。
