#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Hermes Agent 迁移 — 新服务器初始化"
echo "========================================"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 检查 hermes 是否已安装
if ! command -v hermes &> /dev/null; then
    echo -e "${RED}❌ hermes 未安装，请先安装 Hermes Agent${NC}"
    exit 1
fi
echo -e "${GREEN}✅ hermes 已安装: $(hermes --version)${NC}"

# 2. 创建目录结构
echo "📁 创建目录结构..."
mkdir -p ~/.hermes/{skills,harness,memories,cron}
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 3. 解压迁移包
TARBALL="/tmp/hermes-migration.tar.gz"
if [ ! -f "$TARBALL" ]; then
    echo -e "${RED}❌ 未找到迁移包 $TARBALL${NC}"
    echo "   请先用 scp 将迁移包传到本机 /tmp/ 目录"
    exit 1
fi

echo "📦 解压配置包..."
tar xzf "$TARBALL" -C ~/
echo -e "${GREEN}✅ 解压完成${NC}"

# 4. 生成 SSH Key（如果没有）
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "🔑 生成 SSH Key..."
    ssh-keygen -t ed25519 -C "hermes-migration-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519 -N ""
    echo -e "${GREEN}✅ SSH Key 已生成${NC}"
else
    echo -e "${GREEN}✅ SSH Key 已存在${NC}"
fi

# 5. 验证关键文件
echo ""
echo "📋 验证关键文件..."
MISSING=0
for f in SOUL.md AGENTS.md config.yaml; do
    if [ -f ~/.hermes/$f ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — 缺失"
        MISSING=1
    fi
done

# 统计 skills
SKILL_COUNT=$(find ~/.hermes/skills/ -name 'SKILL.md' 2>/dev/null | wc -l)
echo "  📦 skills: $SKILL_COUNT 个"

echo ""
if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}========================================"
    echo "✅ 核心配置迁移完成！"
    echo -e "========================================${NC}"
else
    echo -e "${YELLOW}⚠️  部分文件缺失，请检查${NC}"
fi

echo ""
echo "📝 接下来需要手动操作："
echo "  1. 复制 API Keys: 将旧服务器的 ~/.hermes/.env 内容粘贴到新服务器"
echo "  2. 添加 SSH Key 到 GitHub: cat ~/.ssh/id_ed25519.pub"
echo "  3. 重新登录平台: 微信扫码、元宝账号"
echo "  4. 重建 venv: cd ~/.hermes/hermes-agent && uv sync"
echo ""
echo "🧪 运行验证: hermes --version && head -3 ~/.hermes/SOUL.md"
