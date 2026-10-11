#!/bin/bash
# ============================================================
# Gamma — Color Temperature Manager
# Uninstallation script / Скрипт удаления
# ============================================================

set -e

# Colors for output / Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color / Без цвета

# Installation targets / Цели установки
DESKTOP_FILE="$HOME/.local/share/applications/gamma.desktop"
ICON_FILE="$HOME/.local/share/icons/gamma.png"

# ============================================================
# Functions / Функции
# ============================================================

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}==================================================${NC}"
    echo -e "${CYAN}${BOLD}  Gamma — Color Temperature Manager${NC}"
    echo -e "${CYAN}${BOLD}  Uninstallation Script / Скрипт удаления${NC}"
    echo -e "${CYAN}${BOLD}==================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ============================================================
# Main / Основная логика
# ============================================================

print_header

# Check if installed / Проверяем, установлено ли
if [ ! -f "$DESKTOP_FILE" ] && [ ! -f "$ICON_FILE" ]; then
    print_warning "Gamma is not installed / Gamma не установлена"
    print_info "Nothing to uninstall / Нечего удалять"
    exit 0
fi

# Show what will be removed / Показываем, что будет удалено
print_info "The following files will be removed / Будут удалены следующие файлы:"
[ -f "$DESKTOP_FILE" ] && echo "   • $DESKTOP_FILE"
[ -f "$ICON_FILE" ] && echo "   • $ICON_FILE"
echo ""

# Ask for confirmation / Запрашиваем подтверждение
read -p "Continue? / Продолжить? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Uninstallation cancelled / Удаление отменено"
    exit 0
fi

# Remove desktop file / Удаляем desktop файл
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    print_success "Desktop file removed / Desktop файл удалён"
fi

# Remove icon / Удаляем иконку
if [ -f "$ICON_FILE" ]; then
    rm -f "$ICON_FILE"
    print_success "Icon removed / Иконка удалена"
fi

# Update desktop database / Обновляем базу данных
print_info "Updating desktop database / Обновление базы данных приложений..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons" 2>/dev/null || true
fi

# Summary / Итог
echo ""
echo -e "${GREEN}${BOLD}==================================================${NC}"
echo -e "${GREEN}${BOLD}  Uninstallation Complete! / Удаление завершено!${NC}"
echo -e "${GREEN}${BOLD}==================================================${NC}"
echo ""
print_success "Gamma has been uninstalled from your system"
print_info "Your presets and settings are still in:"
echo "   $(dirname "$DESKTOP_FILE")/../gamma_config.json"
echo ""
print_info "To reinstall / Чтобы переустановить:"
echo "   ./install.sh"
echo ""

exit 0