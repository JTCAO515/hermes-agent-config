#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Hermes Agent Configuration Migration - Setup Script
# ============================================================
# This script sets up Hermes Agent on a fresh server:
#   1. Clones the hermes-agent repo from GitHub
#   2. Creates a Python venv and installs dependencies
#   3. Copies all config files (SOUL.md, AGENTS.md, config.yaml, skills, scripts, etc.)
#   4. Sets up cron states, memory, harness
#   5. Prints comprehensive manual steps for post-migration
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_DIR="${HOME}/.hermes"
HERMES_AGENT_DIR="${HERMES_DIR}/hermes-agent"
HERMES_REPO="https://github.com/nousresearch/hermes-agent"

echo ""
echo "=============================================="
echo "  Hermes Agent Configuration Migration"
echo "=============================================="
echo ""

# ---- Step 1: Clone hermes-agent ----
echo "[1/7] Cloning hermes-agent from GitHub..."
if [ ! -d "${HERMES_AGENT_DIR}" ]; then
    git clone "${HERMES_REPO}" "${HERMES_AGENT_DIR}" --depth 1
    echo "  ✅ Cloned to ${HERMES_AGENT_DIR}"
else
    echo "  ⚠️  ${HERMES_AGENT_DIR} already exists, skipping clone"
    echo "     To re-clone: rm -rf ${HERMES_AGENT_DIR} && re-run this script"
fi

# ---- Step 2: Set up Python venv ----
echo ""
echo "[2/7] Setting up Python virtual environment..."
cd "${HERMES_AGENT_DIR}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✅ venv created"
else
    echo "  ⚠️  venv already exists, skipping"
fi

# Upgrade pip and install requirements
echo "  Installing dependencies..."
venv/bin/pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    venv/bin/pip install -r requirements.txt -q
    echo "  ✅ requirements.txt installed"
else
    echo "  ⚠️  No requirements.txt found, trying pyproject.toml..."
    venv/bin/pip install -e . -q 2>/dev/null || echo "  ⚠️  pip install -e . failed (may need manual setup)"
fi

# ---- Step 3: Create .hermes directory structure ----
echo ""
echo "[3/7] Creating ~/.hermes directory structure..."
mkdir -p "${HERMES_DIR}/scripts"
mkdir -p "${HERMES_DIR}/skills"
mkdir -p "${HERMES_DIR}/harness"
mkdir -p "${HERMES_DIR}/cron/states"
mkdir -p "${HERMES_DIR}/memory"
mkdir -p "${HERMES_DIR}/vault"
mkdir -p "${HERMES_DIR}/data/conversations"
mkdir -p "${HERMES_DIR}/data/dashboard"

# ---- Step 4: Copy core config files ----
echo ""
echo "[4/7] Copying configuration files..."

# Core files
cp "${SCRIPT_DIR}/SOUL.md" "${HERMES_DIR}/SOUL.md"
cp "${SCRIPT_DIR}/AGENTS.md" "${HERMES_DIR}/AGENTS.md"
cp "${SCRIPT_DIR}/config.yaml" "${HERMES_DIR}/config.yaml"
echo "  ✅ SOUL.md, AGENTS.md, config.yaml"

# Skills
if [ -d "${SCRIPT_DIR}/skills" ]; then
    cp -a "${SCRIPT_DIR}/skills/." "${HERMES_DIR}/skills/"
    echo "  ✅ Skills (all SKILL.md + references + scripts)"
fi

# Scripts
cp "${SCRIPT_DIR}/scripts/"*.py "${HERMES_DIR}/scripts/" 2>/dev/null || true
echo "  ✅ Scripts (monitor, news, vault, etc.)"

# Harness templates
if [ -d "${SCRIPT_DIR}/harness" ]; then
    cp "${SCRIPT_DIR}/harness/"* "${HERMES_DIR}/harness/" 2>/dev/null || true
    echo "  ✅ Harness templates"
fi

# Cron states
if [ -d "${SCRIPT_DIR}/cron/states" ]; then
    cp "${SCRIPT_DIR}/cron/states/"* "${HERMES_DIR}/cron/states/" 2>/dev/null || true
    echo "  ✅ Cron states"
fi

# Memory
if [ -d "${SCRIPT_DIR}/memory" ]; then
    cp "${SCRIPT_DIR}/memory/"* "${HERMES_DIR}/memory/" 2>/dev/null || true
    echo "  ✅ Memory files"
fi

# .env.example
cp "${SCRIPT_DIR}/.env.example" "${HERMES_DIR}/.env.example"
echo "  ✅ .env.example"

# ---- Step 5: Permissions ----
echo ""
echo "[5/7] Setting permissions..."
chmod 700 "${HERMES_DIR}/vault"
chmod 600 "${HERMES_DIR}/config.yaml" 2>/dev/null || true

# ---- Step 6: Verify ----
echo ""
echo "[6/7] Verifying installation..."
echo ""

check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $1"
    else
        echo "  ❌ MISSING: $1"
    fi
}

