# 项目从 GitHub 克隆到新服务器

通用模式：克隆 → 装依赖 → 设环境变量 → 跑测试 → 启动。

## 通用模板

```bash
# 1. 克隆
mkdir -p ~/projects
git clone <REPO_URL> ~/projects/<project-name>
cd ~/projects/<project-name>

# 2. 安装依赖（使用 hermes 的 venv 避免污染系统 Python）
/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install -r requirements.txt
# 如有 dev 依赖
/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install -r requirements-dev.txt

# 3. 环境变量 — 追加到 ~/.hermes/.env
cat >> ~/.hermes/.env << 'EOF'
export KEY=VALUE
EOF

# 4. 跑测试
source ~/.hermes/.env
pytest -q

# 5. 启动
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## VisePanda (China Travel Agent) 示例

仓库: `https://github.com/JTCAO515/VisePanda-New`

| 变量 | 值 | 说明 |
|------|-----|------|
| `LLM_ENABLED` | `1` | 启用 LLM |
| `LLM_BASE_URL` | `https://api.deepseek.com` | DeepSeek API |
| `LLM_MODEL` | `deepseek-v4-flash` | 模型名 |
| `LLM_API_KEY` | `sk-xxx` | **需手动填入** |
| `HOTEL_PROVIDER` | `seed` | 种子酒店数据 |
| `AUTH_TEST_BYPASS` | `1` | 测试跳过认证 |

依赖: fastapi, uvicorn, pydantic, SQLAlchemy, python-multipart, httpx, python-jose
测试: 26 tests (pytest)

启动后访问:
- 前端: `http://<IP>:5173/`
- 后端 API 文档: `http://<IP>:8000/docs`
