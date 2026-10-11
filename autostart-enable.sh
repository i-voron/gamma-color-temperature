#!/bin/bash
# ============================================================
# Gamma — Enable Autostart / Включить автозапуск
# ============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAMMA_PY="$SCRIPT_DIR/gamma.py"

echo ""
echo -e "${CYAN}${BOLD}==================================================${NC}"
echo -e "${CYAN}${BOLD}  Gamma — Enable Autostart${NC}"
echo -e "${CYAN}${BOLD}  Включить автозапуск${NC}"
echo -e "${CYAN}${BOLD}==================================================${NC}"
echo ""

# Check if gamma.py exists
if [ ! -f "$GAMMA_PY" ]; then
    echo -e "${RED}❌ gamma.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Create autostart directory
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Create .desktop file
AUTOSTART_FILE="$AUTOSTART_DIR/gamma-restore.desktop"
ABS_GAMMA_PY="$(realpath "$GAMMA_PY")"

cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Gamma Restore
Comment=Restore last applied gamma on login
Exec=$ABS_GAMMA_PY --restore
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$AUTOSTART_FILE"

echo -e "${GREEN}✅ Autostart enabled / Автозапуск включён${NC}"
echo ""
echo -e "📍 File: $AUTOSTART_FILE"
echo ""
echo -e "${CYAN}ℹ️  Gamma will restore your last settings on login${NC}"
echo -e "${CYAN}️  Gamma восстановит последние настройки при входе в систему${NC}"
echo ""
echo -e "To disable / Чтобы отключить:"
echo -e "   ./disable-autostart.sh"
echo ""

exit 0