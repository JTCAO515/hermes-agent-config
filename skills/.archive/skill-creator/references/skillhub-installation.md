# SkillHub Installation — Hermes Agent Workflow

> 从 SkillHub 搜索、安装技能并集成到 Hermes Agent 的完整工作流。

## 单技能安装

```bash
# 1. 搜索
skillhub search <关键词>

# 2. 安装（下载到 ~/skills/<name>/）
skillhub install <skill-name>

# 3. 复制到 Hermes
cp -r /home/ubuntu/skills/<skill-name> /home/ubuntu/.hermes/skills/
```

## 批量安装（10+ 技能）

```python
from hermes_tools import terminal

skills = ["skill-a", "skill-b", ...]
for s in skills:
    result = terminal(f"skillhub install {s}", timeout=30)
    terminal(f"cp -r /home/ubuntu/skills/{s} /home/ubuntu/.hermes/skills/")
```

## 安装后检查清单

- [ ] SKILL.md 在 `~/.hermes/skills/<name>/` 下存在且内容完整
- [ ] 检查 YAML frontmatter 的 `environment_variables`/`requires.env` 字段
- [ ] 如有环境变量需求 → 写入 `~/.hermes/.env`（不要写 `~/.bashrc`）
- [ ] 如有 Python 依赖 → 用 `/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3 install`
- [ ] 如有 Python 包 → 做导入验证：`python3 -c "from <pkg> import ...; print('OK')"`
- [ ] 检查是否有外部命令依赖（如 `which <cmd>`）

## 已知约束

| 约束 | 说明 |
|------|------|
| 安装路径 | `skillhub install` 默认装到 `~/skills/<name>/`，需手动 cp 到 `~/.hermes/skills/` |
| Python venv | 必须用 `/home/ubuntu/.hermes/hermes-agent/venv/bin/pip3`，非系统 pip3 |
| 环境变量 | 写 `~/.hermes/.env`（不能写 `~/.bashrc`，Agent 启动时读取 .env） |
| 技能描述不完整 | 部分 SkillHub 技能的 SKILL.md 可能缺少描述或触发词，需手动补充 |
| 重复技能 | 安装前检查 `~/.hermes/skills/` 是否已有同名或同功能技能 |

## 已安装技能实例（2026-06）

| 来源 | 技能 |
|------|------|
| SkillHub | ths-advanced-analysis, ima-skills, proactive-agent, find-skills, skill-vetter, ontology, agent-browser, humanizer, codeconductor, web-tools-guide, word-docx, excel-xlsx, skill-creator (update), auto-updater, openai-whisper, agent-memory, automation-workflows, evolver, mcporter |
| 自建 | rtk-token-killer |
