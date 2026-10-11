# ============================================================
# Gamma — Color Temperature Manager
# Makefile for installation and management
# ============================================================

# Variables / Переменные
APP_NAME := Gamma
PYTHON := python3
SCRIPT := gamma.py
ICON_PNG := gamma.png
ICON_SVG := gamma.svg

# Installation paths / Пути установки
DESKTOP_DIR := $(HOME)/.local/share/applications
ICON_DIR := $(HOME)/.local/share/icons
DESKTOP_FILE := $(DESKTOP_DIR)/gamma.desktop
ICON_FILE := $(ICON_DIR)/gamma.png

# Current directory / Текущая директория
CURDIR := $(shell pwd)
ABS_SCRIPT := $(CURDIR)/$(SCRIPT)
ABS_ICON := $(CURDIR)/$(ICON_PNG)

# Colors for output / Цвета для вывода
BOLD := \033[1m
GREEN := \033[0;32m
YELLOW := \033[1;33m
CYAN := \033[0;36m
RED := \033[0;31m
NC := \033[0m

# ============================================================
# Targets / Цели
# ============================================================

.PHONY: help install uninstall run test clean check-deps

# Default target / Цель по умолчанию
.DEFAULT_GOAL := help

# Show help / Показать помощь
help:
	@echo ""
	@echo -e "$(BOLD)$(CYAN)==================================================$(NC)"
	@echo -e "$(BOLD)$(CYAN)  Gamma — Color Temperature Manager$(NC)"
	@echo -e "$(BOLD)$(CYAN)==================================================$(NC)"
	@echo ""
	@echo -e "$(BOLD)Available targets / Доступные цели:$(NC)"
	@echo ""
	@echo -e "  $(GREEN)make install$(NC)      Install to system / Установить в систему"
	@echo -e "  $(GREEN)make uninstall$(NC)    Remove from system / Удалить из системы"
	@echo -e "  $(GREEN)make run$(NC)          Launch GUI / Запустить GUI"
	@echo -e "  $(GREEN)make test$(NC)         Check dependencies / Проверить зависимости"
	@echo -e "  $(GREEN)make clean$(NC)        Remove config and logs / Удалить конфиг и логи"
	@echo -e "  $(GREEN)make check-deps$(NC)   Check only dependencies / Только проверка зависимостей"
	@echo ""
	@echo -e "$(BOLD)CLI examples / Примеры CLI:$(NC)"
	@echo -e "  $(PYTHON) $(SCRIPT) --next          # Next preset / Следующий пресет"
	@echo -e "  $(PYTHON) $(SCRIPT) --slot 1        # Slot 1 / Слот 1"
	@echo -e "  $(PYTHON) $(SCRIPT) --preset 6500K  # By name / По имени"
	@echo ""

# Check dependencies / Проверить зависимости
check-deps:
	@echo -e "$(CYAN)ℹ️  Checking dependencies / Проверка зависимостей...$(NC)"
	@MISSING=""; \
	if ! command -v $(PYTHON) &> /dev/null; then MISSING="$$MISSING python3"; fi; \
	if ! command -v xrandr &> /dev/null; then MISSING="$$MISSING xrandr"; fi; \
	if ! $(PYTHON) -c "import tkinter" 2>/dev/null; then MISSING="$$MISSING python3-tk"; fi; \
	if [ -n "$$MISSING" ]; then \
		echo -e "$(RED)❌ Missing dependencies / Отсутствуют зависимости:$$MISSING$(NC)"; \
		echo -e "$(CYAN)ℹ️  Install with / Установите:$(NC) sudo apt install$$MISSING"; \
		exit 1; \
	else \
		echo -e "$(GREEN)✅ All dependencies found / Все зависимости найдены$(NC)"; \
	fi

# Install / Установить
install: check-deps
	@echo ""
	@echo -e "$(CYAN)ℹ️  Installing $(APP_NAME)...$(NC)"
	@mkdir -p $(DESKTOP_DIR) $(ICON_DIR)
	@chmod +x $(SCRIPT)
	@echo "[Desktop Entry]" > $(DESKTOP_FILE)
	@echo "Version=1.0" >> $(DESKTOP_FILE)
	@echo "Type=Application" >> $(DESKTOP_FILE)
	@echo "Name=$(APP_NAME)" >> $(DESKTOP_FILE)
	@echo "Comment=Color Temperature Manager" >> $(DESKTOP_FILE)
	@echo "Exec=$(ABS_SCRIPT)" >> $(DESKTOP_FILE)
	@if [ -f $(ICON_PNG) ]; then \
		echo "Icon=$(ABS_ICON)" >> $(DESKTOP_FILE); \
		cp $(ICON_PNG) $(ICON_FILE); \
		echo -e "$(GREEN)✅ Icon installed$(NC)"; \
	elif [ -f $(ICON_SVG) ]; then \
		echo "Icon=$(CURDIR)/$(ICON_SVG)" >> $(DESKTOP_FILE); \
		echo -e "$(YELLOW)⚠️  Using SVG icon (PNG recommended)$(NC)"; \
	else \
		echo "Icon=gamma" >> $(DESKTOP_FILE); \
		echo -e "$(YELLOW)⚠️  No icon found$(NC)"; \
	fi
	@echo "Terminal=false" >> $(DESKTOP_FILE)
	@echo "Categories=Utility;Settings;HardwareSettings;" >> $(DESKTOP_FILE)
	@echo "Keywords=gamma;color;temperature;display;monitor;" >> $(DESKTOP_FILE)
	@echo "StartupNotify=false" >> $(DESKTOP_FILE)
	@chmod +x $(DESKTOP_FILE)
	@-update-desktop-database $(DESKTOP_DIR) 2>/dev/null || true
	@-gtk-update-icon-cache -f $(ICON_DIR) 2>/dev/null || true
	@echo ""
	@echo -e "$(GREEN)$(BOLD)==================================================$(NC)"
	@echo -e "$(GREEN)$(BOLD)  Installation Complete! / Установка завершена!$(NC)"
	@echo -e "$(GREEN)$(BOLD)==================================================$(NC)"
	@echo ""
	@echo -e "🎨 $(CYAN)$(BOLD)$(APP_NAME)$(NC) installed successfully!"
	@echo " Desktop file: $(DESKTOP_FILE)"
	@echo ""
	@echo "🚀 Run with: make run"
	@echo "️  Remove with: make uninstall"
	@echo ""

# Uninstall / Удалить
uninstall:
	@echo ""
	@echo -e "$(CYAN)ℹ️  Uninstalling $(APP_NAME)...$(NC)"
	@if [ -f $(DESKTOP_FILE) ]; then \
		rm -f $(DESKTOP_FILE); \
		echo -e "$(GREEN)✅ Desktop file removed$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠️  Desktop file not found$(NC)"; \
	fi
	@if [ -f $(ICON_FILE) ]; then \
		rm -f $(ICON_FILE); \
		echo -e "$(GREEN)✅ Icon removed$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠️  Icon not found$(NC)"; \
	fi
	@-update-desktop-database $(DESKTOP_DIR) 2>/dev/null || true
	@-gtk-update-icon-cache -f $(ICON_DIR) 2>/dev/null || true
	@echo ""
	@echo -e "$(GREEN)$(BOLD)==================================================$(NC)"
	@echo -e "$(GREEN)$(BOLD)  Uninstallation Complete! / Удаление завершено!$(NC)"
	@echo -e "$(GREEN)$(BOLD)==================================================$(NC)"
	@echo ""
	@echo -e "$(GREEN)✅ $(APP_NAME) uninstalled$(NC)"
	@echo "💡 Your settings are still in: $(CURDIR)/gamma_config.json"
	@echo ""

# Run / Запустить
run:
	@$(PYTHON) $(SCRIPT)

# Test / Проверка (запуск с проверкой)
test: check-deps
	@echo ""
	@echo -e "$(CYAN)ℹ️  Running $(APP_NAME) in test mode...$(NC)"
	@$(PYTHON) $(SCRIPT)

# Clean / Очистить (удалить конфиг и логи)
clean:
	@echo -e "$(YELLOW)⚠️  This will remove config and log files!$(NC)"
	@read -p "Continue? / Продолжить? [y/N] " REPLY && \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		rm -f gamma_config.json gamma_config.json.bak gamma.log; \
		echo -e "$(GREEN)✅ Cleaned$(NC)"; \
	else \
		echo "Cancelled"; \
	fi