#!/bin/bash
# ============================================================
# Gamma — Disable Autostart / Выключить автозапуск
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}==================================================${NC}"
echo -e "${CYAN}${BOLD}  Gamma — Disable Autostart${NC}"
echo -e "${CYAN}${BOLD}  Выключить автозапуск${NC}"
echo -e "${CYAN}${BOLD}==================================================${NC}"
echo ""

AUTOSTART_FILE="$HOME/.config/autostart/gamma-restore.desktop"

if [ ! -f "$AUTOSTART_FILE" ]; then
    echo -e "${YELLOW}⚠️  Autostart is not enabled / Автозапуск не включён${NC}"
    exit 0
fi

rm -f "$AUTOSTART_FILE"

echo -e "${GREEN}✅ Autostart disabled / Автозапуск выключен${NC}"
echo ""
echo -e "${CYAN}️  Gamma will no longer start automatically${NC}"
echo -e "${CYAN}ℹ️  Gamma больше не будет запускаться автоматически${NC}"
echo ""
echo -e "To enable / Чтобы включить:"
echo -e "   ./enable-autostart.sh"
echo ""

exit 0