check_file "${HERMES_DIR}/SOUL.md"
check_file "${HERMES_DIR}/AGENTS.md"
check_file "${HERMES_DIR}/config.yaml"
check_file "${HERMES_DIR}/skills/SKILLS_GUIDE_MERGED.md"
check_file "${HERMES_DIR}/scripts/weixin_send.py"
check_file "${HERMES_DIR}/scripts/monitor-vp-codex.py"
check_file "${HERMES_DIR}/scripts/news_briefing.py"
check_file "${HERMES_DIR}/harness/PLAN.md"

# Verify hermes-agent binary
if [ -f "${HERMES_AGENT_DIR}/venv/bin/hermes" ]; then
    echo "  ✅ hermes-agent binary"
    HERMES_VERSION=$("${HERMES_AGENT_DIR}/venv/bin/hermes" --version 2>/dev/null || echo "unknown")
    echo "     Version: ${HERMES_VERSION}"
elif command -v hermes &>/dev/null; then
    echo "  ✅ hermes (system PATH)"
else
    echo "  ⚠️  hermes binary not found in venv or PATH"
    echo "     Try: cd ${HERMES_AGENT_DIR} && pip install -e ."
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""

# ---- Step 7: Manual steps ----
cat <<'EOF'
╔══════════════════════════════════════════════════════════════╗
║            📋 迁移后手动操作清单                              ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 必须操作（不做 Hermes 无法启动）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  🔑 填写 API Keys

   cp ~/.hermes/.env.example ~/.hermes/.env
   nano ~/.hermes/.env

   需要填写：
   • DEEPSEEK_API_KEY
   • DASHSCOPE_API_KEY (Qwen)
   • ZHIPU_API_KEY

   config.yaml 里也有 10 个 YOUR_* 占位符要替换：
   nano ~/.hermes/config.yaml
   搜索 "YOUR_" 逐一替换

2️⃣ 🔐 恢复密码本（vault）

   scp 旧服务器:~/.hermes/vault/credentials.json ~/.hermes/vault/
   chmod 600 ~/.hermes/vault/credentials.json

3️⃣ 🔗 GitHub PAT

   nano ~/.git-credentials
   格式：https://用户名:PAT@github.com
   chmod 600 ~/.git-credentials

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 重要操作（影响功能完整度）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4️⃣ 🌐 Xray 代理（国内服务器必备）

   安装：
     bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

   复制配置：
     # 从旧服务器拷贝 /usr/local/xray/config.json 过来
     systemctl start xray
     systemctl enable xray

   验证：curl -x http://127.0.0.1:10809 -s https://www.google.com

5️⃣ 📡 重建 Cron 任务

   Hermes 的 cron 定义存在 SQLite 数据库里，不随文件迁移。
   需要重新创建的定时任务清单：

   ┌─────────────────────┬──────────┬──────────────────────────────┐
   │ 任务                │ 频率     │ 说明                         │
   ├─────────────────────┼──────────┼──────────────────────────────┤
   │ VP 仓库变更监控     │ 每 2h    │ 监控 WC26/VP 仓库新提交     │
   │ Dashboard 状态生成  │ 每 6h    │ 刷新面板数据                 │
   │ 对话导出            │ 每 6h    │ 备份对话历史                 │
   │ 每日新闻早报        │ 每天 7点 │ 推送新闻摘要                 │
   │ 每日新闻晚报        │ 每天 22点│ 推送新闻摘要                 │
   │ 30天自我访谈        │ 每天 21点│ 每日一问                     │
   └─────────────────────┴──────────┴──────────────────────────────┘

   到新服务器上用 Hermes CLI 或找我帮你重建。

6️⃣ 💬 平台重连

   微信 / 元宝 / QQ 机器人 需要重新扫码或配置 Token。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵 可选操作（建议做但可后补）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7️⃣ 📂 克隆项目代码

   旧服务器 ~/projects/ 下有 30+ 项目，包括：
   • VP-Hermes-Web     → https://github.com/JTCAO515/VP-Hermes-Web
   • VP-Claude-Web     → https://github.com/JTCAO515/VP-Claude-Web
   • VP-Codex-APK      → https://github.com/JTCAO515/VP-Codex-APK
   • WC26-Main         → https://github.com/JTCAO515/WC26-Main (私有)
   • hermes-dashboard  → https://github.com/JTCAO515/hermes-dashboard
   • 其他 20+ 项目      → JTCAO515 组织下

   逐个项目 git clone 即可。

8️⃣ 💾 对话历史（可选）

   如果要从旧服务器保留所有对话记录：
   scp 旧服务器:~/.hermes/hermes-agent/state.db ~/.hermes/hermes-agent/
   （注意：state.db 包含 cron 定义和记忆，迁移后可能需重启）

9️⃣ 🔧 安装系统依赖（按需）

   # Python 工具
   sudo apt install python3-pip python3-venv git curl

   # Node.js (某些 skills 需要)
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
   sudo apt install nodejs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 启动 Hermes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   cd ~/.hermes/hermes-agent
   ./venv/bin/hermes serve

   或使用 systemd 自启（安装后找我配置）

EOF

echo ""
echo "Done! 🎉"
echo "Run the manual steps above to complete the migration."
echo ""
