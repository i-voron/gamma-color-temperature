#!/bin/bash
# ============================================================
# Gamma — Color Temperature Manager
# Installation script / Скрипт установки
# ============================================================

set -e

# Colors for output / Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color / Без цвета

# Get script directory (works even if called from another dir)
# Получаем директорию скрипта (работает даже при вызове из другой папки)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Application files / Файлы приложения
GAMMA_PY="$SCRIPT_DIR/gamma.py"
GAMMA_ICON="$SCRIPT_DIR/gamma.png"
GAMMA_ICON_SVG="$SCRIPT_DIR/gamma.svg"

# Installation targets / Цели установки
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_FILE="$DESKTOP_DIR/gamma.desktop"
ICON_FILE="$ICON_DIR/gamma.png"

# ============================================================
# Functions / Функции
# ============================================================

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}==================================================${NC}"
    echo -e "${CYAN}${BOLD}  Gamma — Color Temperature Manager${NC}"
    echo -e "${CYAN}${BOLD}  Installation Script / Скрипт установки${NC}"
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

check_dependencies() {
    print_info "Checking dependencies / Проверка зависимостей..."
    
    local missing=()
    
    # Check Python 3 / Проверяем Python 3
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    # Check xrandr / Проверяем xrandr
    if ! command -v xrandr &> /dev/null; then
        missing+=("xrandr")
    fi
    
    # Check tkinter (via python3) / Проверяем tkinter
    if ! python3 -c "import tkinter" 2>/dev/null; then
        missing+=("python3-tk")
    fi
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing dependencies / Отсутствуют зависимости:"
        for dep in "${missing[@]}"; do
            echo "   • $dep"
        done
        echo ""
        print_info "Install them with / Установите их командой:"
        echo "   sudo apt install ${missing[*]}"
        exit 1
    fi
    
    print_success "All dependencies found / Все зависимости найдены"
}

check_files() {
    print_info "Checking application files / Проверка файлов приложения..."
    
    if [ ! -f "$GAMMA_PY" ]; then
        print_error "gamma.py not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Make gamma.py executable / Делаем gamma.py исполняемым
    chmod +x "$GAMMA_PY"
    print_success "gamma.py found and made executable"
    
    # Check icon (PNG or SVG) / Проверяем иконку
    if [ -f "$GAMMA_ICON" ]; then
        print_success "gamma.png icon found"
    elif [ -f "$GAMMA_ICON_SVG" ]; then
        print_warning "gamma.png not found, but gamma.svg exists"
        print_info "You may want to convert SVG to PNG for better compatibility"
    else
        print_warning "No icon found (gamma.png or gamma.svg)"
    fi
}

create_desktop_file() {
    print_info "Creating .desktop file / Создание .desktop файла..."
    
    # Create target directory / Создаём целевую директорию
    mkdir -p "$DESKTOP_DIR"
    
    # Get absolute paths / Получаем абсолютные пути
    local abs_gamma_py
    abs_gamma_py="$(realpath "$GAMMA_PY")"
    
    local abs_icon
    if [ -f "$GAMMA_ICON" ]; then
        abs_icon="$(realpath "$GAMMA_ICON")"
    elif [ -f "$GAMMA_ICON_SVG" ]; then
        abs_icon="$(realpath "$GAMMA_ICON_SVG")"
    else
        abs_icon="gamma"  # Use system icon fallback / Используем системную иконку
    fi
    
    # Create desktop file / Создаём desktop файл
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Gamma
Comment=Color Temperature Manager
Exec=$abs_gamma_py
Icon=$abs_icon
Terminal=false
Categories=Utility;Settings;HardwareSettings;
Keywords=gamma;color;temperature;display;monitor;
StartupNotify=false
EOF
    
    # Make executable / Делаем исполняемым
    chmod +x "$DESKTOP_FILE"
    
    print_success "Desktop file created at $DESKTOP_FILE"
}

install_icon() {
    if [ -f "$GAMMA_ICON" ]; then
        print_info "Installing icon / Установка иконки..."
        mkdir -p "$ICON_DIR"
        cp "$GAMMA_ICON" "$ICON_FILE"
        print_success "Icon installed to $ICON_FILE"
    fi
}

update_desktop_cache() {
    print_info "Updating desktop database / Обновление базы данных приложений..."
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
        print_success "Desktop database updated"
    else
        print_warning "update-desktop-database not found, skipping"
    fi
    
    # Also try gtk-update-icon-cache for icons / Также пробуем обновить кэш иконок
    if command -v gtk-update-icon-cache &> /dev/null && [ -f "$ICON_FILE" ]; then
        gtk-update-icon-cache -f "$ICON_DIR" 2>/dev/null || true
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}==================================================${NC}"
    echo -e "${GREEN}${BOLD}  Installation Complete! / Установка завершена!${NC}"
    echo -e "${GREEN}${BOLD}==================================================${NC}"
    echo ""
    echo -e "🎨 ${CYAN}${BOLD}Gamma${NC} is now installed!"
    echo ""
    echo "📍 Desktop file: $DESKTOP_FILE"
    [ -f "$ICON_FILE" ] && echo "🖼️  Icon: $ICON_FILE"
    echo ""
    echo " You can now:"
    echo "   • Find Gamma in your applications menu / Найти Gamma в меню приложений"
    echo "   • Run from terminal: $GAMMA_PY"
    echo "   • Assign keyboard shortcuts / Назначить горячие клавиши"
    echo ""
    echo "📋 CLI examples / Примеры CLI:"
    echo "   $GAMMA_PY --next          # Next preset / Следующий пресет"
    echo "   $GAMMA_PY --slot 1        # Slot 1 / Слот 1"
    echo "   $GAMMA_PY --preset 6500K  # By name / По имени"
    echo ""
    echo "🗑️  To uninstall / Чтобы удалить:"
    echo "   $SCRIPT_DIR/uninstall.sh"
    echo ""
}

# ============================================================
# Main / Основная логика
# ============================================================

print_header

# Check if already installed / Проверяем, не установлено ли уже
if [ -f "$DESKTOP_FILE" ]; then
    print_warning "Gamma is already installed / Gamma уже установлена"
    read -p "Reinstall? / Переустановить? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled / Установка отменена"
        exit 0
    fi
fi

check_dependencies
check_files
create_desktop_file
install_icon
update_desktop_cache
print_summary

exit 0