# Backend Scaffold: FastAPI + PostgreSQL (从零搭建)

> 用于 Section I (产品开发设计文档) Phase 0 执行时的参考模板。
> 这是标准后端起步结构，适用于任何需要 API + Auth + DB 的新项目。

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app 入口 + CORS + 路由注册 + startup
│   ├── config.py            # pydantic-settings 配置
│   ├── database.py          # SQLAlchemy engine + SessionLocal + get_db
│   ├── models/              # ORM 模型
│   │   ├── __init__.py
│   │   ├── user.py          # JWT 认证用户
│   │   ├── destination.py   # 目的地/内容
│   │   ├── trip.py          # 用户行程
│   │   └── auth_token.py    # 邮箱验证/密码重置 Token
│   ├── schemas/             # Pydantic 请求/响应
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── destination.py
│   │   └── trip.py
│   ├── api/                 # 路由
│   │   ├── __init__.py
│   │   ├── auth.py          # 注册/登录/验证/重置
│   │   ├── destinations.py  # 列表/详情
│   │   ├── chat.py          # SSE 流式
│   │   ├── trips.py         # CRUD
│   │   └── admin.py         # 管理后台
│   ├── core/                # 核心工具
│   │   ├── __init__.py
│   │   ├── security.py      # JWT + bcrypt
│   │   ├── deps.py          # get_current_user / get_current_admin
│   │   └── email.py         # SMTP (先 mock)
│   └── seed/                # 种子数据
│       └── destinations.py  # 20+ 城市
├── migrations/              # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml       # PostgreSQL + API
└── README.md
```

## 标准依赖 (requirements.txt)

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.31
alembic==1.13.1
pydantic==2.7.4
pydantic-settings==2.3.4
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.9
sse-starlette==2.0.0
```

## 5张核心表

| 表 | 核心字段 | 用途 |
|----|---------|------|
| `users` | id(UUID), email(UNIQUE), password_hash, display_name, role(enum), status(enum), created_at, last_login_at | 认证用户 |
| `destinations` | id(VARCHAR PK), name, name_cn, description, image_url, tags(ARRAY), must_see(JSONB), must_eat(JSONB) | 目的地内容 |
| `trips` | id(UUID), user_id(FK), title, cities(ARRAY), days(INT), content(JSONB), created_at | 用户行程 |
| `email_verifications` | id(UUID), user_id(FK), token(UNIQUE), expires_at, used(BOOL) | 邮箱验证 |
| `password_resets` | id(UUID), user_id(FK), token(UNIQUE), expires_at, used(BOOL) | 密码重置 |

## 认证系统要点

- **密码**: bcrypt (passlib.context.CryptContext)
- **JWT**: python-jose, HS256, 24h 过期
- **注册流程**: 创建用户(status=pending) → 发送验证邮件 → 用户点击验证 → status=active
- **登录流程**: 验证凭据 → 检查 status=active → 返回 JWT(access_token)
- **依赖注入**: `get_current_user` (从 JWT 解 sub→查询 User) + `get_current_admin` (检查 role=admin)

## 种子数据

每个城市至少包含：name, name_cn, description, image_url(placeholder), tags, must_see(3+), must_eat(3+), stay_tips, best_days, budget_range, latitude, longitude

中国主要旅游城市（28个）：Beijing, Shanghai, Guangzhou, Shenzhen, Chengdu, Xi'an, Guilin, Hangzhou, Suzhou, Nanjing, Lijiang, Kunming, Zhangjiajie, Jiuzhaigou, Harbin, Qingdao, Xiamen, Wuhan, Dunhuang, Lhasa, Hong Kong, Macau, Taipei, Dali, Chengde, Dalian, Luoyang, Changsha

## docker-compose.yml 示例

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: visepanda
      POSTGRES_PASSWORD: visepanda
      POSTGRES_DB: visepanda
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U visepanda"]
      interval: 5s
      timeout: 5s
      retries: 5
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql://visepanda:visepanda@db:5432/visepanda"
      JWT_SECRET: "change-me-in-production"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
```

## 快速验证

```bash
docker-compose up -d
# 访问 http://localhost:8000/docs → Swagger UI
# POST /api/auth/register 创建用户
# POST /api/auth/login 获取 JWT
# GET /api/destinations 查看城市列表
```
