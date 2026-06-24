---
name: raganything
description: RAG-Anything — All-in-One 多模态 RAG 框架。支持 PDF/Office/图片/文本文件的解析、索引、多模态知识图谱构建与智能问答。PyPI 包 raganything。
---

# RAG-Anything: All-in-One 多模态 RAG 框架

`pip install raganything`（已安装）

基于 [LightRAG](https://github.com/HKUDS/LightRAG) 构建，支持多模态文档解析、知识图谱和智能检索。

## 快速使用

### 基本用法

```python
import asyncio
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

async def main():
    config = RAGAnythingConfig(
        working_dir="./rag_storage",
        parser="mineru",          # 文档解析器
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )

    # 配置 LLM（替换为你的 API key）
    async def llm_func(prompt, **kwargs):
        return await openai_complete_if_cache(
            "gpt-4o-mini",
            prompt,
            base_url="https://api.deepseek.com/v1",
            api_key="your-key",
            **kwargs
        )

    async def embedding_func(texts):
        return await openai_embed(
            texts,
            model="text-embedding-3-large",
            base_url="https://api.deepseek.com/v1",
            api_key="your-key"
        )

    rag = RAGAnything(
        config=config,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024, max_token_size=8192, func=embedding_func
        ),
    )

    # 处理文档
    await rag.process_document_complete("path/to/document.pdf", output_dir="./output")

    # 查询
    result = await rag.aquery("文档的主要内容是什么？")
    print(result)

asyncio.run(main())
```

### 支持的文档格式
- PDF（MinerU 高保真解析）
- Office：DOC/DOCX/PPT/PPTX/XLS/XLSX（需要 LibreOffice）
- 图片：JPG/PNG/BMP/TIFF/GIF/WebP
- 文本：TXT/MD

### 独立组件
```python
from raganything import RAGAnything, RAGAnythingConfig

# 也可直接使用底层 LightRAG
from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache
```
