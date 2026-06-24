# Docker + 后端部署在中文 VPS 的 Python 依赖陷阱

## 最新 Docker Compose 版本警告

Docker Compose v2 (v5.x) 下，旧版 `docker-compose.yml` 顶层 `version: "3.9"` 属性已废弃：

```
time="..." level=warning msg="/path/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
```

不影响功能（Docker 直接忽略该字段），但建议新建项目时删掉。

## build vs up -d 分离策略

在中国 VPS 上，全量 `docker compose up -d` 会同时拉镜像 + 构建 + 启动，超时难定位。建议分离：

```bash
# 1. 先单独构建（出问题重试快）
docker compose build api

# 2. 再启动全部
docker compose up -d

# 3. 检查状态
docker ps --filter name=backend --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## 问题

在腾讯云/阿里云等中国大陆 VPS 上，Docker 构建时 `pip install` 连接
`files.pythonhosted.org` 超时（ReadTimeoutError）。

## 修复

Dockerfile 中添加 Tencent PyPI 镜像：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.tencent.com/pypi/simple/ -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

其他可用镜像：
- 腾讯：`https://mirrors.tencent.com/pypi/simple/`
- 阿里：`https://mirrors.aliyun.com/pypi/simple/`
- 清华：`https://pypi.tuna.tsinghua.edu.cn/simple/`

## Docker + VPS 部署流程

### 1. 构建与启动

```bash
cd backend/
docker compose build api    # 单独构建（pip 超时时方便重试）
docker compose up -d        # 启动全部容器
```

### 2. 种子数据 + 管理员

```bash
docker exec <container-name> python /app/seed.py
```

### 3. 端口冲突处理

```bash
ss -tlnp | grep 8000
# 修改 docker-compose.yml: ports -> "8001:8000"
```

### 完整全栈验证

```bash
# 1. 健康检查
curl -s --noproxy '*' http://localhost:<PORT>/api/health
# → {"status":"ok","version":"0.1.0"}

# 2. 管理员登录
TOKEN=$(curl -s --noproxy '*' -X POST http://localhost:<PORT>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@visepanda.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Admin 统计
curl -s --noproxy '*' http://localhost:<PORT>/api/admin/stats \
  -H "Authorization: Bearer $TOKEN"

# 4. 目的地列表
curl -s --noproxy '*' "http://localhost:<PORT>/api/destinations?limit=3"
```

> ⚠️ 注意：国内 VPS 的 curl **必须加 `--noproxy '*'`**，否则 `http_proxy` 环境变量会让 curl 走代理而不是直连 localhost，导致 503 或连接超时。

### 5. API 返回 503（非真正错误）

现象：`curl -v` 显示 `Connected to 127.0.0.1:10809` + `503 Service Unavailable`。

原因：`http_proxy` 环境变量指向了一个本地代理（如 Xray/Shadowsocks），curl 实际连的是代理端口而非目标端口。

修复：一律加 `--noproxy '*'` 或设置 `export no_proxy=localhost,127.0.0.1`。

