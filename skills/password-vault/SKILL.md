---
name: password-vault
description: 密码本 — 安全存储和检索 API Key、平台账号密码。用户发送平台名+凭据时自动保存，需要时按平台名调取。
---

# 密码本 (Password Vault)

## 存储位置
`~/.hermes/vault/credentials.json` — 权限 600，仅本机可读。

## 数据格式
```json
{
  "平台名": {
    "username": "账号",
    "password": "密码",
    "api_key": "API Key",
    "api_secret": "API Secret",
    "notes": "备注",
    "created": "2026-06-23",
    "updated": "2026-06-23"
  }
}
```

## 操作方式

### 保存凭据
当用户发送平台名 + 凭据时，调用 `python3 ~/.hermes/scripts/vault.py add`。

**规则：**
- 每个平台名作为 key，覆盖写（更新 updated 时间戳）
- 只保存用户明确告诉的信息，不脑补
- 保存后回复用户 ✅ 已保存

### 调取凭据
当用户问"我XX平台的密码/API key是什么"时，调用 `python3 ~/.hermes/scripts/vault.py get <平台名>`。

**规则：**
- 返回该平台的完整记录
- 只返回给提出请求的用户本人
- 不打印到日志，不写入 memory

### 列出所有平台
调用 `python3 ~/.hermes/scripts/vault.py list`

## 脚本路径
`~/.hermes/scripts/vault.py`

## 安全规则
- 文件权限 600（owner 读写）
- 不提交到任何 git 仓库
- 不记录到 memory 工具
- 不在微信消息中公开显示完整 API key（只显示前4位+后4位脱敏）
- 用户明确要求看完整 key 时才完整展示

## 脱敏显示规则
显示凭据时，API Key/Password 只显示前4位和后4位，中间用 `****` 替代。
示例：`sk-63****458`、`pass****1234`

## 参考文件
- `references/vault-usage.md` — 完整 CLI 用法示例
