# VisePanda 完整项目规格

> 来源：`JTCAO515/vise-panda-2` SPEC.md — 用于「从零重建」场景  
> 包含 API Key 等敏感值，仅供本地参考，切勿提交到公开仓库

## 项目概要

- **名称**: VisePanda
- **定位**: AI 对话式中国旅行规划助手
- **域名**: go2china.space
- **GitHub**: JTCAO515/vise-panda-2
- **LLM**: GLM 5.1 (open.bigmodel.cn/api/paas/v4)
- **数据库**: Supabase (jdlinmdhmulozrjeseyc.supabase.co)
- **部署**: Vercel Serverless Function

## Supabase 配置

```
SUPABASE_URL = https://jdlinmdhmulozrjeseyc.supabase.co
SUPABASE_ANON_KEY = sb_publishable_GDZz-hDv6m-GTzRwsAt7Lw_BaU7CQYM
```

## GLM 5.1 配置

```
LLM_BASE_URL = https://open.bigmodel.cn/api/paas/v4
LLM_MODEL = glm-5.1
LLM_API_KEY = f8deeed9d23b43c8a891f72dd99d8d10.tErLZfXyLsq5wFzc
```

API Key 位置：`grep GLM_API_KEY ~/.hermes/.env`

## 数据库表

3 张表：users, trips, chat_messages

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    profile JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE trips (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    title TEXT, cities JSON, start_date TEXT, end_date TEXT,
    constraints JSON, current_itinerary JSON, itinerary_versions JSON,
    created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT, trip_id TEXT REFERENCES trips(id),
    role TEXT, content TEXT, created_at TIMESTAMP
);
```

## API 端点

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | /api/health | `{ok:true}` | 无 |
| GET | / | 着陆页 HTML | 无 |
| GET | /chat | 聊天页 HTML | 无 |
| GET | /auth/callback | OAuth 回调 | 无 |
| POST | /api/chat | SSE 流式对话 | Bearer 或 guest_id |
| GET | /api/trips | 行程列表 | Bearer |
| GET | /api/trips/{id} | 行程详情 | Bearer |

## 项目结构

```
vise-panda-2/
├── api/
│   ├── main.py          # 所有 FastAPI 代码（单文件 ~400 行）
│   ├── index.py         # from main import app
│   ├── requirements.txt # fastapi, uvicorn, httpx, sqlalchemy, python-jose
│   └── .env.example     # 不含敏感值的模板
├── vercel.json          # {"rewrites": [{"source": "/(.*)", "destination": "/api/index.py"}]}
├── .gitignore
└── SPEC.md              # 本文档
```

## 架构反模式（重写后应避免）

- ❌ 静态 HTML + `fetchPublicConfig()` → ✅ 服务端注入 `window.__SUPABASE_CONFIG__`
- ❌ `__API_BASE__` 硬编码 → ✅ 无此概念
- ❌ vercel.json 几十条 rewrite → ✅ 一条
- ❌ 多文件前端模块链 → ✅ 单文件内联
- ❌ vercel.json 的 `functions` 块 → ✅ 删除，Vercel 自动检测
