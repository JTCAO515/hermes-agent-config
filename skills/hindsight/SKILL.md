---
name: hindsight
description: "Hindsight — Agent记忆系统(需Docker运行)。让AI agent拥有长期学习能力，超越简单对话历史回忆"
version: 1.0.0
source: https://github.com/vectorize-io/hindsight
triggers:
  - hindsight
  - agent memory
  - 记忆系统
  - 长期记忆
---

# Hindsight — Agent Memory System

## 简介

Hindsight 是 vectorize-io 的 Agent 记忆系统，让 agent 能**学习**而非仅**回忆**。

## 安装（Docker）

```bash
docker run -d \
  --name hindsight \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=sk-... \
  vectorize/hindsight
```

## Python SDK

```bash
pip install hindsight-api
```

## 使用示例

```python
from hindsight import wrap_llm
client = wrap_llm(openai_client)  # 自动存储和回忆记忆
```

## 文档
官网: https://hindsight.vectorize.io
论文: https://arxiv.org/abs/2512.12818
