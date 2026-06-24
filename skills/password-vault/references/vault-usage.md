# 密码本 CLI 使用指南

脚本位置：`~/.hermes/scripts/vault.py`

## 保存凭据

```bash
# 基本用法：平台名 + 字段
python3 ~/.hermes/scripts/vault.py add 高德地图 --api-key=xxxxx

# 多字段
python3 ~/.hermes/scripts/vault.py add OpenAI \
  --username=my@email.com \
  --password=secret123 \
  --api-key=sk-xxxxx \
  --notes="主账号"

# 纯账号密码
python3 ~/.hermes/scripts/vault.py add 携程 \
  --username=13800138000 \
  --password=mypassword
```

支持的字段名：`username`, `password`, `api_key`, `api_secret`, `notes`
（任何 `--key=value` 都会被保存，不限于上述列表）

## 调取凭据

```bash
# 查看指定平台的凭据（敏感字段脱敏显示）
python3 ~/.hermes/scripts/vault.py get 高德地图

# 输出示例：
# 📋 高德地图
#   created: 2026-06-23
#   updated: 2026-06-23
#   api-key: xxxx****xxxx  (完整: xxxxxxxxxx)
```

脱敏规则：API Key/Password 显示前4后4，括号内显示完整值。
用户明确要求看完整 key 时，用 `python3 ~/.hermes/scripts/vault.py get <平台名>` 返回完整内容。

## 列出所有平台

```bash
python3 ~/.hermes/scripts/vault.py list
# 📖 密码本 (5 个平台)
#   🔑🔐 高德地图  (更新: 2026-06-23)
#   🔑 OpenAI  (更新: 2026-06-23)
#   🔐 携程  (更新: 2026-06-23)
```

## 删除凭据

```bash
python3 ~/.hermes/scripts/vault.py delete 高德地图
```

## 数据文件

存储位置：`~/.hermes/vault/credentials.json`
权限：600（仅 owner 可读写）
格式：JSON，按平台名 key 索引
