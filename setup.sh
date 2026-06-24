#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Hermes Agent Configuration Migration - Setup Script
# ============================================================
# This script sets up Hermes Agent on a fresh server:
#   1. Clones the hermes-agent repo from GitHub
#   2. Creates a Python venv and installs dependencies
#   3. Copies config files (SOUL.md, AGENTS.md, config.yaml, etc.)
#   4. Sets up cron states, memory, and scripts
#   5. Prints instructions for manual steps (API keys, .env, vault)
# ============================================================

set -euo pipefail

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
echo "[1/6] Cloning hermes-agent from GitHub..."
if [ ! -d "${HERMES_AGENT_DIR}" ]; then
    git clone "${HERMES_REPO}" "${HERMES_AGENT_DIR}" --depth 1
    echo "  ✅ Cloned to ${HERMES_AGENT_DIR}"
else
    echo "  ⚠️  ${HERMES_AGENT_DIR} already exists, skipping clone"
    echo "     To re-clone: rm -rf ${HERMES_AGENT_DIR} && re-run this script"
fi

# ---- Step 2: Set up Python venv ----
echo ""
echo "[2/6] Setting up Python virtual environment..."
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
echo "[3/6] Creating ~/.hermes directory structure..."
mkdir -p "${HERMES_DIR}/scripts"
mkdir -p "${HERMES_DIR}/cron/states"
mkdir -p "${HERMES_DIR}/memory"
mkdir -p "${HERMES_DIR}/vault"
mkdir -p "${HERMES_DIR}/data/conversations"
mkdir -p "${HERMES_DIR}/data/dashboard"

# ---- Step 4: Copy config files ----
echo ""
echo "[4/6] Copying configuration files..."

# Core files
cp "${SCRIPT_DIR}/SOUL.md" "${HERMES_DIR}/SOUL.md"
cp "${SCRIPT_DIR}/AGENTS.md" "${HERMES_DIR}/AGENTS.md"
cp "${SCRIPT_DIR}/config.yaml" "${HERMES_DIR}/config.yaml"
echo "  ✅ SOUL.md, AGENTS.md, config.yaml"

# Scripts
cp "${SCRIPT_DIR}/scripts/"*.py "${HERMES_DIR}/scripts/"
echo "  ✅ Scripts (${SCRIPT_DIR}/scripts/*.py -> ${HERMES_DIR}/scripts/)"

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

# ---- Step 5: Permissions ----
echo ""
echo "[5/6] Setting permissions..."
chmod 700 "${HERMES_DIR}/vault"
chmod 600 "${HERMES_DIR}/config.yaml" 2>/dev/null || true

# ---- Step 6: Verify ----
echo ""
echo "[6/6] Verifying installation..."
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
check_file "${HERMES_DIR}/scripts/weixin_send.py"
check_file "${HERMES_DIR}/scripts/monitor-vp-codex.py"
check_file "${HERMES_DIR}/scripts/check-claude-status.py"
check_file "${HERMES_DIR}/scripts/news_briefing.py"

# Verify hermes-agent binary
if [ -f "${HERMES_AGENT_DIR}/venv/bin/hermes" ]; then
    echo "  ✅ hermes-agent binary"
    HERMES_VERSION=$("${HERMES_AGENT_DIR}/venv/bin/hermes" --version 2>/dev/null || echo "unknown")
    echo "     Version: ${HERMES_VERSION}"
elif command -v hermes &>/dev/null; then
    echo "  ✅ hermes (system PATH)"
else
    echo "  ⚠️  hermes binary not found in venv or PATH"
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""

# ---- Manual steps ----
cat <<EOF
📋 MANUAL STEPS (REQUIRED):

1. 🔑 Set up API keys in ~/.hermes/.env:
     cp .env.example ~/.hermes/.env
     nano ~/.hermes/.env
     → Fill in all YOUR_* placeholders with real API keys

2. 🔐 Restore your vault:
     Copy your credentials.json to ~/.hermes/vault/credentials.json
     chmod 600 ~/.hermes/vault/credentials.json
     (DO NOT commit this to git!)

3. 🔗 Set up GitHub PAT for private repos:
     Add your PAT to ~/.git-credentials:
     https://YOUR_USERNAME:YOUR_PAT@github.com

4. 🌐 Configure Xray proxy (if in China):
     Set HTTP_PROXY=http://127.0.0.1:10809
     Set HTTPS_PROXY=http://127.0.0.1:10809

5. 📡 Set up cron jobs:
     hermes cron add --name "repo-monitor" --interval 2h \
       --command "python3 ~/.hermes/scripts/monitor-vp-codex.py"

6. 🔧 Review and update config.yaml:
     Check provider URLs and model settings for your environment
     Replace YOUR_* placeholders with actual values

7. 🚀 Start Hermes Agent:
     cd ~/.hermes/hermes-agent
     ./venv/bin/hermes serve

EOF

echo "Done! 🎉"
echo ""
