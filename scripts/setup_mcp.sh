#!/bin/bash
# scripts/setup_mcp.sh
# Jarvis projesi için Claude Code MCP sunucularını kurar

set -e

echo "🤖 Jarvis için Claude Code MCP sunucuları kuruluyor..."
echo ""

# Renkli output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Claude Code kurulu mu?
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude Code bulunamadı.${NC}"
    echo "Kurulum için: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo -e "${BLUE}1/6${NC} GitHub MCP (user scope) — repo yönetimi"
claude mcp add github \
    --scope user \
    --transport stdio \
    -- npx -y @modelcontextprotocol/server-github

echo -e "${BLUE}2/6${NC} Brave Search MCP (user scope) — web arama"
echo -e "${YELLOW}   → BRAVE_API_KEY environment variable'ını ayarlamayı unutma${NC}"
claude mcp add brave-search \
    --scope user \
    --transport stdio \
    --env BRAVE_API_KEY="${BRAVE_API_KEY:-YOUR_KEY_HERE}" \
    -- npx -y @modelcontextprotocol/server-brave-search

echo -e "${BLUE}3/6${NC} Memory MCP (project scope) — oturumlar arası hafıza"
claude mcp add memory \
    --scope project \
    --transport stdio \
    -- npx -y @modelcontextprotocol/server-memory

echo -e "${BLUE}4/6${NC} SQLite MCP (project scope) — user profile DB"
claude mcp add sqlite \
    --scope project \
    --transport stdio \
    -- npx -y @modelcontextprotocol/server-sqlite \
    --db-path ./data/jarvis.db

echo -e "${BLUE}5/6${NC} Playwright MCP (project scope) — UI testleri"
claude mcp add playwright \
    --scope project \
    --transport stdio \
    -- npx -y @playwright/mcp@latest

echo -e "${BLUE}6/6${NC} Sequential Thinking MCP (user scope) — karmaşık planlama"
claude mcp add sequential-thinking \
    --scope user \
    --transport stdio \
    -- npx -y @modelcontextprotocol/server-sequential-thinking

echo ""
echo -e "${GREEN}✅ Tüm MCP sunucuları kuruldu!${NC}"
echo ""
echo "Kontrol et:"
echo "  claude mcp list"
echo ""
echo "Bir MCP'yi kaldırmak için:"
echo "  claude mcp remove <name>"
echo ""
echo -e "${YELLOW}📝 Notlar:${NC}"
echo "  • Brave Search için API key gerekli: https://brave.com/search/api/"
echo "  • GitHub MCP için GITHUB_TOKEN environment variable gerekli olabilir"
echo "  • Project scope MCP'ler .mcp.json dosyasına yazılır (git'e commit edebilirsin)"
echo "  • User scope MCP'ler tüm projelerinde geçerlidir"
