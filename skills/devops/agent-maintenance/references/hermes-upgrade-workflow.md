# Hermes Agent Upgrade Workflow

## 升级路径

### 标准方式（无本地改动时）
```bash
hermes update
```

### 有本地改动时的手动方式
当 `hermes update` 因本地改动跳过合并时：

```bash
cd ~/.hermes/hermes-agent
git fetch upstream --tags
git stash push -m "pre-upgrade-YYYYMMDD"
git merge upstream/main --no-edit
git stash pop
hermes --version    # 验证
hermes doctor       # 健康检查
```

## 版本标记规则

Hermes Agent 使用双版本号系统：

| 版本 | Tag | 含义 |
|------|-----|------|
| v0.16.0 | v2026.6.5 | 2026年6月5日发布 |
| v0.17.0 | v2026.6.19 | 2026年6月19日发布 |

`hermes --version` 显示语义版本（v0.17.0），git tag 是日期版本（v2026.6.19）。

## 升级后检查

1. `hermes --version` — 确认版本号
2. `hermes doctor` — Python/SSL/包依赖检查
3. 如有本地改动文件，检查 git status 确认合并无冲突
