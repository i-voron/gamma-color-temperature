#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Gamma Project

"""
Gamma — Color Temperature Manager v1.0
Color temperature preset manager for Linux with GUI and CLI.
Менеджер пресетов цветовой температуры для Linux с GUI и CLI.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import re
import sys
import os
import json
import argparse
import colorsys
import time
import logging
import signal
import threading
import locale
import fcntl
import tempfile
from concurrent.futures import Future
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path

# =============================================================================
# FILE CONFIGURATION / КОНФИГУРАЦИЯ ФАЙЛОВ
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
"""Directory containing the script / Директория, содержащая скрипт."""

CONFIG_FILE = os.path.join(SCRIPT_DIR, "gamma_config.json")
"""Path to configuration file / Путь к файлу конфигурации."""

CONFIG_BACKUP_SUFFIX = ".bak"
"""Suffix for config backup file / Суффикс для файла резервной копии конфига."""

INSTANCE_LOCK_NAME = "\0gamma_lock"
"""Legacy Unix socket name for single-instance lock (no longer used; kept for backward compat) /
Устаревшее имя Unix-сокета для блокировки единственного экземпляра (больше не используется; оставлено для обратной совместимости)."""

LOG_FILE = os.path.join(SCRIPT_DIR, "gamma.log")
"""Path to log file / Путь к файлу лога."""

ICON_FILENAME = "gamma.png"
"""Default icon filename / Имя файла иконки по умолчанию."""

EXPORT_DEFAULT_FILENAME = "gamma_presets.json"
"""Default filename for export / Имя файла по умолчанию для экспорта."""

# =============================================================================
# APPLICATION VERSION / ВЕРСИЯ ПРИЛОЖЕНИЯ
# =============================================================================

APP_VERSION = "1.0"
"""Current application version / Текущая версия приложения."""

# =============================================================================
# WINDOW AND PANEL SIZES / РАЗМЕРЫ ОКНА И ПАНЕЛЕЙ
# =============================================================================

CONTENT_FIXED_WIDTH = 480  # Width of left content panel
STRIP_WIDTH = 20  # Width of toggle strip
LIBRARY_WIDTH = 260  # Default width of library panel
MIN_LIBRARY_WIDTH = 260  # Minimum width of library panel (user can't drag narrower)
MIN_WINDOW_HEIGHT = 400  # Minimum window height
HEIGHT_RESERVE = 10  # Extra height for window chrome

# =============================================================================
# UI PADDING / ОТСТУПЫ UI
# =============================================================================

INNER_PADX = 5  # Inner horizontal padding
INNER_PADY = 5  # Inner vertical padding
SECTION_PADY = (0, 10)  # Section vertical padding
BUTTON_PADY = 5  # Button vertical padding
CANVAS_PADX = 5  # Canvas horizontal padding
HEADER_PADY = 5  # Header vertical padding
SEARCH_PADX = 5  # Search horizontal padding
SEARCH_PADY = (0, 5)  # Search vertical padding
TREEVIEW_PADX = 5  # Treeview horizontal padding
IMPORT_EXPORT_PADX = 2  # Import

# =============================================================================
# ELEMENT COUNTS / КОЛИЧЕСТВО ЭЛЕМЕНТОВ
# =============================================================================

MAX_FAVORITES = 5  # Maximum number of favorite presets
BUTTONS_PER_ROW = 2  # Monitor buttons per row

# =============================================================================
# FONTS / ШРИФТЫ
# =============================================================================

FONT_MONITOR = ("Arial", 11, "bold")  # Font for monitor buttons
FONT_FAVORITE = ("Arial", 11)  # Font for favorite buttons
FONT_LIBRARY_HEADER = ("Arial", 9, "bold")  # Font for library header
FONT_SEARCH = ("Arial", 9)  # Font for search entry
FONT_TREEVIEW = ("Arial", 9)  # Font for treeview
FONT_SLIDER_LABEL = ("Courier New", 10)  # Font for slider labels
FONT_DIALOG = ("Arial", 10)  # Font for dialogs
FONT_TOOLTIP = ("Arial", 9)  # Font for tooltips
FONT_MESSAGE_ICON = ("Arial", 24)  # Font for message dialog icon
SLIDER_BUTTON_FONT = ("Arial", 12, "bold")  # Larger, bolder +/- button glyphs

# =============================================================================
# MONITOR BUTTON PADDING / ОТСТУПЫ КНОПОК МОНИТОРОВ
# =============================================================================

MONITOR_BTN_WIDTH = 12  # Width of monitor button
MONITOR_BTN_PADX = 4  # Horizontal padding for monitor buttons
MONITOR_BTN_PADY = 3  # Vertical padding for monitor buttons
MONITOR_BTN_IPADY = 5  # Internal vertical padding for monitor buttons

# =============================================================================
# FAVORITE BUTTON PADDING / ОТСТУПЫ КНОПОК ИЗБРАННОГО
# =============================================================================

FAV_BTN_HEIGHT = 1  # Height of favorite button
FAV_BTN_PADY = 1  # Vertical padding for favorite buttons

# =============================================================================
# SLIDER PADDING / ОТСТУПЫ СЛАЙДЕРОВ
# =============================================================================

SLIDER_FRAME_PADX = 10  # Horizontal padding for slider frame
SLIDER_FRAME_PADY = 5  # Vertical padding for slider frame
SLIDER_LABEL_WIDTH = 20  # Width of slider label — enough for "Красный (R): 1.00"
SLIDER_ROW_PADY = 4  # Vertical padding for slider row (more breathing room)

# Color indicator (small colored square next to each channel label)
# / Цветной индикатор (маленький цветной квадрат рядом с меткой канала)
SLIDER_INDICATOR_SIZE = 12  # Square size in pixels
SLIDER_INDICATOR_PADX = (0, 4)  # Padding: right of the square, before the label

# Slider trough thickness (vertical height of the groove).
# For a HORIZONTAL tk.Scale this is passed as the `width` option (NOT `height`,
# which is a ttk.Scale-only option and raises TclError on tk.Scale).
# / Толщина жёлоба слайдера (вертикальная высота канавки).
# Для ГОРИЗОНТАЛЬНОГО tk.Scale передаётся как опция `width` (НЕ `height` —
# это опция только ttk.Scale, на tk.Scale вызывает TclError).
SLIDER_TROUGH_HEIGHT = 22  # px — thicker trough for easier grab
SPINBOX_ARROWSIZE = 30  # px — height of TSpinbox up/down arrows (also scales with UI)

# =============================================================================
# SLIDER STEP BUTTONS / КНОПКИ ШАГА СЛАЙДЕРА
# =============================================================================

SLIDER_STEP = 0.01  # Slider step increment
SLIDER_BTN_WIDTH = 1  # Width of slider +/- buttons (chars)
SLIDER_BTN_PADY = 0  # Vertical padding inside slider buttons
SLIDER_BTN_MINUS_PADX = (0, 3)  # Horizontal padding for minus button (symmetric)
SLIDER_BTN_PLUS_PADX = (3, 0)  # Horizontal padding for plus button (symmetric)

# =============================================================================
# AUTO-REPEAT SETTINGS / НАСТРОЙКИ АВТОПОВТОРА
# =============================================================================

AUTO_REPEAT_DELAY = 300  # Delay before auto-repeat starts (ms)
AUTO_REPEAT_INTERVAL = 50  # Interval between auto-repeat events (ms)
APPLY_GAMMA_THROTTLE_MS = 50  # Min interval between xrandr calls on slider drag/hold (ms)

# =============================================================================
# UI SCALE CONFIGURATION / НАСТРОЙКИ МАСШТАБА UI
# =============================================================================

# UI scale configuration
UI_SCALE_MIN = 0.75  # Minimum UI scale factor
UI_SCALE_MAX = 3.0  # Maximum UI scale factor
UI_SCALE_STEP = 0.25  # Step for UI scale changes (Ctrl++ / Ctrl+-)


def round_to_scale_step(value: float, step: float = UI_SCALE_STEP) -> float:
    """Round a scale factor to the nearest step (e.g. 1.221 -> 1.25)."""
    return round(value / step) * step

# =============================================================================
# DIALOG SIZES / РАЗМЕРЫ ДИАЛОГОВ
# =============================================================================

DIALOG_WIDTH = 380  # Width of standard dialogs (was 300 — widened for spinbox layout)
DIALOG_HEIGHT = 140  # Height of standard dialogs
DIALOG_COMMENT_HEIGHT = 65  # Extra height for comment field (was 60)
DIALOG_ENTRY_WIDTH = 30  # Width of dialog entry fields
DIALOG_OFFSET_X = 150  # Dialog horizontal offset from center
DIALOG_OFFSET_Y = 70  # Dialog vertical offset from center
DIALOG_LABEL_PADY = (15, 5)  # Vertical padding for dialog labels
DIALOG_BUTTON_PADY = (5, 5)  # Vertical padding for dialog buttons (was 15,15)
DIALOG_ENTRY_PADY = 5  # Vertical padding for dialog entries
DIALOG_VALIDATE_DELAY_MS = 10  # Delay for dialog validation (ms)

# =============================================================================
# MESSAGE DIALOG SIZES / РАЗМЕРЫ ДИАЛОГОВ СООБЩЕНИЙ
# =============================================================================

MESSAGE_DIALOG_WIDTH = 350  # Width of message dialogs
MESSAGE_DIALOG_HEIGHT = 150  # Height of message dialogs
MESSAGE_ICON_PADX = (0, 15)  # Horizontal padding for message icon
MESSAGE_FRAME_PADX = 20  # Horizontal padding for message frame
MESSAGE_FRAME_PADY = 20  # Vertical padding for message frame
MESSAGE_TEXT_WRAPLENGTH = 250  # Wrap length for message text
MESSAGE_BUTTON_PADY = (0, 15)  # Vertical padding for message button
MESSAGE_BUTTON_PADX = 15  # Horizontal padding for message button
MESSAGE_BUTTON_INNER_PADY = 5  # Internal vertical padding for message button

# =============================================================================
# TREEVIEW SIZES / РАЗМЕРЫ TREEVIEW
# =============================================================================

TREEVIEW_ROWHEIGHT = 36  # Height of treeview row
TREEVIEW_HEIGHT = 10  # Number of visible rows in treeview
TREEVIEW_WRAPPER_X = 5  # Horizontal padding for treeview wrapper (used in pack padx)

# =============================================================================
# TEST STRIP SIZE / РАЗМЕР ТЕСТОВОЙ ПОЛОСКИ
# =============================================================================

CANVAS_HEIGHT = 40  # Height of test color strip
CANVAS_MIN_WIDTH = 10  # Minimum canvas width before fallback
CANVAS_WIDTH_MARGIN = 20  # Margin for canvas width calculation

# =============================================================================
# SLIDER PARAMETERS / ПАРАМЕТРЫ СЛАЙДЕРОВ
# =============================================================================

SLIDER_MIN = 0.01  # Minimum slider value
SLIDER_MAX = 1.0  # Maximum slider value
SLIDER_LENGTH = 24  # Length of slider knob (wider for easier grabbing)
GAMMA_MAX_VALUE = 3.0  # Maximum allowed gamma value

# =============================================================================
# XRANDR SETTINGS / НАСТРОЙКИ XRANDR
# =============================================================================

XRANDR_TIMEOUT = 5  # Timeout for xrandr calls (seconds)
XRANDR_MAX_RETRIES = 2  # Maximum retry attempts for xrandr
XRANDR_RETRY_DELAY = 0.5  # Delay between xrandr retries (seconds)
MONITORS_CACHE_TTL = 2.0  # Monitor list cache TTL (seconds)

# =============================================================================
# LOGGING SETTINGS / НАСТРОЙКИ ЛОГИРОВАНИЯ
# =============================================================================

LOG_MAX_SIZE = 1024 * 1024  # Maximum log file size (1 MB)
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(message)s"  # Log message format
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # Log date format

# =============================================================================
# UI COLORS / ЦВЕТА ИНТЕРФЕЙСА
# =============================================================================

COLOR_CHANNEL_RED = "#e74c3c"  # Red channel accent color
COLOR_CHANNEL_GREEN = "#27ae60"  # Green channel accent color
COLOR_CHANNEL_BLUE = "#2980b9"  # Blue channel accent color
COLOR_CHANNEL_DEFAULT = "#3498db"  # Default accent color
COLOR_FOCUS = "#3498db"  # Focus border color
COLOR_ACTIVE_BORDER = "#FFA500"  # Active preset border color (orange)
COLOR_INACTIVE_BORDER_DARK = "#555555"  # Inactive border in dark theme
COLOR_INACTIVE_BORDER_LIGHT = "#999999"  # Inactive border in light theme
COLOR_TEXT_BLACK = "#000000"  # Black text color
COLOR_TEXT_WHITE = "#ffffff"  # White text color
COLOR_TEXT_GRAY = "gray"  # Gray text color
COLOR_BRIGHTNESS_THRESHOLD = 0.6  # Threshold for text color selection

# =============================================================================
# DIALOG FIELD COLORS / ЦВЕТА ПОЛЕЙ ДИАЛОГОВ
# =============================================================================

DIALOG_FIELD_BG = "#ffffff"  # Background color for dialog input fields
DIALOG_FIELD_FG = "#000000"  # Text color for dialog input fields
DIALOG_FIELD_CURSOR = "#000000"  # Cursor color for dialog input fields

# =============================================================================
# TOOLTIP SETTINGS / НАСТРОЙКИ ПОДСКАЗОК
# =============================================================================

TOOLTIP_BG = "#ffffe0"  # Tooltip background color
TOOLTIP_FG = "#000000"  # Tooltip text color
TOOLTIP_MAX_WIDTH = 300  # Maximum tooltip width
TOOLTIP_PADDING = 6  # Tooltip text padding
TOOLTIP_OFFSET_X = 15  # Tooltip X offset from cursor
TOOLTIP_OFFSET_Y = 10  # Tooltip Y offset from cursor
TOOLTIP_DELAY_MS = 500  # Delay before tooltip appears (ms)

# =============================================================================
# COMMENT FIELD SIZES / РАЗМЕРЫ ПОЛЯ КОММЕНТАРИЯ
# =============================================================================

COMMENT_TEXT_HEIGHT = 3  # Height of comment text field
COMMENT_TEXT_PADX = 20  # Horizontal padding for comment field

# =============================================================================
# BORDER THICKNESS / ТОЛЩИНА РАМОК
# =============================================================================

FAV_BUTTON_BORDER_THICKNESS = 1  # Border thickness for favorite buttons
FAV_BUTTON_ACTIVE_HIGHLIGHT = 1  # Highlight thickness for active favorite
FAV_BUTTON_INACTIVE_HIGHLIGHT = 0  # Highlight thickness for inactive favorite
MONITOR_BUTTON_HIGHLIGHT = 1  # Highlight thickness for monitor buttons
SLIDER_BUTTON_HIGHLIGHT = 1  # Highlight thickness for slider buttons
GENERAL_BUTTON_HIGHLIGHT = 1  # Highlight thickness for general buttons

# =============================================================================
# HOVER FACTORS / КОЭФФИЦИЕНТЫ НАВЕДЕНИЯ
# =============================================================================

HOVER_FACTOR_DARK = 0.85  # Darken factor on hover in dark theme
HOVER_FACTOR_LIGHT = 1.15  # Lighten factor on hover in light theme

# =============================================================================
# SUBPROCESS TIMEOUTS / ТАЙМАУТЫ SUBPROCESS
# =============================================================================

ZENITY_TIMEOUT = 60  # Timeout for zenity dialogs (seconds)
ZENITY_CHECK_TIMEOUT = 2  # Timeout for zenity version check

# =============================================================================
# TEST STRIP GRADIENT COLORS / ЦВЕТА ГРАДИЕНТА ТЕСТОВОЙ ПОЛОСКИ
# =============================================================================

GRADIENT_COLORS = [
    "#FF0000",
    "#FFFF00",
    "#00FF00",
    "#00FFFF",
    "#0000FF",
    "#FF00FF",
]  # Gradient colors for test strip / Цвета градиента тестовой полоски

# =============================================================================
# MESSAGE DIALOG ICONS / ИКОНКИ ДИАЛОГОВ СООБЩЕНИЙ
# =============================================================================


class MessageType(Enum):
    """Message dialog types / Типы диалогов сообщений."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


MESSAGE_ICONS = {
    MessageType.INFO: "ℹ️",
    MessageType.SUCCESS: "✅",
    MessageType.WARNING: "⚠️",
    MessageType.ERROR: "❌",
}  # Icons for message dialog types / Иконки для типов диалогов сообщений

MESSAGE_ICON_DEFAULT = "ℹ️"  # Default icon for unknown message types

# =============================================================================
# PRESET MARKERS / МАРКЕРЫ ПРЕСЕТОВ
# =============================================================================

MARKER_ACTIVE_PREFIX = "▶ "  # Prefix marker for active preset
MARKER_ACTIVE_SUFFIX = " ◀"  # Suffix marker for active preset
MARKER_FAVORITE_PREFIX = "★ "  # Prefix marker for favorite preset

# =============================================================================
# DISPLAY FORMATS / ФОРМАТЫ ОТОБРАЖЕНИЯ
# =============================================================================

PRESET_DISPLAY_FORMAT = (
    "#{id} {name}\nR: {r:.2f}   G: {g:.2f}   B: {b:.2f}"  # Preset display format
)
RGB_FORMAT = "R: {r:.2f} G: {g:.2f} B: {b:.2f}"  # RGB values format
CLI_MONITOR_FORMAT = "  {i}. {name}\n     Mode: {mode}"  # CLI monitor format
CLI_GAMMA_FORMAT = "  {status} {name}: RGB {r:.2f}, {g:.2f}, {b:.2f}"  # CLI gamma format

# =============================================================================
# ICON COORDINATES / КООРДИНАТЫ ИКОНКИ
# =============================================================================

ICON_RED_RECT = [32, 52, 224, 88]  # Red rectangle coordinates
ICON_GREEN_RECT = [32, 110, 224, 146]  # Green rectangle coordinates
ICON_BLUE_RECT = [32, 168, 224, 204]  # Blue rectangle coordinates
ICON_RED_DOT = [116, 46, 164, 94]  # Red dot coordinates
ICON_GREEN_DOT = [146, 104, 194, 152]  # Green dot coordinates
ICON_BLUE_DOT = [86, 162, 134, 210]  # Blue dot coordinates
ICON_COLOR_RED = (239, 68, 68)  # Red channel color for icon elements
ICON_COLOR_GREEN = (34, 197, 94)  # Green channel color for icon elements
ICON_COLOR_BLUE = (59, 130, 246)  # Blue channel color for icon elements
ICON_GRADIENT_R_START = 124  # Icon gradient R start value
ICON_GRADIENT_R_END = 59  # Icon gradient R end value
ICON_GRADIENT_G_START = 58  # Icon gradient G start value
ICON_GRADIENT_G_END = 130  # Icon gradient G end value
ICON_GRADIENT_B_START = 237  # Icon gradient B start value
ICON_GRADIENT_B_END = 246  # Icon gradient B end value

# =============================================================================
# TOGGLE ARROW COORDINATES / КООРДИНАТЫ СТРЕЛКИ ПЕРЕКЛЮЧЕНИЯ
# =============================================================================

ARROW_RIGHT_X_BASE = 12  # Right arrow X base coordinate
ARROW_RIGHT_Y_OFFSETS = (-6, 6, 0)  # Right arrow Y offsets from base
ARROW_RIGHT_X_OFFSETS = (0, 0, -6)  # Right arrow X offsets from base
ARROW_LEFT_X_BASE = 8  # Left arrow X base coordinate
ARROW_LEFT_Y_OFFSETS = (-6, 6, 0)  # Left arrow Y offsets from base
ARROW_LEFT_X_OFFSETS = (0, 0, 6)  # Left arrow X offsets from base

# =============================================================================
# CONFIG KEYS / КЛЮЧИ КОНФИГУРАЦИИ
# =============================================================================

CFG_KEY_MONITOR = "monitor"  # Monitor name key
CFG_KEY_MONITOR_GAMMAS = "monitor_gammas"  # Monitor gammas key
CFG_KEY_LAST_RGB = "last_rgb"  # Last RGB values key
CFG_KEY_AVAILABLE_MONITORS = "available_monitors"  # Available monitors key
CFG_KEY_RIGHT_PANEL = "right_panel_visible"  # Right panel visibility key
CFG_KEY_WINDOW_GEOMETRY = "window_geometry"  # Window geometry key
CFG_KEY_LANGUAGE = "language"  # Language key
CFG_KEY_UI_SCALE = "ui_scale"  # User-saved UI scale factor (overrides auto-DPI)
CFG_KEY_PRESETS = "presets"  # Presets list key
CFG_KEY_FAVORITES = "favorites"  # Favorites list key
CFG_KEY_UI_SETTINGS = "ui_settings"  # UI settings key
CFG_KEY_SYSTEM_SETTINGS = "system_settings"  # System settings key
CFG_KEY_LAST_CLI_SLOT = "last_cli_slot_index"  # Last CLI slot index key

# =============================================================================
# XRANDR ERROR TEXTS / ТЕКСТЫ ОШИБОК XRANDR
# =============================================================================

XRANDR_ERROR_NOT_FOUND = "cannot find output"  # xrandr monitor not found error text
XRANDR_ERROR_NO_SUCH_OUTPUT = "no such output"  # xrandr no such output error text
XRANDR_ERROR_NO_GAMMA = "gamma size is 0"  # xrandr no gamma support error text
XRANDR_ERROR_BAD_VALUE = "badvalue"  # xrandr bad value error text
XRANDR_ERROR_BAD_MATCH = "bad match"  # xrandr bad match error text
XRANDR_ERROR_SERVER = "server"  # xrandr server error text
XRANDR_ERROR_GRAB = "grab"  # xrandr grab error text

# =============================================================================
# TREEVIEW PARAMS / ПАРАМЕТРЫ TREEVIEW
# =============================================================================

TREEVIEW_COLUMN_VALUES = "values"  # Treeview values column name

# =============================================================================
# SCALE PARAMS / ПАРАМЕТРЫ СЛАЙДЕРА
# =============================================================================

SCALE_ORIENT = tk.HORIZONTAL  # Scale orientation
SCALE_SHOWVALUE = False  # Show scale value flag

# =============================================================================
# TEXT WIDGET PARAMS / ПАРАМЕТРЫ ТЕКСТОВОГО ВИДЖЕТА
# =============================================================================

TEXT_START_INDEX = "1.0"  # Text widget start index
TEXT_END_INDEX = tk.END  # Text widget end index

# =============================================================================
# REGEX PATTERNS / РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ
# =============================================================================

XRANDR_MODE_PATTERN = r"\b\d+x\d+\+\d+\+\d+\b"  # xrandr mode regex pattern
XRANDR_GEOMETRY_PATTERN = r"(\d+)x(\d+)\+(\d+)\+(\d+)"  # xrandr geometry regex pattern

# =============================================================================
# DIALOG BINDINGS / ПРИВЯЗКИ ДИАЛОГОВ
# =============================================================================

MESSAGE_RETURN_BIND = "<Return>"  # Message dialog Return key binding
MESSAGE_ESCAPE_BIND = "<Escape>"  # Message dialog Escape key binding
DIALOG_RETURN_BIND = "<Return>"  # Dialog Return key binding
DIALOG_KEYRELEASE_BIND = "<KeyRelease>"  # Dialog KeyRelease key binding
DIALOG_LEFT_CLICK_BIND = "<Button-1>"  # Dialog left mouse button binding
DIALOG_RIGHT_CLICK_BIND = "<Button-3>"  # Dialog right mouse button binding
DIALOG_MOTION_BIND = "<Motion>"  # Dialog mouse motion binding
DIALOG_LEAVE_BIND = "<Leave>"  # Dialog mouse leave binding
DIALOG_DOUBLE_CLICK_BIND = "<Double-Button-1>"  # Dialog double click binding
DIALOG_FOCUS_IN_BIND = "<FocusIn>"  # Dialog focus in binding
DIALOG_FOCUS_OUT_BIND = "<FocusOut>"  # Dialog focus out binding
DIALOG_CONFIGURE_BIND = "<Configure>"  # Dialog configure event binding

# =============================================================================
# CLI PREFIXES / ПРЕФИКСЫ CLI
# =============================================================================

CLI_SUCCESS_PREFIX = "✅ "  # CLI success message prefix
CLI_ERROR_PREFIX = "❌ "  # CLI error message prefix
CLI_WARNING_PREFIX = "⚠️ "  # CLI warning message prefix
CLI_INFO_PREFIX = "📺 "  # CLI info message prefix
CLI_SAVE_PREFIX = "💾 "  # CLI save message prefix
CLI_TARGET_PREFIX = "🎯 "  # CLI target message prefix
CLI_WAIT_PREFIX = "⏳ "  # CLI wait message prefix
CLI_BULLET = "  • "  # CLI list bullet point
CLI_CHECK = "✓"  # CLI check mark symbol
CLI_CROSS = "✗"  # CLI cross mark symbol

# =============================================================================
# LOGGING / ЛОГИРОВАНИЕ
# =============================================================================

LOG_LEVEL_DEBUG = logging.DEBUG  # Debug logging level
LOG_ENCODING = "utf-8"  # Log file encoding
FILE_MODE_READ = "r"  # File read mode
FILE_MODE_WRITE = "w"  # File write mode
FILE_ENCODING = "utf-8"  # General file encoding

# =============================================================================
# DEFAULT PRESETS / ПРЕСЕТЫ ПО УМОЛЧАНИЮ
# =============================================================================

DEFAULT_PRESETS = [
    {
        "id": 1,
        "name": "3500K (Warm Light)",
        "rgb": [1.00, 0.83, 0.61],
        "comment": "Warm white light. Perfect for coding and office work under low ambient lighting.",
    },
    {
        "id": 2,
        "name": "4000K (Neutral)",
        "rgb": [1.00, 0.88, 0.69],
        "comment": "Neutral white with no yellow tint. Reduces eye strain during the daytime.",
    },
    {
        "id": 3,
        "name": "5000K (E-Ink / Paper)",
        "rgb": [1.00, 0.94, 0.77],
        "comment": "Electronic paper effect. Comfortable for long reading sessions and text processing.",
    },
    {
        "id": 4,
        "name": "6500K (Daylight)",
        "rgb": [1.00, 1.00, 1.00],
        "comment": "Standard monitor color profile (sRGB D65). Native colors with no filtering applied.",
    },
    {
        "id": 5,
        "name": "7500K (Cool)",
        "rgb": [0.87, 0.91, 1.00],
        "comment": "Cool dynamic light. Increases contrast and alertness in bright environments.",
    },
    {
        "id": 6,
        "name": "1900K (Candlelight)",
        "rgb": [1.00, 0.62, 0.28],
        "comment": "Ultra-warm orange tint. Maximum blue light suppression for late-night use in complete darkness.",
    },
    {
        "id": 7,
        "name": "2300K (Dim Sunset)",
        "rgb": [1.00, 0.68, 0.36],
        "comment": "Soft amber glow. Excellent for relaxing or watching movies before sleep.",
    },
    {
        "id": 8,
        "name": "2700K (Incandescent)",
        "rgb": [1.00, 0.71, 0.43],
        "comment": "Classic cozy home lighting spectrum. Simulates a traditional incandescent bulb.",
    },
    {
        "id": 9,
        "name": "Dimmer (Low Light)",
        "rgb": [0.50, 0.50, 0.50],
        "comment": "Reduces display matrix brightness by 50% without altering the color temperature balance.",
    },
    {
        "id": 10,
        "name": "Amber (High Contrast)",
        "rgb": [1.00, 0.60, 0.01],
        "comment": "High contrast terminal mode. Completely cuts blue spectrum, making white text amber.",
    },
    {
        "id": 11,
        "name": "Darkroom (Red Mono)",
        "rgb": [1.00, 0.01, 0.01],
        "comment": "Monochrome red mode. Preserves night vision and protects melatonin production entirely.",
    },
    {
        "id": 12,
        "name": "Eco (Green Tint)",
        "rgb": [0.30, 1.00, 0.30],
        "comment": "Green phosphor filter. Maximizes UI legibility at extremely low hardware brightness levels.",
    },
]  # Default color temperature presets / Пресеты цветовой температуры по умолчанию

# =============================================================================
# MONITOR COLOR GENERATION / ГЕНЕРАЦИЯ ЦВЕТОВ МОНИТОРОВ
# =============================================================================

MONITOR_COLOR_SATURATION = 0.75  # Saturation for monitor colors in light theme
MONITOR_COLOR_VALUE = 0.45  # Value (brightness) for monitor colors in light theme
MONITOR_COLOR_SATURATION_DARK = 0.6  # Saturation for monitor colors in dark theme
MONITOR_COLOR_VALUE_DARK = 0.85  # Value (brightness) for monitor colors in dark theme

# =============================================================================
# RESIZE DEBOUNCE / ЗАДЕРЖКА ИЗМЕНЕНИЯ РАЗМЕРА
# =============================================================================

RESIZE_DEBOUNCE_MS = 200  # Debounce delay for resize events (ms)

# =============================================================================
# RESTORE RETRY SETTINGS / НАСТРОЙКИ ПОВТОРНЫХ ПОПЫТОК ВОССТАНОВЛЕНИЯ
# =============================================================================

RESTORE_MAX_ATTEMPTS = 3  # Maximum retry attempts for restore
RESTORE_RETRY_DELAY = 2  # Delay between restore retries (seconds)

# =============================================================================
# ICON SETTINGS / НАСТРОЙКИ ИКОНКИ
# =============================================================================

ICON_SIZE = 256  # Icon size in pixels
ICON_CORNER_RADIUS = 18  # Corner radius for icon elements

# =============================================================================
# TOGGLE ARROW SETTINGS / НАСТРОЙКИ СТРЕЛКИ ПЕРЕКЛЮЧЕНИЯ
# =============================================================================

TOGGLE_ARROW_MIN_HEIGHT = 20  # Minimum height for arrow drawing
TOGGLE_ARROW_FALLBACK_HEIGHT = 400  # Fallback height if too small

# =============================================================================
# PRESET NAMES / НАЗВАНИЯ ПРЕСЕТОВ
# =============================================================================

PRESET_NAME_CUSTOM = "Custom"  # Name for custom preset

# =============================================================================
# CLI OUTPUT SEPARATOR / РАЗДЕЛИТЕЛЬ ВЫВОДА CLI
# =============================================================================

CLI_SEPARATOR_CHAR = "="  # Character for CLI separator
CLI_SEPARATOR_LENGTH = 50  # Length of CLI separator

# =============================================================================
# LEGACY CONFIG KEYS / УСТАРЕВШИЕ КЛЮЧИ КОНФИГА
# =============================================================================

LEGACY_LEFT_PANEL_KEY = "left_panel_visible"  # Legacy key for left panel visibility

# =============================================================================
# DEFAULT FALLBACK RESOLUTION / РАЗРЕШЕНИЕ ПО УМОЛЧАНИЮ
# =============================================================================

DEFAULT_FALLBACK_RESOLUTION = (
    0,
    0,
    1920,
    1080,
)  # Fallback resolution when monitor geometry cannot be determined

# =============================================================================
# DATA MODELS / МОДЕЛИ ДАННЫХ
# =============================================================================


@dataclass
class RGB:
    """RGB color values / Значения цвета RGB."""

    r: float
    g: float
    b: float

    def to_list(self) -> list[float]:
        """Convert to list / Преобразовать в список."""
        return [self.r, self.g, self.b]

    def to_hex(self) -> str:
        """Convert to HEX color string / Конвертировать в HEX-строку цвета."""
        r = int(max(0, min(1, self.r)) * 255)
        g = int(max(0, min(1, self.g)) * 255)
        b = int(max(0, min(1, self.b)) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def brightness(self) -> float:
        """Calculate brightness / Вычислить яркость."""
        return (self.r + self.g + self.b) / 3

    def is_valid_gamma(self) -> bool:
        """Check if valid gamma values / Проверить валидность значений гаммы."""
        return (
            0.0 <= self.r <= GAMMA_MAX_VALUE
            and 0.0 <= self.g <= GAMMA_MAX_VALUE
            and 0.0 <= self.b <= GAMMA_MAX_VALUE
        )

    @classmethod
    def from_list(cls, rgb_list: list[float]) -> "RGB":
        """Create from list / Создать из списка."""
        return cls(r=rgb_list[0], g=rgb_list[1], b=rgb_list[2])


@dataclass
class Preset:
    """Color temperature preset / Пресет цветовой температуры."""

    id: int
    name: str
    rgb: RGB
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary / Преобразовать в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "rgb": self.rgb.to_list(),
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Preset":
        """Create from dictionary / Создать из словаря."""
        return cls(
            id=data["id"],
            name=data["name"],
            rgb=RGB.from_list(data["rgb"]),
            comment=data.get("comment", ""),
        )


@dataclass
class Monitor:
    """Monitor information / Информация о мониторе."""

    name: str
    mode: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary / Преобразовать в словарь."""
        return {"name": self.name, "mode": self.mode}


@dataclass
class ThemeColors:
    """Theme color palette / Палитра цветов темы."""

    bg: str
    fg: str
    select_bg: str
    select_fg: str
    disabled_fg: str
    trough: str
    border: str
    toggle_strip_bg: str
    toggle_arrow_color: str
    fav_tree_bg: str
    fav_tree_fg: str
    empty_slot_bg: str
    panel_bg: str
    field_bg: str
    field_fg: str
    field_placeholder_fg: str
    field_cursor: str
    is_dark: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary / Преобразовать в словарь."""
        return {
            "bg": self.bg,
            "fg": self.fg,
            "select_bg": self.select_bg,
            "select_fg": self.select_fg,
            "disabled_fg": self.disabled_fg,
            "trough": self.trough,
            "border": self.border,
            "toggle_strip_bg": self.toggle_strip_bg,
            "toggle_arrow_color": self.toggle_arrow_color,
            "fav_tree_bg": self.fav_tree_bg,
            "fav_tree_fg": self.fav_tree_fg,
            "empty_slot_bg": self.empty_slot_bg,
            "panel_bg": self.panel_bg,
            "field_bg": self.field_bg,
            "field_fg": self.field_fg,
            "field_placeholder_fg": self.field_placeholder_fg,
            "field_cursor": self.field_cursor,
            "is_dark": self.is_dark,
        }


@dataclass
class UISettings:
    """UI settings (typed replacement for ui_settings dict) /
    Настройки интерфейса (типизированная замена dict'а ui_settings)."""

    right_panel_visible: bool = True
    window_geometry: str | None = None
    language: str = "en"
    ui_scale: float | None = None  # User-saved UI scale factor (None = auto-DPI)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict / Сериализация в JSON-совместимый dict."""
        return {
            CFG_KEY_RIGHT_PANEL: self.right_panel_visible,
            CFG_KEY_WINDOW_GEOMETRY: self.window_geometry,
            CFG_KEY_LANGUAGE: self.language,
            CFG_KEY_UI_SCALE: self.ui_scale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UISettings":
        """Deserialize from dict, with legacy key migration /
        Десериализация из dict, с миграцией устаревших ключей."""
        # Legacy migration: left_panel_visible -> right_panel_visible
        if LEGACY_LEFT_PANEL_KEY in data and CFG_KEY_RIGHT_PANEL not in data:
            data = {**data, CFG_KEY_RIGHT_PANEL: data[LEGACY_LEFT_PANEL_KEY]}
        raw_scale = data.get(CFG_KEY_UI_SCALE)
        ui_scale: float | None = None
        if raw_scale is not None:
            try:
                f = float(raw_scale)
                if UI_SCALE_MIN <= f <= UI_SCALE_MAX:
                    ui_scale = f
            except (TypeError, ValueError):
                pass
        return cls(
            right_panel_visible=data.get(CFG_KEY_RIGHT_PANEL, True),
            window_geometry=data.get(CFG_KEY_WINDOW_GEOMETRY),
            language=data.get(CFG_KEY_LANGUAGE, "en"),
            ui_scale=ui_scale,
        )


@dataclass
class SystemSettings:
    """System settings (typed replacement for system_settings dict) /
    Системные настройки (типизированная замена dict'а system_settings)."""

    monitor: str = ""
    monitor_gammas: dict[str, list[float]] = field(default_factory=dict)
    last_rgb: list[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    last_cli_slot: int = -1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict / Сериализация в JSON-совместимый dict."""
        return {
            CFG_KEY_MONITOR: self.monitor,
            CFG_KEY_MONITOR_GAMMAS: self.monitor_gammas,
            CFG_KEY_LAST_RGB: self.last_rgb,
            CFG_KEY_LAST_CLI_SLOT: self.last_cli_slot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemSettings":
        """Deserialize from dict / Десериализация из dict."""
        return cls(
            monitor=data.get(CFG_KEY_MONITOR, ""),
            monitor_gammas=data.get(CFG_KEY_MONITOR_GAMMAS, {}),
            last_rgb=data.get(CFG_KEY_LAST_RGB, [1.0, 1.0, 1.0]),
            last_cli_slot=data.get(CFG_KEY_LAST_CLI_SLOT, -1),
        )


@dataclass
class AppConfig:
    """Application configuration / Конфигурация приложения."""

    ui: UISettings = field(default_factory=UISettings)
    system: SystemSettings = field(default_factory=SystemSettings)
    presets: list[dict[str, Any]] = field(default_factory=list)
    favorites: list[int | None] = field(default_factory=lambda: [1, 2, 3, 4, 5])

    def get_presets(self) -> list[Preset]:
        """Get presets as Preset objects / Получить пресеты как объекты Preset."""
        return [Preset.from_dict(p) for p in self.presets]

    def set_presets(self, presets: list[Preset]) -> None:
        """Set presets from Preset objects / Установить пресеты из объектов Preset."""
        self.presets = [p.to_dict() for p in presets]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict (preserves original file format) /
        Сериализация в JSON-совместимый dict (сохраняет исходный формат файла)."""
        return {
            CFG_KEY_UI_SETTINGS: self.ui.to_dict(),
            CFG_KEY_SYSTEM_SETTINGS: self.system.to_dict(),
            CFG_KEY_PRESETS: self.presets,
            CFG_KEY_FAVORITES: self.favorites,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """Deserialize from dict / Десериализация из dict."""
        return cls(
            ui=UISettings.from_dict(data.get(CFG_KEY_UI_SETTINGS, {})),
            system=SystemSettings.from_dict(data.get(CFG_KEY_SYSTEM_SETTINGS, {})),
            presets=data.get(CFG_KEY_PRESETS, []),
            favorites=data.get(CFG_KEY_FAVORITES, []),
        )


# =============================================================================
# LOCALIZATION / ЛОКАЛИЗАЦИЯ
# =============================================================================

TRANSLATIONS = {
    "ru": {
        "window_title": "Gamma — Менеджер цветовой температуры v{}",
        "library": "Пресеты",
        "favorites": "★ Избранное (ПКМ для удаления)",
        "color_adjustment": "Настройка цвета (RGB)",
        "test": "Тест",
        "red_value": "Красный (R): {:.2f}",
        "green_value": "Зеленый (G): {:.2f}",
        "blue_value": "Синий (B): {:.2f}",
        "save_as_new": "💾 Сохранить текущее как новый пресет",
        "reset": "↺ Сброс",
        "import": "Импорт",
        "export": "Экспорт",
        "save": "Сохранить",
        "search_placeholder": "🔍 Поиск...",
        "slot": "Слот {}",
        "apply_to_all_tooltip": "Применить текущие значения ко всем мониторам (Ctrl+Shift+A)",
        "empty_slot": "[ Пусто ]",
        "error_id": "[ Ошибка ID ]",
        "inactive_preset": "[#{0}] {1}",
        "add_to_favorites": "Добавить в избранное",
        "rename": "Переименовать",
        "edit": "Изменить...",
        "edit_title": "Изменение пресета",
        "rgb_label": "Значения RGB:",
        "delete_preset": "Удалить пресет",
        "rename_title": "Переименовать пресет",
        "new_preset_title": "Новый пресет",
        "new_name_label": "Новое название:",
        "new_preset_label": "Название нового пресета:",
        "new_comment_label": "Комментарий (необязательно):",
        "info": "Информация",
        "success": "Успех",
        "error": "Ошибка",
        "import_completed": "Импорт завершен",
        "warning": "Предупреждение",
        "already_in_favorites": "Этот пресет уже есть в избранном.",
        "export_success": "Пресеты успешно экспортированы:\n{}",
        "save_file_error": "Не удалось сохранить файл:\n{}",
        "import_invalid_json": "Файл содержит некорректный JSON.",
        "import_error": "Не удалось импортировать файл:\n{}",
        "import_empty": "Файл не содержит валидных пресетов для добавления.",
        "import_added": "✅ Добавлено новых: {}",
        "import_skipped": "⏭️ Пропущено дубликатов (по RGB): {}",
    },
    "en": {
        "window_title": "Gamma — Color Temperature Manager v{}",
        "library": "Presets",
        "favorites": "★ Favorites (Right-click to remove)",
        "color_adjustment": "Color Adjustment (RGB)",
        "test": "Test",
        "red_value": "Red (R): {:.2f}",
        "green_value": "Green (G): {:.2f}",
        "blue_value": "Blue (B): {:.2f}",
        "save_as_new": "💾 Save current as new preset",
        "reset": "↺ Reset",
        "import": "Import",
        "export": "Export",
        "save": "Save",
        "search_placeholder": "🔍 Search...",
        "slot": "Slot {}",
        "apply_to_all_tooltip": "Apply current values to all monitors (Ctrl+Shift+A)",
        "empty_slot": "[ Empty ]",
        "error_id": "[ ID Error ]",
        "inactive_preset": "[#{0}] {1}",
        "add_to_favorites": "Add to favorites",
        "rename": "Rename",
        "edit": "Edit...",
        "edit_title": "Edit preset",
        "rgb_label": "RGB values:",
        "delete_preset": "Delete preset",
        "rename_title": "Rename preset",
        "new_preset_title": "New preset",
        "new_name_label": "New name:",
        "new_preset_label": "New preset name:",
        "new_comment_label": "Comment (optional):",
        "info": "Information",
        "success": "Success",
        "error": "Error",
        "import_completed": "Import completed",
        "warning": "Warning",
        "already_in_favorites": "This preset is already in favorites.",
        "export_success": "Presets successfully exported to:\n{}",
        "save_file_error": "Failed to save file:\n{}",
        "import_invalid_json": "File contains invalid JSON.",
        "import_error": "Failed to import file:\n{}",
        "import_empty": "File contains no valid presets to add.",
        "import_added": "✅ Added new: {}",
        "import_skipped": "⏭️ Skipped duplicates (by RGB): {}",
    },
}  # Translation dictionaries / Словари переводов

# =============================================================================
# LOGGING / ЛОГИРОВАНИЕ
# =============================================================================

logger = logging.getLogger("gamma_picker")  # Global logger instance / Глобальный экземпляр логгера


def setup_logging() -> logging.Logger:
    """
    Setup logging system using RotatingFileHandler.
    Настраивает систему логирования с использованием RotatingFileHandler.

    Returns / Возвращает:
        logging.Logger: Configured logger / Настроенный логгер
    """
    global logger
    logger.setLevel(LOG_LEVEL_DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    try:
        # RotatingFileHandler handles size limits automatically / RotatingFileHandler автоматически ограничивает размер
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_SIZE, backupCount=3, encoding=LOG_ENCODING
        )
        file_handler.setLevel(LOG_LEVEL_DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        logger.addHandler(file_handler)
    except Exception as e:
        fallback_handler = logging.StreamHandler(sys.stderr)
        fallback_handler.setLevel(logging.WARNING)
        fallback_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        logger.addHandler(fallback_handler)
        logger.warning("Failed to create log file %s: %s", LOG_FILE, e)

    return logger


# =============================================================================
# LOCALIZATION FUNCTIONS / ФУНКЦИИ ЛОКАЛИЗАЦИИ
# =============================================================================

# Language cache state: holds last detected language and config file mtime
# Состояние кэша языка: хранит последний определённый язык и mtime файла конфига
_lang_state: dict = {"lang": None, "mtime": None}


def detect_language() -> str:
    """
    Detect system language automatically.
    Автоматически определяет язык системы.

    Returns / Возвращает:
        str: "ru" for Russian, "en" for English / "ru" для русского, "en" для английского
    """
    try:
        lang = locale.getlocale()[0]
        if not lang:
            lang = os.environ.get("LC_ALL") or os.environ.get("LANG") or os.environ.get("LANGUAGE")
        if lang and lang.startswith("ru"):
            return "ru"
        return "en"
    except Exception:
        return "en"


def get_language() -> str:
    """
    Get current language from config or detect automatically.
    Возвращает текущий язык из конфига или определяет автоматически.
    Uses file mtime cache to avoid re-reading config on every call.
    Использует кэш по mtime файла, чтобы не читать конфиг при каждом вызове.

    Returns / Возвращает:
        str: Language code ("ru" or "en") / Код языка ("ru" или "en")
    """
    global _lang_state
    if not os.path.exists(CONFIG_FILE):
        return detect_language()
    try:
        mtime = os.path.getmtime(CONFIG_FILE)
        if _lang_state["lang"] is not None and _lang_state["mtime"] == mtime:
            return _lang_state["lang"]
        with open(CONFIG_FILE, FILE_MODE_READ, encoding=FILE_ENCODING) as f:
            config = json.load(f)
        lang = config.get(CFG_KEY_UI_SETTINGS, {}).get(CFG_KEY_LANGUAGE, detect_language())
        _lang_state["lang"] = lang
        _lang_state["mtime"] = mtime
        return lang
    except Exception:
        return detect_language()


def invalidate_language_cache() -> None:
    """
    Invalidate cached language value.
    Сбрасывает закэшированное значение языка (вызывать после save_config).
    """
    global _lang_state
    _lang_state["lang"] = None
    _lang_state["mtime"] = None


def tr(key: str, *args) -> str:
    """
    Get translated string by key with formatting.
    Получить перевод строки по ключу с форматированием.

    Args:
        key (str): Translation key / Ключ перевода
        *args: Format arguments / Аргументы форматирования

    Returns / Возвращает:
        str: Translated string / Переведённая строка
    """
    lang = get_language()
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = translations.get(key, TRANSLATIONS["en"].get(key, key))
    if args:
        try:
            return text.format(*args)
        except Exception:
            return text
    return text


# =============================================================================
# THEME DETECTION / ОПРЕДЕЛЕНИЕ ТЕМЫ
# =============================================================================


def get_system_colors() -> ThemeColors:
    """
    Detect system theme and return color palette.
    Определяет системную тему и возвращает палитру цветов.

    Returns / Возвращает:
        ThemeColors: Theme color palette / Палитра цветов темы
    """
    is_dark = False

    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            theme = result.stdout.strip().lower().strip("'\"")
            is_dark = "dark" in theme
    except Exception:
        pass

    if not is_dark:
        gtk_theme = os.environ.get("GTK_THEME", "").lower()
        is_dark = "dark" in gtk_theme

    if not is_dark:
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                scheme = result.stdout.strip().lower().strip("'\"")
                is_dark = "dark" in scheme or "prefer-dark" in scheme
        except Exception:
            pass

    if is_dark:
        return ThemeColors(
            bg="#2b2b2b",
            fg="#ffffff",
            select_bg="#3c3f41",
            select_fg="#ffffff",
            disabled_fg="#808080",
            trough="#505050",
            border="#505050",
            toggle_strip_bg="#3c3c3c",
            toggle_arrow_color="#ffffff",
            fav_tree_bg="#1e3a2f",
            fav_tree_fg="#a3d9b1",
            empty_slot_bg="#3c3c3c",
            panel_bg="#353535",
            field_bg="#1e1e1e",
            field_fg="#ffffff",
            field_placeholder_fg="#A0A0A0",
            field_cursor="#ffffff",
            is_dark=True,
        )
    else:
        return ThemeColors(
            bg="#f0f0f0",
            fg="#000000",
            select_bg="#d0d0d0",
            select_fg="#000000",
            disabled_fg="#808080",
            trough="#c0c0c0",
            border="#a0a0a0",
            toggle_strip_bg="#e0e0e0",
            toggle_arrow_color="#555",
            fav_tree_bg="#d1e7dd",
            fav_tree_fg="#0f5132",
            empty_slot_bg="#d0d0d0",
            panel_bg="#e8e8e8",
            field_bg="#ffffff",
            field_fg="#000000",
            field_placeholder_fg="#707070",
            field_cursor="#000000",
            is_dark=False,
        )


# =============================================================================
# DATA MANAGEMENT / УПРАВЛЕНИЕ ДАННЫМИ
# =============================================================================


class ConfigSaveError(Exception):
    """Raised when config cannot be saved / Ошибка сохранения конфига."""


def _rgb_match(a: RGB, b: RGB) -> bool:
    """
    Compare two RGB values with 2-decimal rounding.
    Сравнивает два RGB значения с округлением до 2 знаков.
    """
    return (
        round(a.r, 2) == round(b.r, 2)
        and round(a.g, 2) == round(b.g, 2)
        and round(a.b, 2) == round(b.b, 2)
    )


def _create_default_config() -> AppConfig:
    """Build a fresh default AppConfig instance / Создаёт новый AppConfig со значениями по умолчанию."""
    return AppConfig(
        ui=UISettings(language=detect_language()),
        system=SystemSettings(),
        presets=DEFAULT_PRESETS.copy(),
        favorites=[1, 2, 3, 4, 5],
    )


def _config_from_dict(config_dict: dict[str, Any]) -> AppConfig:
    """Parse a dict loaded from JSON into AppConfig / Разбирает dict из JSON в AppConfig."""
    return AppConfig.from_dict(config_dict)


def save_config(config: AppConfig) -> None:
    """
    Save config atomically using tempfile + os.replace, with backup.
    Атомарно сохраняет конфиг через tempfile + os.replace с резервной копией.

    Args:
        config (AppConfig): Application configuration / Конфигурация приложения

    Raises:
        ConfigSaveError: If write/replace fails / Если запись/замена не удалась
    """
    config_path = Path(CONFIG_FILE)
    backup_path = config_path.with_name(config_path.name + CONFIG_BACKUP_SUFFIX)

    # Create backup only if the main file already exists / Бэкап только если основной файл существует
    if config_path.exists():
        try:
            backup_path.write_bytes(config_path.read_bytes())
        except Exception as e:
            logger.warning("Failed to create backup: %s", e)

    config_dict = config.to_dict()

    tmp_fd = None
    tmp_path: str | None = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(config_path.parent), prefix=".gamma_cfg_", suffix=".tmp"
        )
        with os.fdopen(tmp_fd, FILE_MODE_WRITE, encoding=FILE_ENCODING) as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        tmp_fd = None  # file is now closed / файл закрыт
        os.replace(tmp_path, CONFIG_FILE)
        tmp_path = None
    except Exception as e:
        logger.error("Config save error: %s", e)
        # Cleanup tmp file if still alive / Очистка tmp-файла при ошибке
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except Exception:
                pass
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise ConfigSaveError(str(e)) from e
    finally:
        # Invalidate language cache after each successful save / Сброс кэша языка после сохранения
        invalidate_language_cache()


def load_config() -> AppConfig:
    """
    Load config with backup recovery.
    Загружает конфиг с восстановлением из бэкапа.

    Returns / Возвращает:
        AppConfig: Application configuration / Конфигурация приложения
    """
    if not os.path.exists(CONFIG_FILE):
        config = _create_default_config()
        save_config(config)
        logger.info("Created default config, language: %s", config.ui.language)
        return config

    def try_load_json(file_path: str) -> tuple[dict | None, str | None]:
        """Try to load JSON from file / Попытаться загрузить JSON из файла."""
        try:
            with open(file_path, FILE_MODE_READ, encoding=FILE_ENCODING) as f:
                return json.load(f), None
        except json.JSONDecodeError as e:
            return None, f"JSON error: {e}"
        except Exception as e:
            return None, f"Read error: {e}"

    config_dict, error = try_load_json(CONFIG_FILE)

    if error:
        logger.error("Main config load error: %s", error)
        backup_file = CONFIG_FILE + CONFIG_BACKUP_SUFFIX
        if os.path.exists(backup_file):
            logger.info("Attempting recovery from backup: %s", backup_file)
            config_dict, backup_error = try_load_json(backup_file)
            if config_dict is not None:
                logger.info("[OK] Config restored from backup")
                config = _config_from_dict(config_dict)
                save_config(config)
                return config
            else:
                logger.error("[ERROR] Backup also corrupted: %s", backup_error)
                config_dict = None
        else:
            logger.error("[ERROR] Backup not found")

    if config_dict is None:
        logger.warning("[WARN] Creating new default config")
        config = _create_default_config()
        save_config(config)
        return config

    try:
        config = _config_from_dict(config_dict)

        # Sanitize presets / Очистка пресетов
        if config.presets:
            seen_ids = set()
            max_id = 0
            for p in config.presets:
                if "id" in p:
                    if p["id"] in seen_ids:
                        max_id = max(max_id, max(seen_ids)) if seen_ids else 0
                        max_id += 1
                        p["id"] = max_id
                    else:
                        seen_ids.add(p["id"])
                        max_id = max(max_id, p["id"])
            if len(seen_ids) != len(config.presets):
                logger.info("Duplicate IDs found in config. Auto-fixed")
                save_config(config)

        # Legacy keys migration is now handled inside UISettings.from_dict() /
        # Миграция устаревших ключей теперь выполняется внутри UISettings.from_dict()
        # Defensive language fallback (in case language loaded as empty string) /
        # Защитный fallback по языку (на случай пустой строки)
        if not config.ui.language:
            config.ui.language = detect_language()
            save_config(config)

        return config
    except Exception as e:
        logger.error("Config sanitization error: %s", e)
        backup_file = CONFIG_FILE + CONFIG_BACKUP_SUFFIX
        if os.path.exists(backup_file):
            config_dict, _ = try_load_json(backup_file)
            if config_dict is not None:
                return _config_from_dict(config_dict)
        return _create_default_config()


def get_next_id(presets: list[Preset]) -> int:
    """
    Get next available preset ID.
    Получить следующий доступный ID пресета.

    Args:
        presets (List[Preset]): List of presets / Список пресетов

    Returns / Возвращает:
        int: Next available ID / Следующий доступный ID
    """
    if not presets:
        return 1
    return max(p.id for p in presets) + 1


def get_preset_by_id(presets: list[Preset], pid: int) -> Preset | None:
    """
    Find preset by ID.
    Найти пресет по ID.

    Args:
        presets (List[Preset]): List of presets / Список пресетов
        pid (int): Preset ID / ID пресета

    Returns / Возвращает:
        Optional[Preset]: Preset or None / Пресет или None
    """
    for p in presets:
        if p.id == pid:
            return p
    return None


def generate_monitor_colors(count: int, is_dark: bool = False) -> list[str]:
    """
    Generate N evenly distributed colors for monitor buttons.
    Генерирует N равномерно распределенных цветов для кнопок мониторов.

    Args:
        count (int): Number of colors / Количество цветов
        is_dark (bool): Use dark theme colors / Использовать цвета тёмной темы

    Returns / Возвращает:
        List[str]: List of HEX color strings / Список HEX-строк цветов
    """
    colors = []
    saturation = MONITOR_COLOR_SATURATION_DARK if is_dark else MONITOR_COLOR_SATURATION
    value = MONITOR_COLOR_VALUE_DARK if is_dark else MONITOR_COLOR_VALUE
    for i in range(count):
        hue = i / count if count > 1 else 0.0
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        colors.append(hex_color)
    return colors


def create_default_icon() -> str | None:
    """
    Create simple PNG icon programmatically using Pillow.
    Создать простую PNG иконку программно с помощью Pillow.

    Returns / Возвращает:
        Optional[str]: Path to created icon or None / Путь к созданной иконке или None
    """
    try:
        from PIL import Image, ImageDraw

        size = ICON_SIZE
        # Build gradient as a 1-pixel-wide column then resize — much faster than
        # drawing one rectangle per row / Градиент строится как колонка шириной 1px
        # и затем масштабируется — намного быстрее, чем рисовать прямоугольник на каждую строку
        column = Image.new("RGBA", (1, size), (0, 0, 0, 0))
        for y in range(size):
            progress = y / size
            r = int(ICON_GRADIENT_R_START * (1 - progress) + ICON_GRADIENT_R_END * progress)
            g = int(ICON_GRADIENT_G_START * (1 - progress) + ICON_GRADIENT_G_END * progress)
            b = int(ICON_GRADIENT_B_START * (1 - progress) + ICON_GRADIENT_B_END * progress)
            column.putpixel((0, y), (r, g, b, 255))
        img = column.resize((size, size))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            ICON_RED_RECT, radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_RED, 255)
        )
        draw.rounded_rectangle(
            [140, 52, 224, 88], radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_RED, 100)
        )
        draw.rounded_rectangle(
            ICON_GREEN_RECT, radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_GREEN, 255)
        )
        draw.rounded_rectangle(
            [170, 110, 224, 146], radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_GREEN, 100)
        )
        draw.rounded_rectangle(
            ICON_BLUE_RECT, radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_BLUE, 255)
        )
        draw.rounded_rectangle(
            [110, 168, 224, 204], radius=ICON_CORNER_RADIUS, fill=(*ICON_COLOR_BLUE, 100)
        )
        draw.ellipse(ICON_RED_DOT, fill=(255, 255, 255, 255))
        draw.ellipse(ICON_GREEN_DOT, fill=(255, 255, 255, 255))
        draw.ellipse(ICON_BLUE_DOT, fill=(255, 255, 255, 255))
        icon_path = os.path.join(SCRIPT_DIR, ICON_FILENAME)
        img.save(icon_path, "PNG")
        logger.info("Default icon created: %s", icon_path)
        return icon_path
    except ImportError:
        logger.warning("Pillow not installed, cannot create default icon")
        return None
    except Exception as e:
        logger.error("Failed to create default icon: %s", e)
        return None


# =============================================================================
# SYSTEM FUNCTIONS / СИСТЕМНЫЕ ФУНКЦИИ
# =============================================================================

_monitors_cache: dict[str, Any] = {
    "data": None,
    "timestamp": 0,
}  # Cache for monitor list / Кэш списка мониторов


def _run_xrandr(
    args: list[str], timeout: int = XRANDR_TIMEOUT
) -> tuple[str | None, str | None, int]:
    """
    Centralized xrandr call with retry and timeout.
    Централизованный вызов xrandr с retry и таймаутом.

    Args:
        args (List[str]): Arguments for xrandr / Аргументы для xrandr
        timeout (int): Timeout in seconds / Таймаут в секундах

    Returns / Возвращает:
        Tuple[Optional[str], Optional[str], int]: (stdout, stderr, returncode)
    """
    cmd = ["xrandr"] + args
    for attempt in range(XRANDR_MAX_RETRIES + 1):
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return stdout, stderr, process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                logger.warning(
                    "xrandr timeout (attempt %s/%s)", attempt + 1, XRANDR_MAX_RETRIES + 1
                )
        except FileNotFoundError:
            logger.error("xrandr not found. Install xrandr package")
            return None, None, -1
        except Exception as e:
            logger.warning("xrandr call error (attempt %s): %s", attempt + 1, e)
        if attempt < XRANDR_MAX_RETRIES:
            time.sleep(XRANDR_RETRY_DELAY)
    return None, None, -1


def check_single_instance() -> None:
    """
    Prevent multiple instances using fcntl.flock on a lock file in XDG_RUNTIME_DIR.
    Предотвращает запуск нескольких копий через fcntl.flock на lock-файле в XDG_RUNTIME_DIR.

    Legacy name kept for backward compatibility; delegates to acquire_single_instance_lock.
    Старое имя оставлено для обратной совместимости; делегирует к acquire_single_instance_lock.
    """
    if not acquire_single_instance_lock():
        logger.info("Another instance already running")
        sys.exit(0)


# File descriptor holding the singleton lock (kept open for the lifetime of the process)
# Файловый дескриптор, удерживающий блокировку единственного экземпляра (открыт всё время жизни процесса)
_LOCK_FD: int | None = None


def acquire_single_instance_lock() -> bool:
    """
    Try to acquire an exclusive lock on a per-user lock file.
    Пытается получить эксклюзивную блокировку на per-user lock-файл.

    Uses $XDG_RUNTIME_DIR/gamma-{uid}.lock (fallback to tempfile.gettempdir()).
    Использует $XDG_RUNTIME_DIR/gamma-{uid}.lock (fallback на tempfile.gettempdir()).

    Returns / Возвращает:
        bool: True if lock acquired, False if another instance holds it /
              True если блокировка получена, False если уже занята
    """
    global _LOCK_FD
    if _LOCK_FD is not None:
        return True
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    lock_path = os.path.join(runtime_dir, f"gamma-{os.getuid()}.lock")
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as e:
        logger.warning("Cannot open singleton lock file %s: %s", lock_path, e)
        # Be permissive: allow running without a lock if we cannot create it
        # Будем мягкими: разрешаем запуск без блокировки, если не можем её создать
        return True
    try:
        # LOCK_NB — non-blocking; fail immediately if already locked by another process
        # LOCK_NB — неблокирующий режим; сразу неудача, если уже занято другим процессом
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            os.close(fd)
        except Exception:
            pass
        return False
    _LOCK_FD = fd
    logger.debug("Singleton lock acquired: %s", lock_path)
    return True


def get_monitors() -> list[Monitor]:
    """
    Get connected monitors with caching.
    Получает список подключенных мониторов с кэшированием.

    Returns / Возвращает:
        List[Monitor]: List of monitors / Список мониторов
    """
    now = time.time()
    if (
        _monitors_cache["data"] is not None
        and now - _monitors_cache["timestamp"] < MONITORS_CACHE_TTL
    ):
        return _monitors_cache["data"]

    stdout, stderr, code = _run_xrandr([])
    if code != 0 or stdout is None:
        if stderr:
            logger.warning("xrandr returned error: %s", stderr.strip())
        if _monitors_cache["data"] is not None:
            logger.info("Using cached monitor list")
            return _monitors_cache["data"]
        return []

    monitors = []
    try:
        for line in stdout.splitlines():
            if " connected " in line:
                parts = line.split()
                if parts:
                    name = parts[0]
                    mode_match = re.search(XRANDR_MODE_PATTERN, line)
                    mode = mode_match.group(0) if mode_match else "Active"
                    monitors.append(Monitor(name=name, mode=mode))
    except Exception as e:
        logger.warning("xrandr output parse error: %s", e)
        if _monitors_cache["data"] is not None:
            return _monitors_cache["data"]
        return []

    _monitors_cache["data"] = monitors
    _monitors_cache["timestamp"] = now
    logger.debug("Detected monitors: %s", [m.name for m in monitors])
    return monitors


def apply_gamma(monitor_name: str, rgb: RGB) -> tuple[bool, str]:
    """
    Apply gamma to monitor with retry.
    Применяет гамму к монитору с retry.

    Args:
        monitor_name (str): Monitor name / Имя монитора
        rgb (RGB): RGB values / Значения RGB

    Returns / Возвращает:
        Tuple[bool, str]: (success, message) / (успех, сообщение)
    """
    if not monitor_name or not monitor_name.strip():
        return False, "Monitor name is empty"
    if not rgb.is_valid_gamma():
        return False, f"Invalid RGB values: {rgb.r}, {rgb.g}, {rgb.b}"

    stdout, stderr, code = _run_xrandr(
        ["--output", monitor_name, "--gamma", f"{rgb.r:.2f}:{rgb.g:.2f}:{rgb.b:.2f}"]
    )

    if code == 0:
        logger.info("Gamma applied to %s: R=%.2f G=%.2f B=%.2f", monitor_name, rgb.r, rgb.g, rgb.b)
        return True, f"Gamma applied to {monitor_name}"

    error_msg = stderr.strip() if stderr else "Unknown error"
    return False, _classify_xrandr_error(monitor_name, error_msg)


# Rules table for xrandr error classification / Таблица правил классификации ошибок xrandr
# Each rule: (predicate over lowercased message, message template).
# Predicates preserve the EXACT boolean logic of the original if/elif chain
# (OR for alternatives, AND where the original used AND).
# Каждое правило: (предикат над нижним регистром сообщения, шаблон сообщения).
# Предикаты сохраняют ТОЧНУ логику оригинальной цепочки if/elif
# (OR для альтернатив, AND где в оригинале было AND).
_XRANDR_ERROR_RULES = [
    (
        lambda m: XRANDR_ERROR_NOT_FOUND in m or XRANDR_ERROR_NO_SUCH_OUTPUT in m,
        "Monitor '{mon}' not found. It may be disconnected.",
    ),
    (lambda m: XRANDR_ERROR_NO_GAMMA in m, "Monitor '{mon}' does not support gamma adjustment."),
    (
        lambda m: XRANDR_ERROR_BAD_VALUE in m or XRANDR_ERROR_BAD_MATCH in m,
        "Invalid gamma values for monitor '{mon}'.",
    ),
    (
        lambda m: XRANDR_ERROR_SERVER in m and XRANDR_ERROR_GRAB in m,
        "X server is busy with another application. Try later.",
    ),
]


def _classify_xrandr_error(monitor_name: str, error_msg: str) -> str:
    """
    Classify an xrandr stderr message into a human-readable string using a rule table.
    Классифицирует stderr-сообщение xrandr в человекочитаемую строку через таблицу правил.

    Args:
        monitor_name (str): Monitor name for message formatting / Имя монитора для подстановки
        error_msg (str): Raw stderr from xrandr / Сырой stderr из xrandr

    Returns / Возвращает:
        str: Friendly error message / Дружелюбное сообщение об ошибке
    """
    low = error_msg.lower()
    for predicate, template in _XRANDR_ERROR_RULES:
        if predicate(low):
            return template.format(mon=monitor_name)
    return f"xrandr error: {error_msg}"


# =============================================================================
# GUI APPLICATION / GUI ПРИЛОЖЕНИЕ
# =============================================================================


class GammaApp:
    """
    Main GUI application for Gamma color temperature manager.
    Основное GUI приложение для менеджера цветовой температуры Gamma.
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the application.
        Инициализирует приложение.

        Args:
            root (tk.Tk): Main Tkinter window / Главное окно Tkinter
        """
        self.root = root
        self.colors = get_system_colors()
        self._setup_window()
        self._load_initial_data()
        self._build_interface()
        self._calculate_window_geometry()  # H8: now UI is built, can measure real widgets
        self._show_window()  # H8: deiconify + toggle arrow, after geometry is set
        self._bind_events()

    def _setup_window(self) -> None:
        """Setup main window properties / Настроить свойства главного окна."""
        # Withdraw IMMEDIATELY — before any other operation — to prevent the default
        # 200x200 placeholder window from flashing on screen at startup.
        # / Скрываем окно НЕМЕДЛЕННО — до любых других операций — чтобы дефолтное
        # окно 200x200 не мелькало на экране при старте.
        # Note: tk.Tk() creates the window already visible; without this early withdraw(),
        # any update_idletasks() (e.g. in _setup_dpi_scaling) would render the placeholder.
        # / Примечание: tk.Tk() создаёт уже видимое окно; без раннего withdraw()
        # любой update_idletasks() (напр. в _setup_dpi_scaling) отрисовал бы плейсхолдер.
        self.root.withdraw()

        self._setup_dpi_scaling()
        self.root.option_add("*relief", "flat")
        self.root.option_add("*borderWidth", "0")
        self.root.option_add("*highlightThickness", "0")
        self.root.option_add("*Background", self.colors.bg)
        self.root.option_add("*Foreground", self.colors.fg)
        # Apply a scaled font to all LabelFrame titles ("Избранное", "Настройка цвета",
        # "Тест") — tk.LabelFrame doesn't accept a `font=` parameter directly, so we
        # use the option database which affects all LabelFrame widgets globally.
        # / Применяем масштабируемый шрифт ко всем заголовкам LabelFrame («Избранное»,
        # «Настройка цвета», «Тест») — tk.LabelFrame не принимает `font=` напрямую,
        # поэтому используем БД опций, которая влияет на все LabelFrame глобально.
        self.root.option_add("*Labelframe*font", FONT_LIBRARY_HEADER)
        self.root.option_add("*Labelframe*foreground", self.colors.fg)
        self.root.configure(bg=self.colors.bg)
        self.root.title(tr("window_title", APP_VERSION))

        icon_path = os.path.join(SCRIPT_DIR, ICON_FILENAME)
        if not os.path.exists(icon_path):
            icon_path = create_default_icon()
        if icon_path and os.path.exists(icon_path):
            try:
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
                self.root.icon = icon
            except Exception as e:
                logger.warning("Failed to load icon: %s", e)

        self.root.resizable(False, False)
        min_total_width = CONTENT_FIXED_WIDTH + STRIP_WIDTH + MIN_LIBRARY_WIDTH
        self.root.minsize(min_total_width, 0)

    def _setup_dpi_scaling(self) -> None:
        """
        Detect HiDPI and scale the whole UI accordingly (Approach A — extended).

        Detection strategy (in order of reliability):
        1. Saved `ui_scale` in config — explicit user override via Ctrl++/Ctrl+-.
        2. GAMMA_UI_SCALE env var — explicit user override (e.g. GAMMA_UI_SCALE=1.5).
        3. GDK_SCALE env var — GNOME sets this to 2 on 200% HiDPI.
        4. Xft.dpi X resource — set by some DEs (XFCE, KDE) when user configures scaling.
        5. xrandr physical monitor size (mm) — compute real DPI from pixels and mm.
        6. Fallback: 1.0 (no scaling).

        Once scale_factor is determined:
        - `tk scaling <factor>` is called so fonts (point-based) render at the right size.
        - Fixed pixel-based size constants (CONTENT_FIXED_WIDTH, LIBRARY_WIDTH, etc.)
          are multiplied by factor via _apply_ui_scale(), so the whole layout scales.

        After the auto-detected factor is applied, it is persisted to config
        (`ui_scale`) so subsequent launches skip the detection and use the saved
        value directly. If the user explicitly changes the scale at runtime via
        Ctrl++/Ctrl+-, the new value is saved to `ui_scale` by _rebuild_ui_with_scale.

        / Стратегия детекта (в порядке надёжности):
        1. Сохранённый `ui_scale` в конфиге — явный override через Ctrl++/Ctrl+-.
        2. GAMMA_UI_SCALE — явный override пользователем (напр. 1.5).
        3. GDK_SCALE — GNOME ставит 2 при 200% HiDPI.
        4. Xft.dpi — некоторые DE (XFCE, KDE) устанавливают при настройке scaling.
        5. xrandr — физический размер монитора (мм) → реальный DPI.
        6. Fallback: 1.0.

        После определения scale_factor:
        - `tk scaling <factor>` масштабирует шрифты (point-based).
        - Фиксированные пиксельные размеры (CONTENT_FIXED_WIDTH, LIBRARY_WIDTH и т.д.)
          умножаются на factor через _apply_ui_scale(), масштабируется весь layout.

        После применения авто-детект-фактор сохраняется в конфиг (`ui_scale`),
        чтобы при следующих запусках детектинг пропускался. Если пользователь явно
        меняет масштаб в рантайме через Ctrl++/Ctrl+-, новое значение сохраняется
        в `ui_scale` методом _rebuild_ui_with_scale.
        """
        # 1. Saved ui_scale (highest priority — user explicitly chose a scale).
        # / Сохранённый ui_scale (высший приоритет — пользователь явно выбрал масштаб).
        saved_scale = None
        try:
            saved_scale = load_config().ui.ui_scale
        except Exception as e:
            logger.debug("Could not load saved ui_scale: %s", e)

        if saved_scale is not None:
            factor = saved_scale
            source = "saved"
        else:
            # 2. Env var override (only when no saved scale).
            # / Override через env var (только при отсутствии сохранённого масштаба).
            env_scale = os.environ.get("GAMMA_UI_SCALE")
            if env_scale:
                try:
                    f = float(env_scale)
                    if 0.5 <= f <= 4.0:
                        factor = max(UI_SCALE_MIN, min(UI_SCALE_MAX, round_to_scale_step(f)))
                        source = "env"
                    else:
                        factor = 1.0
                        source = "default"
                except ValueError:
                    factor = 1.0
                    source = "default"
            else:
                # 3-5. Auto-detect via Xft.dpi / GDK_SCALE / xrandr.
                # / Авто-детект через Xft.dpi / GDK_SCALE / xrandr.
                font_scale, layout_scale, det_source = self._detect_ui_scale()
                factor = layout_scale
                source = det_source

        # We scale fonts directly via _scale_font_tuple() (multiplying the point
        # size in each FONT_* tuple). This is more reliable on Linux than
        # `tk scaling`, which is often ignored for named fonts or double-applied
        # when Xft.dpi is set. So we do NOT call `tk scaling` here.
        # / Шрифты масштабируем напрямую через _scale_font_tuple() (умножаем
        # размер в пунктах в каждом кортеже FONT_*). Это надёжнее на Linux, чем
        # `tk scaling`, который часто игнорируется для named fonts или удваивается
        # при установленном Xft.dpi. Поэтому `tk scaling` НЕ вызываем.
        if abs(factor - 1.0) > 0.01:
            self._apply_ui_scale(factor)

        self.ui_scale = factor
        logger.info(
            "UI scaling: factor=%.2f (source=%s)",
            factor,
            source,
        )

        # Persist the auto-detected factor for the next launch (only if the user
        # hasn't already saved one — we don't overwrite a saved value here).
        # / Сохраняем авто-детект-фактор для следующего запуска (только если
        # пользователь ещё не сохранял свой — здесь не перезаписываем).
        if saved_scale is None:
            try:
                cfg = load_config()
                cfg.ui.ui_scale = factor
                save_config(cfg)
            except Exception as e:
                logger.warning("Could not save auto-detected ui_scale: %s", e)

    def _detect_ui_scale(self) -> tuple[float, float, str]:
        """
        Detect the UI scaling factor using multiple strategies.
        Детектирует factor масштабирования UI несколькими стратегиями.
        """
        # 1. Explicit user override via env var (highest priority).
        env = os.environ.get("GAMMA_UI_SCALE")
        if env:
            try:
                f = float(env)
                if 0.5 <= f <= 4.0:
                    f_clamped = max(UI_SCALE_MIN, min(UI_SCALE_MAX, round_to_scale_step(f)))
                    logger.info("UI scale source: env (GAMMA_UI_SCALE=%s) -> %.2f", env, f_clamped)
                    return f_clamped, f_clamped, "env"
            except ValueError:
                logger.warning("GAMMA_UI_SCALE='%s' is not a number, ignoring", env)

        # 2. Xft.dpi X resource — if set AND > 96, fonts are already scaled by Xft.dpi.
        # If Xft.dpi == 96 (the default), it tells us nothing about the real DPI —
        # we must continue to the xrandr strategy to detect HiDPI.
        # / Xft.dpi — если установлен И > 96, шрифты уже отмасштабированы.
        # Если Xft.dpi == 96 (по умолчанию), это ничего не говорит о реальном DPI —
        # нужно продолжить к стратегии xrandr для детекта HiDPI.
        try:
            result = subprocess.run(
                ["xrdb", "-query"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Xft.dpi" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            try:
                                dpi = float(parts[1].strip())
                            except ValueError:
                                continue
                            if dpi > 96:
                                layout = max(UI_SCALE_MIN, min(UI_SCALE_MAX, round_to_scale_step(dpi / 96.0)))
                                logger.info(
                                    "UI scale source: xft_dpi (Xft.dpi=%.1f) -> layout=%.2f",
                                    dpi,
                                    layout,
                                )
                                return 1.0, layout, "xft_dpi"
                            # Xft.dpi == 96 (or lower) — default, fall through to xrandr.
                            # / Xft.dpi == 96 (или меньше) — по умолчанию, идём к xrandr.
                            logger.info(
                                "Xft.dpi=%.1f (default, not HiDPI) — continuing to xrandr",
                                dpi,
                            )
                            break  # break out of the for loop, continue to xrandr
            else:
                logger.debug("xrdb -query failed (returncode=%d)", result.returncode)
        except FileNotFoundError:
            logger.debug("xrdb binary not found")
        except Exception as e:
            logger.debug("xrdb query error: %s", e)

        # 3. GDK_SCALE (GNOME).
        gdk = os.environ.get("GDK_SCALE")
        if gdk:
            try:
                f = float(gdk)
                if f > 1.0:
                    f_clamped = max(UI_SCALE_MIN, min(UI_SCALE_MAX, round_to_scale_step(f)))
                    logger.info("UI scale source: gdk (GDK_SCALE=%s) -> %.2f", gdk, f_clamped)
                    return f_clamped, f_clamped, "gdk"
            except ValueError:
                logger.warning("GDK_SCALE='%s' is not a number, ignoring", gdk)

        # 4. xrandr physical monitor size — compute real DPI.
        # Determine WHICH monitor to measure: the one where the window was last
        # closed (saved geometry's X coordinate), falling back to primary.
        # / xrandr — физический размер монитора, вычисляем реальный DPI.
        # Определяем КАКОЙ монитор мерить: тот, где окно было закрыто в прошлый раз
        # (X-координата из сохранённой геометрии), иначе primary.
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=3
            )
            if result.returncode != 0:
                logger.warning("xrandr --query failed (returncode=%d)", result.returncode)
            else:
                connected_lines = [
                    line for line in result.stdout.splitlines() if " connected " in line
                ]
                for line in connected_lines:
                    logger.debug("xrandr monitor: %s", line)
                # Determine target monitor: where the window was last closed.
                # / Определяем целевой монитор: где окно было последний раз закрыто.
                target_monitor = self._detect_monitor_from_saved_geometry(result.stdout)
                if target_monitor:
                    logger.info(
                        "DPI detection: window was last on monitor '%s'", target_monitor
                    )
                else:
                    logger.info(
                        "DPI detection: no saved geometry match — using primary"
                    )
                dpi = self._extract_dpi_from_xrandr(result.stdout, target_monitor)
                if dpi is None:
                    logger.info(
                        "xrandr: could not extract DPI (no mm info or parse failed) — "
                        "connected monitors: %s",
                        [l.split()[0] for l in connected_lines],
                    )
                else:
                    logger.info(
                        "xrandr: detected DPI=%.1f (monitor=%s)",
                        dpi,
                        target_monitor or "primary",
                    )
                    if dpi > 110:
                        scale = max(UI_SCALE_MIN, min(UI_SCALE_MAX, round_to_scale_step(dpi / 96.0)))
                        logger.info(
                            "UI scale source: xrandr (DPI=%.1f, monitor=%s) -> %.2f",
                            dpi,
                            target_monitor or "primary",
                            scale,
                        )
                        return scale, scale, "xrandr"
                    logger.info(
                        "xrandr DPI=%.1f (<=110, no scaling — not HiDPI threshold)", dpi
                    )
        except FileNotFoundError:
            logger.warning("xrandr binary not found")
        except Exception as e:
            logger.warning("xrandr query error: %s", e)

        logger.info("UI scale: no scaling (factor=1.0, source=none)")
        return 1.0, 1.0, "none"

    def _detect_monitor_from_saved_geometry(self, xrandr_output: str) -> str | None:
        """
        Determine which monitor the window was last closed on, by name.
        Определяет, на каком мониторе окно было закрыто в прошлый раз (по имени).

        Reads the saved `window_geometry` from config (format "WxH+X+Y"), takes the
        X coordinate, and finds which monitor's bounding box contains it. Returns
        the monitor name (e.g. "eDP") or None if no match / no saved geometry.
        / Читает сохранённую `window_geometry` из конфига (формат "WxH+X+Y"),
        берёт X-координату и находит, в bounding box какого монитора она попадает.
        Возвращает имя монитора (напр. "eDP") или None если нет совпадения.
        """
        try:
            saved_geom = load_config().ui.window_geometry
        except Exception:
            saved_geom = None
        if not saved_geom:
            logger.debug("no saved window_geometry — using primary for DPI")
            return None
        # Parse "WxH+X+Y" → we need the window WIDTH (for center calculation) and X.
        # / Парсим "WxH+X+Y" — нужны ШИРИНА окна (для центра) и X-координата.
        try:
            parts = saved_geom.split("x")
            saved_w = int(parts[0])
            rest = parts[1].split("+")
            saved_x = int(rest[1]) if len(rest) > 1 else 0
        except (IndexError, ValueError):
            logger.debug("could not parse saved geometry: %s", saved_geom)
            return None
        # Compute the window's horizontal CENTER (saved_x + width/2).
        # / Вычисляем горизонтальный ЦЕНТР окна (saved_x + ширина/2).
        window_center_x = saved_x + saved_w // 2
        logger.debug(
            "saved window geometry: %s — X=%d width=%d center_x=%d",
            saved_geom,
            saved_x,
            saved_w,
            window_center_x,
        )
        # Find which monitor's bounding box contains the window's center X.
        # / Находим, в bounding box какого монитора попадает центр окна по X.
        for line in xrandr_output.splitlines():
            if " connected " not in line:
                continue
            name = line.split()[0]
            match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
            if not match:
                continue
            mon_w = int(match.group(1))
            mon_x = int(match.group(3))
            if mon_x <= window_center_x < mon_x + mon_w:
                logger.debug(
                    "window center X=%d is on monitor '%s' (x=%d..%d)",
                    window_center_x,
                    name,
                    mon_x,
                    mon_x + mon_w,
                )
                return name
        logger.debug(
            "window center X=%d not inside any detected monitor — using primary",
            window_center_x,
        )
        return None

    def _extract_dpi_from_xrandr(
        self, xrandr_output: str, target_monitor: str | None = None
    ) -> float | None:
        """
        Parse `xrandr --query` output to find a monitor's physical DPI.
        Разбирает вывод `xrandr --query` для нахождения DPI монитора.

        Args:
            xrandr_output: Raw stdout of `xrandr --query` / Вывод `xrandr --query`
            target_monitor: If given, parse THIS monitor's DPI (e.g. "eDP").
                            If None, fall back to primary, then first connected.
                            / Если задан, парсим DPI ЭТОГО монитора.
                            Если None — primary, затем первый подключенный.

        Returns DPI computed from pixels / mm, or None if parsing fails.
        / Возвращает DPI из pixels / mm, или None если не удалось.
        """
        primary_line = None
        first_connected = None
        target_line = None
        for line in xrandr_output.splitlines():
            if " connected " in line:
                name = line.split()[0]
                if target_monitor and name == target_monitor:
                    target_line = line
                    break
                if " primary" in line and primary_line is None:
                    primary_line = line
                if first_connected is None:
                    first_connected = line
        chosen = target_line or primary_line or first_connected
        if not chosen:
            logger.debug("xrandr DPI parse: no 'connected' line found")
            return None
        logger.debug(
            "xrandr DPI parse: target=%s chosen line = %s",
            target_monitor or "(auto)",
            chosen,
        )
        # Find the "WxH+X+Y" geometry token.
        geom_match = re.search(r"(\d+)x(\d+)\+\d+\+\d+", chosen)
        if not geom_match:
            logger.debug("xrandr DPI parse: no geometry (WxH+X+Y) token found")
            return None
        px_w = int(geom_match.group(1))
        px_h = int(geom_match.group(2))
        logger.debug("xrandr DPI parse: geometry = %dx%d", px_w, px_h)
        # Find the "Wmm x Hmm" physical size token.
        mm_match = re.search(r"(\d+)mm\s*x\s*(\d+)mm", chosen)
        if not mm_match:
            logger.info(
                "xrandr DPI parse: no mm size token found in line: %s", chosen
            )
            return None
        mm_w = int(mm_match.group(1))
        mm_h = int(mm_match.group(2))
        logger.debug("xrandr DPI parse: physical size = %dmm x %dmm", mm_w, mm_h)
        if mm_w <= 0 or mm_h <= 0:
            logger.info("xrandr DPI parse: physical size is zero or negative")
            return None
        dpi_x = px_w / (mm_w / 25.4)
        dpi_y = px_h / (mm_h / 25.4)
        dpi = (dpi_x + dpi_y) / 2.0
        logger.debug(
            "xrandr DPI parse: dpi_x=%.1f dpi_y=%.1f avg=%.1f", dpi_x, dpi_y, dpi
        )
        return dpi

    def _apply_ui_scale(self, factor: float) -> None:
        """
        Multiply fixed pixel-based UI size constants by `factor`.
        Умножает фиксированные пиксельные размеры UI на `factor`.

        Idempotent: on the FIRST call it snapshots the current (baseline) values of
        every scaled constant into `self._BASE_SCALE_CONSTANTS`. On EVERY call
        (including the first) it re-derives the scaled values from that baseline,
        so it is safe to call repeatedly with different factors (e.g. when the user
        changes the UI scale via Ctrl++ / Ctrl+- at runtime). The baseline is the
        set of values defined at the top of the file (factor=1.0).
        / Идемпотентно: при ПЕРВОМ вызове снимает слепок текущих (базовых) значений
        всех масштабируемых констант в `self._BASE_SCALE_CONSTANTS`. При КАЖДОМ вызове
        (включая первый) заново выводит масштабированные значения из этого базового
        слепка, поэтому метод безопасно вызывать повторно с разными factor (напр.
        при смене масштаба через Ctrl++ / Ctrl+- в рантайме). Базовые значения —
        те, что определены в начале файла (factor=1.0).
        """
        global CONTENT_FIXED_WIDTH, STRIP_WIDTH, LIBRARY_WIDTH, MIN_LIBRARY_WIDTH
        global MIN_WINDOW_HEIGHT, HEIGHT_RESERVE
        global TREEVIEW_ROWHEIGHT, TREEVIEW_HEIGHT
        global CANVAS_HEIGHT, CANVAS_MIN_WIDTH, CANVAS_WIDTH_MARGIN
        global DIALOG_WIDTH, DIALOG_HEIGHT, DIALOG_COMMENT_HEIGHT, DIALOG_ENTRY_WIDTH
        global DIALOG_OFFSET_X, DIALOG_OFFSET_Y
        global MESSAGE_DIALOG_WIDTH, MESSAGE_DIALOG_HEIGHT, MESSAGE_TEXT_WRAPLENGTH
        global MESSAGE_FRAME_PADX, MESSAGE_FRAME_PADY, MESSAGE_BUTTON_PADX
        global SLIDER_TROUGH_HEIGHT, SLIDER_LENGTH, SLIDER_INDICATOR_SIZE
        global SPINBOX_ARROWSIZE
        global ICON_SIZE, ICON_CORNER_RADIUS
        global TOOLTIP_MAX_WIDTH, TOOLTIP_PADDING
        global FONT_MONITOR, FONT_FAVORITE, FONT_LIBRARY_HEADER, FONT_SEARCH
        global FONT_TREEVIEW, FONT_SLIDER_LABEL, FONT_DIALOG, FONT_TOOLTIP
        global FONT_MESSAGE_ICON, SLIDER_BUTTON_FONT

        # Snapshot baseline values on the first call only.
        # / Снимаем базовые значения только при первом вызове.
        if not hasattr(self, "_BASE_SCALE_CONSTANTS"):
            self._BASE_SCALE_CONSTANTS = {
                "CONTENT_FIXED_WIDTH": CONTENT_FIXED_WIDTH,
                "STRIP_WIDTH": STRIP_WIDTH,
                "LIBRARY_WIDTH": LIBRARY_WIDTH,
                "MIN_LIBRARY_WIDTH": MIN_LIBRARY_WIDTH,
                "MIN_WINDOW_HEIGHT": MIN_WINDOW_HEIGHT,
                "HEIGHT_RESERVE": HEIGHT_RESERVE,
                "TREEVIEW_ROWHEIGHT": TREEVIEW_ROWHEIGHT,
                "CANVAS_HEIGHT": CANVAS_HEIGHT,
                "CANVAS_MIN_WIDTH": CANVAS_MIN_WIDTH,
                "CANVAS_WIDTH_MARGIN": CANVAS_WIDTH_MARGIN,
                "DIALOG_WIDTH": DIALOG_WIDTH,
                "DIALOG_HEIGHT": DIALOG_HEIGHT,
                "DIALOG_COMMENT_HEIGHT": DIALOG_COMMENT_HEIGHT,
                "DIALOG_ENTRY_WIDTH": DIALOG_ENTRY_WIDTH,
                "DIALOG_OFFSET_X": DIALOG_OFFSET_X,
                "DIALOG_OFFSET_Y": DIALOG_OFFSET_Y,
                "MESSAGE_DIALOG_WIDTH": MESSAGE_DIALOG_WIDTH,
                "MESSAGE_DIALOG_HEIGHT": MESSAGE_DIALOG_HEIGHT,
                "MESSAGE_TEXT_WRAPLENGTH": MESSAGE_TEXT_WRAPLENGTH,
                "MESSAGE_FRAME_PADX": MESSAGE_FRAME_PADX,
                "MESSAGE_FRAME_PADY": MESSAGE_FRAME_PADY,
                "MESSAGE_BUTTON_PADX": MESSAGE_BUTTON_PADX,
                "SLIDER_TROUGH_HEIGHT": SLIDER_TROUGH_HEIGHT,
                "SPINBOX_ARROWSIZE": SPINBOX_ARROWSIZE,
                "SLIDER_LENGTH": SLIDER_LENGTH,
                "SLIDER_INDICATOR_SIZE": SLIDER_INDICATOR_SIZE,
                "ICON_SIZE": ICON_SIZE,
                "ICON_CORNER_RADIUS": ICON_CORNER_RADIUS,
                "TOOLTIP_MAX_WIDTH": TOOLTIP_MAX_WIDTH,
                "TOOLTIP_PADDING": TOOLTIP_PADDING,
                "FONT_MONITOR": FONT_MONITOR,
                "FONT_FAVORITE": FONT_FAVORITE,
                "FONT_LIBRARY_HEADER": FONT_LIBRARY_HEADER,
                "FONT_SEARCH": FONT_SEARCH,
                "FONT_TREEVIEW": FONT_TREEVIEW,
                "FONT_SLIDER_LABEL": FONT_SLIDER_LABEL,
                "FONT_DIALOG": FONT_DIALOG,
                "FONT_TOOLTIP": FONT_TOOLTIP,
                "FONT_MESSAGE_ICON": FONT_MESSAGE_ICON,
                "SLIDER_BUTTON_FONT": SLIDER_BUTTON_FONT,
            }
        base = self._BASE_SCALE_CONSTANTS

        def s(v: int) -> int:
            return int(round(v * factor))

        # Window / panel sizes
        CONTENT_FIXED_WIDTH = s(base["CONTENT_FIXED_WIDTH"])
        STRIP_WIDTH = s(base["STRIP_WIDTH"])
        LIBRARY_WIDTH = s(base["LIBRARY_WIDTH"])
        MIN_LIBRARY_WIDTH = s(base["MIN_LIBRARY_WIDTH"])
        MIN_WINDOW_HEIGHT = s(base["MIN_WINDOW_HEIGHT"])
        HEIGHT_RESERVE = s(base["HEIGHT_RESERVE"])

        # Treeview
        TREEVIEW_ROWHEIGHT = s(base["TREEVIEW_ROWHEIGHT"])
        # TREEVIEW_HEIGHT is a row count — leave as is (not in base dict).

        # Test strip canvas
        CANVAS_HEIGHT = s(base["CANVAS_HEIGHT"])
        CANVAS_MIN_WIDTH = s(base["CANVAS_MIN_WIDTH"])
        CANVAS_WIDTH_MARGIN = s(base["CANVAS_WIDTH_MARGIN"])

        # Dialog sizes
        DIALOG_WIDTH = s(base["DIALOG_WIDTH"])
        DIALOG_HEIGHT = s(base["DIALOG_HEIGHT"])
        DIALOG_COMMENT_HEIGHT = s(base["DIALOG_COMMENT_HEIGHT"])
        DIALOG_ENTRY_WIDTH = s(base["DIALOG_ENTRY_WIDTH"])
        DIALOG_OFFSET_X = s(base["DIALOG_OFFSET_X"])
        DIALOG_OFFSET_Y = s(base["DIALOG_OFFSET_Y"])

        # Message dialog
        MESSAGE_DIALOG_WIDTH = s(base["MESSAGE_DIALOG_WIDTH"])
        MESSAGE_DIALOG_HEIGHT = s(base["MESSAGE_DIALOG_HEIGHT"])
        MESSAGE_TEXT_WRAPLENGTH = s(base["MESSAGE_TEXT_WRAPLENGTH"])
        MESSAGE_FRAME_PADX = s(base["MESSAGE_FRAME_PADX"])
        MESSAGE_FRAME_PADY = s(base["MESSAGE_FRAME_PADY"])
        MESSAGE_BUTTON_PADX = s(base["MESSAGE_BUTTON_PADX"])

        # Slider physical sizes
        SLIDER_TROUGH_HEIGHT = s(base["SLIDER_TROUGH_HEIGHT"])
        SPINBOX_ARROWSIZE = s(base["SPINBOX_ARROWSIZE"])
        SLIDER_LENGTH = s(base["SLIDER_LENGTH"])
        SLIDER_INDICATOR_SIZE = s(base["SLIDER_INDICATOR_SIZE"])

        # Icon
        ICON_SIZE = s(base["ICON_SIZE"])
        ICON_CORNER_RADIUS = s(base["ICON_CORNER_RADIUS"])

        # Tooltip
        TOOLTIP_MAX_WIDTH = s(base["TOOLTIP_MAX_WIDTH"])
        TOOLTIP_PADDING = s(base["TOOLTIP_PADDING"])

        # Fonts — scale the point size of each FONT_* tuple.
        # `tk scaling` alone is unreliable on Linux for named fonts, so we directly
        # multiply the point size in the FONT_* tuples (the 2nd element).
        # / Шрифты — масштабируем размер в пунктах каждого FONT_* кортежа.
        # `tk scaling` ненадёжен на Linux для named fonts, поэтому напрямую
        # умножаем размер (2-й элемент кортежа FONT_*).
        FONT_MONITOR = self._scale_font_tuple(base["FONT_MONITOR"], factor)
        FONT_FAVORITE = self._scale_font_tuple(base["FONT_FAVORITE"], factor)
        FONT_LIBRARY_HEADER = self._scale_font_tuple(base["FONT_LIBRARY_HEADER"], factor)
        FONT_SEARCH = self._scale_font_tuple(base["FONT_SEARCH"], factor)
        FONT_TREEVIEW = self._scale_font_tuple(base["FONT_TREEVIEW"], factor)
        FONT_SLIDER_LABEL = self._scale_font_tuple(base["FONT_SLIDER_LABEL"], factor)
        FONT_DIALOG = self._scale_font_tuple(base["FONT_DIALOG"], factor)
        FONT_TOOLTIP = self._scale_font_tuple(base["FONT_TOOLTIP"], factor)
        FONT_MESSAGE_ICON = self._scale_font_tuple(base["FONT_MESSAGE_ICON"], factor)
        SLIDER_BUTTON_FONT = self._scale_font_tuple(base["SLIDER_BUTTON_FONT"], factor)

    @staticmethod
    def _scale_font_tuple(font: tuple, factor: float) -> tuple:
        """
        Scale a tkinter font tuple's point size by `factor`.
        Масштабирует размер шрифта в кортеже tkinter на `factor`.

        A font tuple looks like ("Arial", 10) or ("Arial", 10, "bold").
        The 2nd element (index 1) is the point size — we multiply it by factor
        and round to the nearest integer. Other elements (family, style) are
        preserved unchanged. / Кортеж шрифта выглядит как ("Arial", 10) или
        ("Arial", 10, "bold"). 2-й элемент (индекс 1) — размер в пунктах,
        мы умножаем его на factor и округляем. Остальные элементы сохраняем.
        """
        if not isinstance(font, tuple) or len(font) < 2:
            return font
        family = font[0]
        size = font[1]
        if not isinstance(size, (int, float)):
            return font
        new_size = max(6, int(round(size * factor)))  # min 6pt for readability
        # / мин 6pt для читаемости
        return (family, new_size) + tuple(font[2:])

    def _load_initial_data(self) -> None:
        """Load initial data / Загрузить начальные данные."""
        self.config = load_config()
        self.monitors = get_monitors()
        # M3: do not persist available_monitors to config (kept only at runtime)
        # M3: не сохраняем available_monitors в конфиг (только в рантайме)
        try:
            save_config(self.config)
        except ConfigSaveError as e:
            logger.error("Failed to save initial config: %s", e)
            self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)

        saved_monitor = self.config.system.monitor
        monitor_names = [m.name for m in self.monitors]
        if saved_monitor in monitor_names:
            self.current_monitor = saved_monitor
        elif monitor_names:
            self.current_monitor = monitor_names[0]
            self.config.system.monitor = self.current_monitor
            try:
                save_config(self.config)
            except ConfigSaveError as e:
                logger.error("Failed to save monitor selection: %s", e)
                self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
        else:
            self.current_monitor = ""

        self.right_panel_visible = self.config.ui.right_panel_visible
        self.all_presets: list[dict[str, Any]] = []
        # M2: dict by id for fast lookup in _on_tree_motion / словарь по id для быстрого поиска
        self.all_presets_by_id: dict[str, dict[str, Any]] = {}
        # M5: presets cache (invalidated in update_ui_from_config) / кэш пресетов
        self._presets_cache: list[Preset] | None = None
        # C1: pending gamma timer id for apply_manual debounce / id таймера debounce apply_manual
        self._pending_gamma: str | None = None
        self._last_gamma_apply_ms: int = 0  # Throttle timestamp for xrandr calls

        self.tooltip_window: tk.Toplevel | None = None
        self.tooltip_timer: str | None = None
        self.tooltip_current_item: str | None = None

        self.resize_timer: str | None = None  # ← ДОБАВИТЬ ЭТУ СТРОКУ

        self.current_menu: tk.Menu | None = None  # ← тоже полезно добавить

        self.use_zenity = self._check_zenity()

    def _check_zenity(self) -> bool:
        """Check if zenity is available / Проверить доступность zenity."""
        try:
            result = subprocess.run(
                ["zenity", "--version"], capture_output=True, timeout=ZENITY_CHECK_TIMEOUT
            )
            available = result.returncode == 0
            if available:
                logger.info("Zenity detected, will use native file dialogs")
            return available
        except Exception:
            return False

    def _calculate_window_geometry(self) -> None:
        """Calculate and apply window geometry / Вычислить и применить геометрию окна.

        HiDPI-aware: after _setup_dpi_scaling() has multiplied the fixed pixel
        constants, the computed window size may exceed the monitor. We clamp the
        library panel width down (or hide it) so the window fits on screen.
        / HiDPI-осведомлённый: после _setup_dpi_scaling() фиксированные пиксельные
        константы умножены, и вычисленный размер окна может превысить монитор.
        Уменьшаем ширину библиотечной панели (или скрываем её), чтобы окно влезло.
        """
        content_h = self._calculate_content_height()
        total_h = max(content_h + HEIGHT_RESERVE, MIN_WINDOW_HEIGHT)

        # Determine the TARGET monitor: the one where the saved window was last
        # closed. If no saved geometry or it doesn't match any monitor, fall back
        # to primary. This is critical for clamping — we must clamp to the monitor
        # the window will actually appear on, not necessarily the primary.
        # / Определяем ЦЕЛЕВОЙ монитор: тот, где окно было последний раз закрыто.
        # Если нет сохранённой геометрии или она не совпадает ни с одним монитором,
        # fallback на primary. Это критично для clamping — нужно ограничивать по
        # монитору, на котором окно реально появится, а не обязательно primary.
        saved_geom = self.config.ui.window_geometry
        target_monitor_name = None
        if saved_geom:
            try:
                parts = saved_geom.split("x")
                saved_w = int(parts[0])
                rest = parts[1].split("+")
                saved_x = int(rest[1]) if len(rest) > 1 else 0
                target_monitor_name = self._detect_monitor_at_x(saved_x + saved_w // 2)
            except (IndexError, ValueError):
                pass
        mx, my, mw, mh = self._get_monitor_geometry(target_monitor_name)
        logger.debug(
            "Target monitor for geometry: %s (%dx%d+%d+%d)",
            target_monitor_name or "primary",
            mw,
            mh,
            mx,
            my,
        )

        # Determine library width, clamping it if the full window would exceed the monitor.
        # / Определяем ширину панели пресетов, уменьшая если полное окно не влезает в монитор.
        base_content_w = CONTENT_FIXED_WIDTH + STRIP_WIDTH
        avail_for_library = max(0, mw - base_content_w - 20)  # 20 px margin
        current_lib_width = min(LIBRARY_WIDTH, avail_for_library) if self.right_panel_visible else 0
        if self.right_panel_visible and current_lib_width < MIN_LIBRARY_WIDTH:
            # Not enough room for the library panel — hide it for this session.
            # / Недостаточно места для библиотечной панели — скрываем на эту сессию.
            logger.info(
                "Hiding library panel: not enough room (avail=%d, min=%d)",
                avail_for_library,
                MIN_LIBRARY_WIDTH,
            )
            self.right_panel_visible = False
            current_lib_width = 0
        full_w = base_content_w + current_lib_width
        min_lib_w = min(MIN_LIBRARY_WIDTH, avail_for_library) if self.right_panel_visible else 0
        # Fixed-size window (Variant 4): lock both minsize and maxsize to the
        # computed (full_w, total_h) so the user can't drag-resize the window.
        # The actual size is set below via self.root.geometry(...).
        # / Окно фиксированного размера (Variant 4): фиксируем minsize и maxsize
        # в вычисленных (full_w, total_h), чтобы пользователь не мог менять размер
        # перетаскиванием. Реальный размер устанавливается ниже через geometry().
        self.root.minsize(full_w, total_h)
        self.root.maxsize(full_w, total_h)

        # Clamp total height to monitor height with a small margin.
        # / Ограничиваем высоту по высоте монитора с небольшим запасом.
        if total_h > mh - 20:
            total_h = max(MIN_WINDOW_HEIGHT, mh - 20)
            logger.info("Clamped window height to monitor: %d", total_h)
            # Re-lock min/max after height clamping so the window stays fixed-size.
            # / Перефиксируем min/max после clamping высоты, чтобы окно осталось фиксированным.
            self.root.minsize(full_w, total_h)
            self.root.maxsize(full_w, total_h)

        saved_geom = self.config.ui.window_geometry
        if saved_geom:
            parts = saved_geom.split("x")
            saved_w = int(parts[0])
            rest = parts[1].split("+")
            saved_x = int(rest[1]) if len(rest) > 1 else 0
            saved_y = int(rest[2]) if len(rest) > 2 else 0

            # Variant 4 (fixed size): we ALWAYS use the computed `full_w` for the
            # window width — never `saved_w`. The saved geometry may have been
            # recorded at a different UI scale or with a different library panel
            # state, so trusting it would produce a wrong-sized window. We only
            # reuse the saved X/Y position (clamped to the current monitor).
            # / Variant 4 (фиксированный размер): ВСЕГДА используем вычисленный
            # `full_w` для ширины окна — никогда `saved_w`. Сохранённая геометрия
            # могла быть записана при другом масштабе UI или с другим состоянием
            # библиотечной панели, поэтому доверять ей нельзя — получился бы неправильный
            # размер. Переиспользуем только сохранённую позицию X/Y (с ограничением
            # по текущему монитору).
            monitor_margin = 20  # px margin from screen edges / отступ от краёв экрана
            # Clamp X so the window stays on the current monitor (don't let it open
            # off-screen if the saved position was on a now-disconnected monitor).
            # / Ограничиваем X, чтобы окно оставалось на текущем мониторе (не дать
            # ему открыться за экраном, если позиция была на отключённом мониторе).
            if saved_x < mx:
                saved_x = mx
            elif saved_x + full_w > mx + mw - monitor_margin:
                saved_x = max(mx, mx + mw - full_w - monitor_margin)
            # Clamp Y similarly (height may have changed too).
            if saved_y < my:
                saved_y = my
            elif saved_y + total_h > my + mh - monitor_margin:
                saved_y = max(my, my + mh - total_h - monitor_margin)

            self.root.geometry(f"{full_w}x{total_h}+{saved_x}+{saved_y}")
            logger.debug(
                "Applied saved window geometry: %s -> fixed size %dx%d at +%d+%d",
                saved_geom,
                full_w,
                total_h,
                saved_x,
                saved_y,
            )
            # If the library panel was hidden due to monitor width clamping (above),
            # actually remove it from the PanedWindow now — _build_interface already ran
            # and added it, so we need to forget it to match the new right_panel_visible.
            # / Если библиотечная панель была скрыта из-за clamping ширины (выше),
            # реально удаляем её из PanedWindow сейчас — _build_interface уже отработал
            # и добавил её, нужно forget чтобы соответствовать новому right_panel_visible.
            if not self.right_panel_visible and hasattr(self, "library_frame"):
                try:
                    self._hide_library_no_resize()
                except Exception as e:
                    logger.debug("Could not hide library panel after clamping: %s", e)
        else:
            x = mx + (mw - full_w) // 2
            y = my + (mh - total_h) // 2
            x = max(mx, min(x, mx + mw - full_w))
            y = max(my, min(y, my + mh - total_h))
            self.root.geometry(f"{full_w}x{total_h}+{x}+{y}")
            logger.debug("Applied default window geometry: %sx%s+%s+%s", full_w, total_h, x, y)

    def _build_interface(self) -> None:
        """Build user interface / Построить пользовательский интерфейс."""
        self.paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL, sashwidth=0, bd=0, bg=self.colors.bg
        )
        self.paned.pack(fill=tk.BOTH, expand=True)
        self.paned.pack_propagate(False)

        self._build_content_panel()
        self._build_library_panel()

        self.root.update_idletasks()
        self.draw_color_strip()

        if self.right_panel_visible:
            self.paned.sash_place(0, CONTENT_FIXED_WIDTH, 0)
            self.paned.sash_place(1, CONTENT_FIXED_WIDTH + STRIP_WIDTH, 0)
        else:
            self._hide_library_no_resize()

    def _show_window(self) -> None:
        """Show the main window after geometry is set / Показать окно после установки геометрии."""
        self.root.deiconify()
        if self.right_panel_visible:
            self.draw_toggle_arrow(True)

    def _build_content_panel(self) -> None:
        """Build content panel / Построить панель контента."""
        self.content_frame = tk.Frame(self.paned, width=CONTENT_FIXED_WIDTH, bg=self.colors.bg)
        self.inner_content = tk.Frame(self.content_frame, bg=self.colors.bg)
        self.inner_content.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=INNER_PADX, pady=INNER_PADY
        )

        self.toggle_strip = tk.Canvas(
            self.paned,
            width=STRIP_WIDTH,
            bg=self.colors.toggle_strip_bg,
            highlightthickness=0,
            cursor="hand2",
        )

        self.content_frame.propagate(False)
        self.paned.add(self.content_frame, minsize=CONTENT_FIXED_WIDTH)
        self.paned.add(self.toggle_strip, minsize=STRIP_WIDTH)

        self._build_monitor_buttons(self.inner_content)
        self._build_favorites_panel(self.inner_content)
        self._build_sliders(self.inner_content)
        self._build_save_button(self.inner_content)
        self._build_test_strip(self.inner_content)

    def _build_monitor_buttons(self, parent: tk.Widget) -> None:
        """Build monitor buttons / Построить кнопки мониторов."""
        mon_frame = tk.Frame(parent, bg=self.colors.bg)
        mon_frame.pack(fill=tk.X, pady=SECTION_PADY)
        self.monitor_var = tk.StringVar(value=self.current_monitor)
        monitor_colors = generate_monitor_colors(len(self.monitors), self.colors.is_dark)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        for idx, monitor in enumerate(self.monitors):
            text_color = monitor_colors[idx]
            btn = tk.Radiobutton(
                mon_frame,
                text=monitor.name,
                variable=self.monitor_var,
                value=monitor.name,
                indicatoron=False,
                command=self.on_monitor_change,
                font=FONT_MONITOR,
                width=MONITOR_BTN_WIDTH,
                bg=self.colors.bg,
                fg=text_color,
                selectcolor=self.colors.select_bg,
                activebackground=self.colors.select_bg,
                activeforeground=text_color,
                relief="flat",
                bd=0,
                highlightthickness=MONITOR_BUTTON_HIGHLIGHT,
                highlightbackground=inactive_border,
                highlightcolor=COLOR_FOCUS,
            )
            row = idx // BUTTONS_PER_ROW
            col = idx % BUTTONS_PER_ROW
            btn.grid(
                row=row,
                column=col,
                sticky="ew",
                padx=MONITOR_BTN_PADX,
                pady=MONITOR_BTN_PADY,
                ipady=MONITOR_BTN_IPADY,
            )
        mon_frame.columnconfigure(0, weight=1)
        mon_frame.columnconfigure(1, weight=1)

    def _build_favorites_panel(self, parent: tk.Widget) -> None:
        """Build favorites panel / Построить панель избранного."""
        fav_frame = tk.Frame(parent, bg=self.colors.bg)
        fav_frame.pack(fill=tk.X, pady=SECTION_PADY)

        # Header row: "★ Избранное (ПКМ для удаления)" label on the left,
        # "🌐" apply-to-all button on the right.
        # / Ряд заголовка: метка «★ Избранное...» слева, кнопка «🌐» справа.
        header = tk.Frame(fav_frame, bg=self.colors.bg)
        header.pack(fill=tk.X, pady=(0, 2))
        tk.Label(
            header,
            text=tr("favorites"),
            font=FONT_LIBRARY_HEADER,
            bg=self.colors.bg,
            fg=self.colors.fg,
        ).pack(side=tk.LEFT)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )
        all_btn = tk.Button(
            header,
            text="🌐",
            command=self.apply_to_all_monitors,
            font=FONT_FAVORITE,
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        )
        all_btn.pack(side=tk.RIGHT)
        # Tooltip: show on hover, hide on leave.
        # / Подсказка: показ при наведении, скрытие при уходе.
        all_btn.bind(DIALOG_MOTION_BIND, lambda e: self._show_tooltip(e, tr("apply_to_all_tooltip")), add="+")
        all_btn.bind(DIALOG_LEAVE_BIND, self._hide_tooltip, add="+")

        self.fav_buttons: list[tk.Button] = []
        for i in range(MAX_FAVORITES):
            btn = tk.Button(
                fav_frame,
                text=tr("slot", i + 1),
                height=FAV_BTN_HEIGHT,
                command=lambda idx=i: self.activate_favorite_slot(idx),
                font=FONT_FAVORITE,
                bg=self.colors.bg,
                fg=self.colors.fg,
                activebackground=self.colors.select_bg,
                activeforeground=self.colors.select_fg,
                relief="solid",
                bd=FAV_BUTTON_BORDER_THICKNESS,
            )
            btn.pack(fill=tk.X, pady=FAV_BTN_PADY)
            btn.bind(DIALOG_RIGHT_CLICK_BIND, lambda e, idx=i: self.remove_from_favorites(idx))
            self.fav_buttons.append(btn)

    def _build_sliders(self, parent: tk.Widget) -> None:
        """Build RGB sliders / Построить слайдеры RGB."""
        slider_frame = tk.LabelFrame(
            parent,
            text=tr("color_adjustment"),
            padx=SLIDER_FRAME_PADX,
            pady=SLIDER_FRAME_PADY,
            bg=self.colors.bg,
            fg=self.colors.fg,
            relief="flat",
            bd=0,
        )
        slider_frame.pack(fill=tk.X, pady=SECTION_PADY)
        self.r_val = tk.DoubleVar(value=1.0)
        self.g_val = tk.DoubleVar(value=1.0)
        self.b_val = tk.DoubleVar(value=1.0)

        self.r_slider, self.r_label = self._create_slider(slider_frame, "red", self.r_val, 0)
        self.g_slider, self.g_label = self._create_slider(slider_frame, "green", self.g_val, 1)
        self.b_slider, self.b_label = self._create_slider(slider_frame, "blue", self.b_val, 2)

    def _create_slider(
        self, parent: tk.Widget, label_key: str, var: tk.DoubleVar, row_idx: int
    ) -> tuple[tk.Scale, tk.Label]:
        """
        Create slider with flat design, color indicator, and tall trough matching button height.
        Создать слайдер с плоским дизайном, цветным индикатором и высоким жёлобом,
        совпадающим по высоте с кнопками ±.

        Layout (grid, 5 columns):
            [0] color indicator (Canvas square)
            [1] channel label "R: 1.00"
            [2] "−" button
            [3] Scale (expands)
            [4] "+" button

        Layout (grid, 5 колонок):
            [0] цветной индикатор (квадрат Canvas)
            [1] метка канала "R: 1.00"
            [2] кнопка "−"
            [3] слайдер (растягивается)
            [4] кнопка "+"

        Args:
            parent: Parent widget / Родительский виджет
            label_key (str): Translation key / Ключ перевода
            var: Tkinter variable / Переменная Tkinter
            row_idx (int): Row index / Индекс строки

        Returns / Возвращает:
            Tuple[tk.Scale, tk.Label]: (Scale widget, Label widget)
        """
        bg = self.colors.bg
        fg = self.colors.fg
        select_bg = self.colors.select_bg
        trough = self.colors.trough
        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        channel_colors = {
            "red": COLOR_CHANNEL_RED,
            "green": COLOR_CHANNEL_GREEN,
            "blue": COLOR_CHANNEL_BLUE,
        }
        active_color = channel_colors.get(label_key.lower(), COLOR_CHANNEL_DEFAULT)

        # [col 0] Color indicator — small filled square showing the channel's color.
        # / [кол 0] Цветной индикатор — маленький залитый квадрат цвета канала.
        indicator = tk.Canvas(
            parent,
            width=SLIDER_INDICATOR_SIZE,
            height=SLIDER_INDICATOR_SIZE,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        indicator.create_rectangle(
            0,
            0,
            SLIDER_INDICATOR_SIZE,
            SLIDER_INDICATOR_SIZE,
            fill=active_color,
            outline="",
        )
        indicator.grid(
            row=row_idx,
            column=0,
            sticky="",
            pady=SLIDER_ROW_PADY,
            padx=SLIDER_INDICATOR_PADX,
        )

        # [col 1] Channel label with current value (e.g. "Red (R): 1.00")
        # / [кол 1] Метка канала со значением (напр. "Красный (R): 1.00")
        lbl = tk.Label(
            parent,
            text=tr(f"{label_key}_value", 1.0),
            anchor="w",
            font=FONT_SLIDER_LABEL,
            width=SLIDER_LABEL_WIDTH,
            bg=bg,
            fg=fg,
        )
        lbl.grid(row=row_idx, column=1, sticky="w", pady=SLIDER_ROW_PADY)

        # [col 2] Minus button — larger bold glyph, extra pady for height.
        # / [кол 2] Кнопка минус — крупный жирный знак, доп. pady для высоты.
        btn_minus = tk.Button(
            parent,
            text="-",
            font=SLIDER_BUTTON_FONT,
            width=SLIDER_BTN_WIDTH,
            pady=SLIDER_BTN_PADY,
            command=lambda: self._adjust_slider(var, -SLIDER_STEP),
            repeatdelay=AUTO_REPEAT_DELAY,
            repeatinterval=AUTO_REPEAT_INTERVAL,
            bg=bg,
            fg=fg,
            activebackground=select_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightthickness=SLIDER_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        )
        btn_minus.grid(
            row=row_idx, column=2, sticky="e", pady=SLIDER_ROW_PADY, padx=SLIDER_BTN_MINUS_PADX
        )

        # [col 3] Scale — trough thickness matches the ± buttons so they look aligned.
        # / [кол 3] Слайдер — толщина жёлоба совпадает с кнопками ±, выравнивание по центру.
        # Note: for a HORIZONTAL tk.Scale, `width` controls the trough thickness (vertical
        # height of the groove), while `length` controls the horizontal span. There is no
        # `-height` option on tk.Scale (that's a ttk.Scale thing) — using it raises TclError.
        # / Примечание: для ГОРИЗОНТАЛЬНОГО tk.Scale `width` задаёт толщину жёлоба (вертикальную
        # высоту канавки), а `length` — горизонтальную длину. Опции `-height` у tk.Scale нет
        # (это особенность ttk.Scale) — её использование вызывает TclError.
        s = tk.Scale(
            parent,
            from_=SLIDER_MIN,
            to=SLIDER_MAX,
            variable=var,
            resolution=SLIDER_STEP,
            orient=SCALE_ORIENT,
            showvalue=SCALE_SHOWVALUE,
            sliderlength=SLIDER_LENGTH,
            width=SLIDER_TROUGH_HEIGHT,
            borderwidth=0,
            highlightthickness=0,
            bg=bg,
            fg=fg,
            troughcolor=trough,
            activebackground=active_color,
            command=lambda v: self.apply_manual(),
        )
        s.grid(row=row_idx, column=3, sticky="ew", padx=2, pady=SLIDER_ROW_PADY)

        def on_trough_click(event: tk.Event) -> None:
            """Handle instant jump when clicking on the empty slider track."""
            element = s.identify(event.x, event.y)
            if "trough" in element:
                width = s.winfo_width()
                if width <= 1:
                    return
                click_ratio = max(0.0, min(1.0, event.x / width))
                value_range = SLIDER_MAX - SLIDER_MIN
                raw_value = SLIDER_MIN + (click_ratio * value_range)
                stepped_value = round(raw_value / SLIDER_STEP) * SLIDER_STEP
                final_value = max(SLIDER_MIN, min(SLIDER_MAX, stepped_value))
                var.set(final_value)
                self.apply_manual()
                s.event_generate("<B1-Motion>", x=event.x, y=event.y)

        s.bind(DIALOG_LEFT_CLICK_BIND, on_trough_click, add="+")

        # [col 4] Plus button — same styling as minus.
        # / [кол 4] Кнопка плюс — тот же стиль, что у минус.
        btn_plus = tk.Button(
            parent,
            text="+",
            font=SLIDER_BUTTON_FONT,
            width=SLIDER_BTN_WIDTH,
            pady=SLIDER_BTN_PADY,
            command=lambda: self._adjust_slider(var, SLIDER_STEP),
            repeatdelay=AUTO_REPEAT_DELAY,
            repeatinterval=AUTO_REPEAT_INTERVAL,
            bg=bg,
            fg=fg,
            activebackground=select_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightthickness=SLIDER_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        )
        btn_plus.grid(
            row=row_idx, column=4, sticky="w", pady=SLIDER_ROW_PADY, padx=SLIDER_BTN_PLUS_PADX
        )

        # Only the Scale column (3) should expand horizontally.
        # / Только колонка слайдера (3) растягивается по горизонтали.
        parent.columnconfigure(3, weight=1)
        return s, lbl

    def _build_save_button(self, parent: tk.Widget) -> None:
        """Build save + reset buttons row / Построить ряд кнопок сохранения и сброса."""
        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )
        # Row with two buttons: "Save as new" (expand) + "Reset" (auto width)
        # / Ряд из двух кнопок: «Сохранить» (растягивается) + «Сброс» (авто-ширина)
        btn_row = tk.Frame(parent, bg=self.colors.bg)
        btn_row.pack(fill=tk.X, pady=BUTTON_PADY)
        tk.Button(
            btn_row,
            text=tr("save_as_new"),
            command=self.save_current_as_new,
            font=FONT_DIALOG,  # scaled font / масштабируемый шрифт
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(
            btn_row,
            text=tr("reset"),
            command=self.reset_gamma,
            font=FONT_DIALOG,  # scaled font / масштабируемый шрифт
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        ).pack(side=tk.LEFT, padx=(5, 0))

    def reset_gamma(self) -> None:
        """
        Reset current monitor's gamma to neutral RGB(1.0, 1.0, 1.0).
        Сбросить гамму текущего монитора к нейтральному RGB(1.0, 1.0, 1.0).
        """
        if not self.current_monitor:
            return
        neutral = RGB(r=1.0, g=1.0, b=1.0)
        # Move sliders to neutral position, then apply via the existing async path.
        # / Ставим слайдеры в нейтраль и применяем через существующий асинхронный путь.
        self.r_val.set(neutral.r)
        self.g_val.set(neutral.g)
        self.b_val.set(neutral.b)
        self._set_slider_labels(neutral)
        self.apply_manual()

    def apply_to_all_monitors(self) -> None:
        """
        Apply the CURRENT slider values to ALL connected monitors at once.
        Применяет ТЕКУЩИЕ значения слайдеров ко ВСЕМ подключенным мониторам сразу.

        Reads the current RGB from the sliders, then calls apply_gamma for each
        monitor in a separate daemon thread (so the UI doesn't freeze). Saves
        the gamma for each monitor in config.
        / Читает текущие RGB со слайдеров, затем вызывает apply_gamma для каждого
        монитора в отдельном daemon-потоке (чтобы UI не зависал). Сохраняет гамму
        для каждого монитора в config.
        """
        if not self.monitors:
            logger.warning("apply_to_all_monitors: no monitors detected")
            return
        # Skip if a dialog is open (same guard as other hotkeys).
        # / Пропускаем если открыт диалог (как другие горячие клавиши).
        if self._is_dialog_open():
            logger.debug("apply_to_all_monitors: dialog open, skipping")
            return
        rgb = RGB(r=self.r_val.get(), g=self.g_val.get(), b=self.b_val.get())
        logger.info(
            "Applying RGB to ALL monitors: R=%.2f G=%.2f B=%.2f", rgb.r, rgb.g, rgb.b
        )

        def worker() -> None:
            for monitor in self.monitors:
                try:
                    success, msg = apply_gamma(monitor.name, rgb)
                    if success:
                        # Save gamma for this monitor in config.
                        # / Сохраняем гамму для этого монитора в config.
                        self.config.system.monitor_gammas[monitor.name] = rgb.to_list()
                        logger.info(
                            "Applied to %s: R=%.2f G=%.2f B=%.2f",
                            monitor.name, rgb.r, rgb.g, rgb.b,
                        )
                    else:
                        logger.warning("Failed to apply to %s: %s", monitor.name, msg)
                except Exception as e:
                    logger.error("Error applying to %s: %s", monitor.name, e)

        def on_done() -> None:
            # Save config and update UI after all monitors are done.
            # / Сохраняем config и обновляем UI после завершения.
            self.config.system.last_rgb = rgb.to_list()
            try:
                save_config(self.config)
            except ConfigSaveError as e:
                logger.error("Failed to save config after apply_to_all: %s", e)
            self.update_active_indicator()
            logger.info("Apply-to-all complete")

        def poll() -> None:
            if not thread.is_alive():
                on_done()
            else:
                self.root.after(100, poll)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.root.after(100, poll)

    def _build_test_strip(self, parent: tk.Widget) -> None:
        """Build test color strip / Построить тестовую цветную полоску."""
        test_frame = tk.LabelFrame(
            parent,
            text=tr("test"),
            padx=0,
            pady=5,
            bg=self.colors.bg,
            fg=self.colors.fg,
            relief="flat",
            bd=0,
        )
        test_frame.pack(fill=tk.X, pady=SECTION_PADY)
        self.color_canvas = tk.Canvas(
            test_frame, height=CANVAS_HEIGHT, bd=0, highlightthickness=0, bg=self.colors.bg
        )
        self.color_canvas.pack(fill=tk.X, expand=True, padx=CANVAS_PADX)

    def _build_library_panel(self) -> None:
        "Build preset panel / Построить панель пресетов."
        self.library_frame = tk.Frame(self.paned, bg=self.colors.bg)
        bg = self.colors.bg
        fg = self.colors.fg
        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        header_frame = tk.Frame(self.library_frame, bg=bg)
        header_frame.pack(fill=tk.X, pady=HEADER_PADY)
        tk.Label(header_frame, text=tr("library"), bg=bg, fg=fg, font=FONT_LIBRARY_HEADER).pack(
            side=tk.LEFT
        )
        btn_frame = tk.Frame(header_frame, bg=bg)
        btn_frame.pack(side=tk.RIGHT)
        tk.Button(
            btn_frame,
            text=tr("import"),
            command=self.import_presets,
            font=FONT_SEARCH,
            bg=bg,
            fg=fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        ).pack(side=tk.LEFT, padx=IMPORT_EXPORT_PADX)
        tk.Button(
            btn_frame,
            text=tr("export"),
            command=self.export_presets,
            font=FONT_SEARCH,
            bg=bg,
            fg=fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
        ).pack(side=tk.LEFT, padx=IMPORT_EXPORT_PADX)

        search_frame = tk.Frame(self.library_frame, bg=bg)
        search_frame.pack(fill=tk.X, padx=SEARCH_PADX, pady=SEARCH_PADY)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=FONT_SEARCH)
        self.search_entry.pack(fill=tk.X)
        self.search_entry.insert(0, tr("search_placeholder"))
        self.search_entry.configure(foreground=self.colors.field_placeholder_fg)

        list_wrapper = tk.Frame(self.library_frame, bg=bg)
        # M10: use pack(fill=BOTH, expand=True) instead of place() with magic offsets;
        # header_frame and search_frame above are packed with fill=X, so list_wrapper
        # automatically takes the remaining vertical space.
        # / M10: pack(fill=BOTH, expand=True) вместо place() с магическими смещениями;
        # header_frame и search_frame выше упакованы с fill=X, поэтому list_wrapper
        # автоматически занимает оставшееся вертикальное пространство.
        list_wrapper.pack(fill=tk.BOTH, expand=True, padx=TREEVIEW_WRAPPER_X)
        tree_frame = tk.Frame(list_wrapper, bg=bg)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.preset_tree = ttk.Treeview(
            tree_frame,
            columns=(TREEVIEW_COLUMN_VALUES,),
            show="tree",
            selectmode="browse",
            height=TREEVIEW_HEIGHT,
        )
        self.preset_tree.column("#0", stretch=True)
        self.preset_tree.column(TREEVIEW_COLUMN_VALUES, width=0, stretch=False)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.preset_tree.yview)
        self.preset_tree.configure(yscrollcommand=scrollbar.set)
        self.preset_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure(
            "Treeview",
            rowheight=TREEVIEW_ROWHEIGHT,
            font=FONT_TREEVIEW,
            background=bg,
            foreground=fg,
            fieldbackground=bg,
        )
        style.map(
            "Treeview",
            background=[("selected", self.colors.select_bg)],
            foreground=[("selected", self.colors.select_fg)],
        )
        # TEntry style — make the search entry match the theme colors.
        # / Стиль TEntry — оформляем поле поиска под цвета темы.
        style.configure(
            "TEntry",
            fieldbackground=self.colors.field_bg,
            foreground=self.colors.field_fg,
            insertcolor=self.colors.field_cursor,
            bordercolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
            lightcolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
            darkcolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
        )
        # TSpinbox style — used in the edit-preset dialog. Make the spinbox taller
        # (arrowsize controls the height of the up/down button area, which also
        # increases the overall spinbox height). arrowcolor must contrast with the
        # field background — on dark themes, use white arrows.
        # / Стиль TSpinbox — используется в диалоге редактирования пресета.
        # Делаем спинбокс выше (arrowsize задаёт высоту области кнопок up/down,
        # что также увеличивает общую высоту спинбокса). arrowcolor должен
        # контрастировать с фоном поля — в тёмных темах используем белые стрелки.
        style.configure(
            "TSpinbox",
            fieldbackground=self.colors.field_bg,
            foreground=self.colors.field_fg,
            arrowcolor=self.colors.fg,
            insertcolor=self.colors.field_cursor,
            bordercolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
            lightcolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
            darkcolor=COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT,
            arrowsize=SPINBOX_ARROWSIZE,  # px — scaled with UI / масштабируется с UI
        )

        self.paned.add(self.library_frame)

    def _bind_events(self) -> None:
        """Bind event handlers / Привязать обработчики событий."""
        # Unbind root-level bindings before re-binding (root survives rebuild).
        # / Отвязываем root-level привязки перед повторной привязкой (root переживает rebuild).
        for evt in (DIALOG_CONFIGURE_BIND, "<Escape>"):
            try:
                self.root.unbind(evt)
            except Exception:
                pass
        self.toggle_strip.bind(DIALOG_LEFT_CLICK_BIND, self.toggle_right_panel)
        self.search_entry.bind(DIALOG_FOCUS_IN_BIND, lambda e: self._on_search_focus_in())
        self.search_entry.bind(DIALOG_FOCUS_OUT_BIND, lambda e: self._on_search_focus_out())
        self.search_var.trace_add("write", lambda *args: self._filter_presets())
        self.preset_tree.bind(DIALOG_DOUBLE_CLICK_BIND, self.on_tree_double_click)
        self.preset_tree.bind(DIALOG_RIGHT_CLICK_BIND, self.on_tree_right_click)
        self.root.bind(DIALOG_CONFIGURE_BIND, self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._bind_hotkeys()

        self.update_ui_from_config()
        self.load_monitor_gamma()

    def _is_text_widget_focused(self) -> bool:
        """
        Check if a text-input widget (Entry/Text/Spinbox) currently has focus.
        Проверяет, находится ли сейчас в фокусе виджет ввода текста (Entry/Text/Spinbox).
        Used to decide whether digit hotkeys (1-5) should be intercepted or passed through.
        Используется для решения: перехватывать цифровые горячие клавиши (1-5) или пропустить.

        Returns True (treat as text-focused) when focus cannot be determined — this happens
        when a native file dialog (__tk_filedialog) or zenity dialog is open and focus_get()
        raises KeyError on the temporary widget path. Treating it as text-focused is safe:
        all hotkeys that filter on this (Ctrl+S, 1-5, Escape) are skipped, letting the
        dialog handle the key normally.
        / Возвращает True (считаем, что фокус в тексте), если фокус не удалось определить —
        это происходит, когда открыт нативный файловый диалог (__tk_filedialog) или zenity,
        и focus_get() бросает KeyError на временном пути виджета. Считать текстовым фокусом
        безопасно: все горячие клавиши, фильтрующиеся по этому признаку (Ctrl+S, 1-5, Escape),
        пропускаются, позволяя диалогу обработать клавишу штатно.
        """
        try:
            focused = self.root.focus_get()
        except KeyError:
            # Raised when a native file dialog (__tk_filedialog) is open — its widget path
            # is not registered in our root's children dict. Treat as text-focused so that
            # Ctrl+S / 1-5 / Escape hotkeys don't interfere with the dialog.
            # / Возникает при открытом нативном файловом диалоге (__tk_filedialog) — путь
            # его виджета не зарегистрирован в children нашего root. Считаем текстовым фокусом,
            # чтобы Ctrl+S / 1-5 / Escape не мешали диалогу.
            return True
        except Exception:
            # Any other focus_get() failure — be conservative and skip hotkeys.
            # / Любая другая ошибка focus_get() — консервативно пропускаем горячие клавиши.
            return True
        if focused is None:
            return False
        # tk.Entry, ttk.Entry, tk.Text, ttk.Spinbox, tk.Spinbox — all accept text input
        # / все эти виджеты принимают текстовый ввод
        return isinstance(focused, (tk.Entry, ttk.Entry, tk.Text, tk.Spinbox, ttk.Spinbox))

    def _bind_hotkeys(self) -> None:
        """Bind global keyboard shortcuts / Привязать глобальные горячие клавиши.

        Idempotent: unbinds ALL previously bound hotkeys first, so calling this
        multiple times (e.g. after a UI rebuild) doesn't accumulate handlers.
        / Идемпотентный: сначала отвязывает ВСЕ ранее привязанные горячие клавиши,
        поэтому многократный вызов (напр. после rebuild UI) не накапливает обработчики.
        """
        # Unbind ALL previously bound hotkeys first. Without this, bind_all() with
        # add="+" accumulates handlers on every rebuild — after N rebuilds, each
        # hotkey fires N+1 times (e.g. N+1 file dialogs open on Ctrl+I).
        # / Сначала отвязываем ВСЕ ранее привязанные горячие клавиши. Без этого
        # bind_all() с add="+" накапливает обработчики при каждом rebuild — после
        # N rebuild каждая клавиша срабатывает N+1 раз (напр. N+1 диалогов на Ctrl+I).
        hotkey_events = [
            "<Control-s>", "<Control-i>", "<Control-e>", "<Control-f>",
            "<Control-plus>", "<Control-KP_Add>",
            "<Control-minus>", "<Control-KP_Subtract>",
            "<Control-0>", "<Control-KP_0>",
            "<Control-Shift-A>",
        ]
        for i in range(1, MAX_FAVORITES + 1):
            hotkey_events.append(f"<Key-{i}>")
        for evt in hotkey_events:
            try:
                self.root.unbind_all(evt)
            except Exception:
                pass

        # Ctrl+S/I/E/F use bind_all — they work regardless of focus
        # / Ctrl+S/I/E/F через bind_all — работают независимо от фокуса
        self.root.bind_all("<Control-s>", lambda e: self._hotkey_save())
        self.root.bind_all("<Control-i>", lambda e: self.import_presets())
        self.root.bind_all("<Control-e>", lambda e: self.export_presets())
        self.root.bind_all("<Control-f>", lambda e: self._hotkey_focus_search())
        # Digit hotkeys 1-5
        # / Цифры 1-5
        for i in range(1, MAX_FAVORITES + 1):
            self.root.bind_all(
                f"<Key-{i}>",
                lambda e, idx=i - 1: self._hotkey_slot(idx),
            )
        # Escape: close window. Use root.bind (NOT bind_all) so it only fires when
        # the main window has focus — Toplevel dialogs have their own <Escape>
        # binding and grab_set() prevents root from receiving events while open.
        # / Escape: закрыть окно. Используем root.bind (НЕ bind_all), чтобы
        # срабатывало только при фокусе на главном окне — Toplevel-диалоги имеют
        # собственную привязку <Escape>, а grab_set() не даёт root получать события.
        self.root.bind("<Escape>", lambda e: self._hotkey_escape())
        # Ctrl++ / Ctrl+- / Ctrl+0 — change UI scale at runtime (rebuilds the window).
        # / Ctrl++ / Ctrl+- / Ctrl+0 — смена масштаба UI в рантайме (перестраивает окно).
        self.root.bind_all("<Control-plus>", lambda e: self._change_ui_scale(+0.25))
        self.root.bind_all("<Control-KP_Add>", lambda e: self._change_ui_scale(+0.25))
        self.root.bind_all("<Control-minus>", lambda e: self._change_ui_scale(-0.25))
        self.root.bind_all("<Control-KP_Subtract>", lambda e: self._change_ui_scale(-0.25))
        self.root.bind_all("<Control-0>", lambda e: self._reset_ui_scale())
        self.root.bind_all("<Control-KP_0>", lambda e: self._reset_ui_scale())
        # Ctrl+Shift+A — apply current RGB to ALL monitors.
        # / Ctrl+Shift+A — применить текущие RGB ко ВСЕМ мониторам.
        self.root.bind_all("<Control-Shift-A>", lambda e: self.apply_to_all_monitors())

    def _change_ui_scale(self, delta: float) -> None:
        """
        Increase or decrease the UI scale by `delta` (in scale units) and rebuild
        the window. The new scale is rounded to UI_SCALE_STEP and clamped to
        [UI_SCALE_MIN, UI_SCALE_MAX]. If the clamped/rounded value matches the
        current one, nothing happens.
        / Увеличивает или уменьшает масштаб UI на `delta` (в единицах scale) и
        перестраивает окно. Новый масштаб округляется до UI_SCALE_STEP и
        ограничивается диапазоном [UI_SCALE_MIN, UI_SCALE_MAX]. Если новое
        значение совпадает с текущим — ничего не происходит.
        """
        current = getattr(self, "ui_scale", 1.0)
        new = round_to_scale_step(current + delta)
        new = max(UI_SCALE_MIN, min(UI_SCALE_MAX, new))
        if abs(new - current) < 0.001:
            logger.debug("UI scale unchanged: %.2f (delta=%.2f)", current, delta)
            return
        logger.info("UI scale change: %.2f -> %.2f (delta=%.2f)", current, new, delta)
        self._rebuild_ui_with_scale(new)

    def _reset_ui_scale(self) -> None:
        """
        Reset the UI scale to the auto-detected value (drops the saved `ui_scale`
        from config and re-runs auto-detection).
        / Сбрасывает масштаб UI к авто-детекту (удаляет сохранённый `ui_scale`
        из конфига и заново выполняет авто-детект).
        """
        logger.info("UI scale reset to auto-detect")
        self._rebuild_ui_with_scale(None)

    def _rebuild_ui_with_scale(self, new_scale: float | None) -> None:
        """
        Tear down the current UI and rebuild it at `new_scale`.
        Разрушает текущий UI и перестраивает его в масштабе `new_scale`.

        Args:
            new_scale: Target scale factor. If None, auto-detect via _detect_ui_scale
                       and clear the saved `ui_scale` from config (so future launches
                       re-run detection). If a float, use it directly and persist it.
                       / Целевой масштаб. Если None — авто-детект через
                       _detect_ui_scale и очистка сохранённого `ui_scale` (чтобы
                       при следующих запусках детект выполнялся заново). Если число —
                       использовать напрямую и сохранить.
        """
        # 1. Save state that lives in widgets which are about to be destroyed.
        # / Сохраняем состояние, живущее в виджетах, которые сейчас будут удалены.
        saved_monitor = self.current_monitor
        saved_right_panel = self.right_panel_visible
        saved_rgb = RGB(
            r=self.r_val.get() if hasattr(self, "r_val") else 1.0,
            g=self.g_val.get() if hasattr(self, "g_val") else 1.0,
            b=self.b_val.get() if hasattr(self, "b_val") else 1.0,
        )
        saved_search = (
            self.search_var.get() if hasattr(self, "search_var") else ""
        )
        # If the search field currently shows the placeholder, treat it as empty.
        # / Если в поле поиска сейчас плейсхолдер — считаем пустым.
        if saved_search == tr("search_placeholder"):
            saved_search = ""

        # 2. Save current geometry to config BEFORE rebuild so _calculate_window_geometry
        # can clamp to the same monitor / use the same saved position.
        # / Сохраняем текущую геометрию в конфиг ДО перестройки, чтобы
        # _calculate_window_geometry мог ограничить по тому же монитору / позиции.
        try:
            self.config.ui.window_geometry = self.root.geometry()
        except Exception as e:
            logger.debug("Could not capture window geometry before rebuild: %s", e)

        # 3. Determine factor: explicit new_scale, or auto-detect.
        # / Определяем factor: явный new_scale или авто-детект.
        if new_scale is not None:
            factor = new_scale
        else:
            _font_scale, layout_scale, _src = self._detect_ui_scale()
            factor = layout_scale

        # 4. Apply the scale (idempotent via _BASE_SCALE_CONSTANTS).
        # / Применяем масштаб (идемпотентно через _BASE_SCALE_CONSTANTS).
        self._apply_ui_scale(factor)
        self.ui_scale = factor

        # 5. Persist the choice: `new_scale` (None means auto — drops the override
        # so the next launch re-runs detection).
        # / Сохраняем выбор: `new_scale` (None = авто — убираем override, чтобы
        # при следующем запуске детект выполнялся заново).
        try:
            self.config.ui.ui_scale = new_scale
            save_config(self.config)
        except Exception as e:
            logger.warning("Could not save ui_scale after rebuild: %s", e)

        # 6. Clean up any open context menu before destroying widgets.
        # / Закрываем открытое контекстное меню перед удалением виджетов.
        self._close_context_menu()

        # 7. Destroy all top-level widgets — start with a clean slate.
        # / Уничтожаем все виджеты верхнего уровня — начинаем с чистого листа.
        for child in self.root.winfo_children():
            try:
                child.destroy()
            except Exception as e:
                logger.debug("Could not destroy child during rebuild: %s", e)

        # 8. Re-setup the window (without re-running DPI detection — we already
        # applied the scale in step 4) and rebuild the interface.
        # / Заново настраиваем окно (без повторного DPI-детекта — масштаб уже
        # применён в шаге 4) и перестраиваем интерфейс.
        self._setup_window_no_scaling()
        self._build_interface()
        self._calculate_window_geometry()
        self._bind_events()
        self._show_window()

        # 9. Restore state into the freshly-built widgets.
        # / Восстанавливаем состояние в свежепостроенные виджеты.
        self.current_monitor = saved_monitor
        if hasattr(self, "monitor_var"):
            try:
                self.monitor_var.set(saved_monitor)
            except Exception as e:
                logger.debug("Could not restore monitor_var: %s", e)
        self.right_panel_visible = saved_right_panel
        try:
            self.apply_preset_values(saved_rgb)
        except Exception as e:
            logger.debug("Could not restore RGB values after rebuild: %s", e)
        if hasattr(self, "search_var") and saved_search:
            try:
                self.search_var.set(saved_search)
                # Restore the active-text color (focus_out would set placeholder color).
                # / Восстанавливаем цвет активного текста (focus_out выставил бы цвет плейсхолдера).
                if hasattr(self, "search_entry"):
                    self.search_entry.configure(foreground=self.colors.field_fg)
            except Exception as e:
                logger.debug("Could not restore search_var: %s", e)

    def _setup_window_no_scaling(self) -> None:
        """
        Same as _setup_window, but skips _setup_dpi_scaling() (the scale has
        already been applied by the caller) and forces resizable(False, False)
        so the user can't drag-resize the rebuilt window.
        / То же, что _setup_window, но пропускает _setup_dpi_scaling()
        (масштаб уже применён вызывающим кодом) и фиксирует resizable(False, False),
        чтобы пользователь не мог менять размер окна перетаскиванием.
        """
        self.root.withdraw()
        # NOTE: deliberately NOT calling self._setup_dpi_scaling() here —
        # the caller (_rebuild_ui_with_scale) has already applied the new factor.
        # / Намеренно НЕ вызываем self._setup_dpi_scaling() здесь —
        # вызывающий (_rebuild_ui_with_scale) уже применил новый factor.
        self.root.option_add("*relief", "flat")
        self.root.option_add("*borderWidth", "0")
        self.root.option_add("*highlightThickness", "0")
        self.root.option_add("*Background", self.colors.bg)
        self.root.option_add("*Foreground", self.colors.fg)
        self.root.option_add("*Labelframe*font", FONT_LIBRARY_HEADER)
        self.root.option_add("*Labelframe*foreground", self.colors.fg)
        self.root.configure(bg=self.colors.bg)
        self.root.title(tr("window_title", APP_VERSION))

        icon_path = os.path.join(SCRIPT_DIR, ICON_FILENAME)
        if not os.path.exists(icon_path):
            icon_path = create_default_icon()
        if icon_path and os.path.exists(icon_path):
            try:
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
                self.root.icon = icon
            except Exception as e:
                logger.warning("Failed to load icon: %s", e)

        self.root.resizable(False, False)
        min_total_width = CONTENT_FIXED_WIDTH + STRIP_WIDTH + MIN_LIBRARY_WIDTH
        self.root.minsize(min_total_width, 0)

    def _close_context_menu(self) -> None:
        """
        Destroy any currently-open context menu and reset the reference.
        Уничтожает открытое контекстное меню и сбрасывает ссылку на него.
        """
        if hasattr(self, "current_menu") and self.current_menu:
            try:
                self.current_menu.destroy()
            except Exception:
                pass
            self.current_menu = None

    def _hotkey_save(self) -> None:
        """Ctrl+S handler — save current as new preset (skip if a dialog is open).
        / Ctrl+S — сохранить как новый пресет (пропуск если открыт диалог).

        Only skips when a Toplevel dialog (edit/save) is open — NOT when the search
        entry has focus. The search entry doesn't need Ctrl+S, so it's safe to
        intercept. / Пропускает только при открытом Toplevel-диалоге (редактирование/
        сохранение) — НЕ при фокусе в строке поиска. Поиску Ctrl+S не нужен, поэтому
        перехватывать безопасно.
        """
        if self._is_dialog_open():
            return
        self.save_current_as_new()

    def _is_dialog_open(self) -> bool:
        """Check if a Toplevel dialog is currently open.
        Проверяет, открыт ли сейчас диалог Toplevel."""
        try:
            for w in self.root.winfo_children():
                if isinstance(w, tk.Toplevel) and w.winfo_exists():
                    return True
        except Exception:
            pass
        return False

    def _hotkey_focus_search(self) -> None:
        """Ctrl+F handler — focus the search entry."""
        self.search_entry.focus_set()
        # Select all text for easy replacement / выделяем весь текст
        self.search_entry.select_range(0, tk.END)

    def _hotkey_slot(self, slot_index: int) -> None:
        """Digit 1-5 handler — activate favorite slot (skip if a dialog is open).
        / 1-5 — активировать слот избранного (пропуск если открыт диалог).

        Only skips when a Toplevel dialog is open — NOT when the search entry has
        focus. Activating a slot while typing in search is useful and harmless.
        / Пропускает только при открытом Toplevel-диалоге — НЕ при фокусе в строке
        поиска. Активация слота во время ввода в поиск полезна и безобидна.
        """
        if self._is_dialog_open():
            return
        self.activate_favorite_slot(slot_index)

    def _hotkey_escape(self) -> None:
        """Escape handler — close the main window (and any open tooltip).
        / Обработчик Escape — закрыть главное окно (и скрыть tooltip).

        If a Toplevel dialog (edit/save preset) is open, do NOT close the main
        window — the dialog's own <Escape> binding handles closing it.
        / Если открыто диалоговое окно Toplevel (редактирование/сохранение пресета),
        НЕ закрываем главное окно — собственная привязка <Escape> диалога закроет его.
        """
        if self._is_dialog_open():
            return  # Dialog is open — let it handle Escape.
            # / Диалог открыт — пусть он обрабатывает Escape.
        self._hide_tooltip()
        self.on_closing()

    def _calculate_content_height(self) -> int:
        """
        Calculate minimum content height by measuring the real built content panel.
        Вычисляет минимальную высоту контента, измеряя реально построенную панель контента.

        H8: previously this method created a temporary tk.Frame(None) and duplicated all
        widgets to measure required height. Now the UI is built before this is called,
        so we measure self.inner_content directly.
        / H8: ранее этот метод создавал временный tk.Frame(None) и дублировал все виджеты
        для измерения требуемой высоты. Теперь UI строится до вызова, поэтому измеряем
        self.inner_content напрямую.

        Returns / Возвращает:
            int: Required height in pixels / Требуемая высота в пикселях
        """
        self.root.update_idletasks()
        return self.inner_content.winfo_reqheight()

    def _detect_monitor_at_x(self, x: int) -> str | None:
        """
        Determine which monitor contains the given X coordinate, by name.
        Определяет, какому монитору принадлежит X-координата (по имени).

        Runs `xrandr --query` and finds the monitor whose horizontal bounding box
        contains `x`. Returns the monitor name (e.g. "eDP") or None on failure.
        / Запускает `xrandr --query` и находит монитор, в горизонтальный bounding box
        которого попадает `x`. Возвращает имя монитора (напр. "eDP") или None.
        """
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=3
            )
            if result.returncode != 0:
                return None
            for line in result.stdout.splitlines():
                if " connected " not in line:
                    continue
                name = line.split()[0]
                match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                if not match:
                    continue
                mon_w = int(match.group(1))
                mon_x = int(match.group(3))
                if mon_x <= x < mon_x + mon_w:
                    return name
        except Exception:
            pass
        return None

    def _get_monitor_geometry(self, monitor_name: str | None = None) -> tuple[int, int, int, int]:
        """
        Get geometry of a specific monitor by name, or primary if name is None.
        Получает геометрию конкретного монитора по имени, или primary если None.

        Args:
            monitor_name: Monitor name (e.g. "eDP", "HDMI-A-0"). If None or not
                          found, falls back to primary, then first connected.
                          / Имя монитора. Если None или не найден — primary,
                          затем первый подключенный.

        Returns / Возвращает:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=3, check=True
            )
            output = result.stdout
            primary_line = None
            first_connected = None
            target_line = None
            for line in output.splitlines():
                if " connected " in line:
                    name = line.split()[0]
                    if monitor_name and name == monitor_name:
                        target_line = line
                        break
                    if " primary" in line and primary_line is None:
                        primary_line = line
                    if first_connected is None:
                        first_connected = line
            chosen = target_line or primary_line or first_connected
            if not chosen:
                logger.warning("No connected monitors found, using fallback resolution")
                return DEFAULT_FALLBACK_RESOLUTION
            match = re.search(XRANDR_GEOMETRY_PATTERN, chosen)
            if match:
                return (
                    int(match.group(3)),
                    int(match.group(4)),
                    int(match.group(1)),
                    int(match.group(2)),
                )
        except FileNotFoundError:
            logger.warning("xrandr not found, using screen geometry for monitor detection")
        except subprocess.TimeoutExpired:
            logger.warning("xrandr --query timed out, using screen geometry for monitor detection")
        except subprocess.CalledProcessError as e:
            logger.warning(
                "xrandr --query failed (rc=%s): %s", e.returncode, (e.stderr or "").strip()
            )
        except Exception as e:
            logger.warning("Failed to get monitor geometry: %s", e)
        return (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())

    def _get_active_monitor_geometry(self) -> tuple[int, int, int, int]:
        """
        Get geometry of primary or first connected monitor (legacy, kept for compat).
        Получить геометрию основного или первого подключенного монитора.

        Returns / Возвращает:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        try:
            result = subprocess.run(
                ["xrandr", "--query"], capture_output=True, text=True, timeout=3, check=True
            )
            output = result.stdout
            lines = output.splitlines()
            primary_line = None
            first_connected = None
            for line in lines:
                if " connected " in line and " primary" in line:
                    primary_line = line
                    break
                elif " connected " in line and first_connected is None:
                    first_connected = line
            target_line = primary_line or first_connected
            if not target_line:
                logger.warning("No connected monitors found, using fallback resolution")
                return DEFAULT_FALLBACK_RESOLUTION
            match = re.search(XRANDR_GEOMETRY_PATTERN, target_line)
            if match:
                return (
                    int(match.group(3)),
                    int(match.group(4)),
                    int(match.group(1)),
                    int(match.group(2)),
                )
        except FileNotFoundError:
            logger.warning("xrandr not found, using screen geometry for monitor detection")
        except subprocess.TimeoutExpired:
            logger.warning("xrandr --query timed out, using screen geometry for monitor detection")
        except subprocess.CalledProcessError as e:
            logger.warning(
                "xrandr --query failed (rc=%s): %s", e.returncode, (e.stderr or "").strip()
            )
        except Exception as e:
            logger.warning("Failed to get monitor geometry: %s", e)
        return (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())

    def _get_file_path(self, mode: str = "save") -> str | None:
        """
        Get file path using zenity (follows system theme).
        Получить путь к файлу через zenity.

        Args:
            mode (str): "save" or "open" / "save" или "open"

        Returns / Возвращает:
            Optional[str]: Selected file path or None / Выбранный путь или None
        """
        if not self.use_zenity:
            return None

        try:
            if mode == "save":
                result = subprocess.run(
                    [
                        "zenity",
                        "--file-selection",
                        "--save",
                        "--confirm-overwrite",
                        f"--filename={EXPORT_DEFAULT_FILENAME}",
                        "--file-filter=JSON files *.json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=ZENITY_TIMEOUT,
                )
            else:
                result = subprocess.run(
                    [
                        "zenity",
                        "--file-selection",
                        "--file-filter=JSON files *.json",
                        "--file-filter=All files *",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=ZENITY_TIMEOUT,
                )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.warning("Zenity failed: %s, falling back to tkinter", e)
            return None

    def _pick_file(self, mode: str) -> str | None:
        """
        Pick a file path using zenity if available, otherwise fall back to tkinter filedialog.
        Выбирает путь к файлу через zenity если доступен, иначе через tkinter filedialog.

        Args:
            mode (str): "save" or "open" / "save" или "open"

        Returns / Возвращает:
            Optional[str]: Selected file path or None / Выбранный путь или None
        """
        # Try zenity first (follows system theme) / Сначала пробуем zenity (системная тема)
        if self.use_zenity:
            path = self._get_file_path(mode=mode)
            if path:
                return path
        # Fallback to tkinter filedialog / Запасной вариант — tkinter filedialog
        if mode == "save":
            return filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export presets",
                initialfile=EXPORT_DEFAULT_FILENAME,
            )
        return filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import preset library",
        )

    def _on_search_focus_in(self) -> None:
        """Clear search placeholder / Очистить placeholder поиска."""
        if self.search_entry.get() == tr("search_placeholder"):
            self.search_entry.delete(0, tk.END)
            self.search_entry.configure(foreground=self.colors.field_fg)

    def _on_search_focus_out(self) -> None:
        """Restore search placeholder / Восстановить placeholder поиска."""
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, tr("search_placeholder"))
            self.search_entry.configure(foreground=self.colors.field_placeholder_fg)

    def draw_toggle_arrow(self, is_visible: bool) -> None:
        """
        Draw toggle arrow.
        Нарисовать стрелку переключения.

        Args:
            is_visible (bool): Whether library panel is visible / Видима ли панель
        """
        self.toggle_strip.delete("all")
        w, h = STRIP_WIDTH, self.toggle_strip.winfo_height()
        if h < TOGGLE_ARROW_MIN_HEIGHT:
            h = TOGGLE_ARROW_FALLBACK_HEIGHT
        mid_y = h // 2

        if is_visible:
            points = [
                (ARROW_RIGHT_X_BASE + dx, mid_y + dy)
                for dx, dy in zip(ARROW_RIGHT_X_OFFSETS, ARROW_RIGHT_Y_OFFSETS)
            ]
            self.toggle_strip.create_polygon(points, fill=self.colors.toggle_arrow_color)
        else:
            points = [
                (ARROW_LEFT_X_BASE + dx, mid_y + dy)
                for dx, dy in zip(ARROW_LEFT_X_OFFSETS, ARROW_LEFT_Y_OFFSETS)
            ]
            self.toggle_strip.create_polygon(points, fill=self.colors.toggle_arrow_color)

    def draw_color_strip(self) -> None:
        """Draw color gradient strip / Нарисовать цветную полоску-градиент."""
        self.color_canvas.delete("all")
        self.color_canvas.update_idletasks()
        width = self.color_canvas.winfo_width()
        if width < CANVAS_MIN_WIDTH:
            width = CONTENT_FIXED_WIDTH - CANVAS_WIDTH_MARGIN
        height = CANVAS_HEIGHT

        # Создаём PhotoImage для градиента / Create PhotoImage for gradient
        gradient = tk.PhotoImage(width=width, height=height)

        # Генерируем градиент / Generate gradient
        segment = width / (len(GRADIENT_COLORS) - 1)
        for x in range(width):
            pos = x / segment
            idx = int(pos)
            t = pos - idx
            if idx >= len(GRADIENT_COLORS) - 1:
                idx = len(GRADIENT_COLORS) - 2
                t = 1.0
            c1, c2 = GRADIENT_COLORS[idx], GRADIENT_COLORS[idx + 1]
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r, g, b = int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            # Устанавливаем цвет для всей колонки / Set color for entire column
            gradient.put(color, to=(x, 0, x + 1, height))

        # Отображаем изображение / Display image
        self.color_canvas.create_image(0, 0, anchor=tk.NW, image=gradient)
        self.color_canvas.image = gradient  # Сохраняем ссылку / Keep reference

    def show_message(
        self, title: str, message: str, msg_type: MessageType = MessageType.INFO
    ) -> None:
        """
        Show themed message dialog.
        Показать тематизированное окно сообщения.

        Args:
            title (str): Dialog title / Заголовок диалога
            message (str): Message text / Текст сообщения
            msg_type (MessageType): Message type / Тип сообщения
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.colors.bg)

        icon = MESSAGE_ICONS.get(msg_type, MESSAGE_ICON_DEFAULT)

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (MESSAGE_DIALOG_WIDTH // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (MESSAGE_DIALOG_HEIGHT // 2)
        dialog.geometry(f"{MESSAGE_DIALOG_WIDTH}x{MESSAGE_DIALOG_HEIGHT}+{x}+{y}")

        msg_frame = tk.Frame(dialog, bg=self.colors.bg)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=MESSAGE_FRAME_PADX, pady=MESSAGE_FRAME_PADY)

        icon_label = tk.Label(
            msg_frame, text=icon, font=FONT_MESSAGE_ICON, bg=self.colors.bg, fg=self.colors.fg
        )
        icon_label.pack(side=tk.LEFT, padx=MESSAGE_ICON_PADX)

        msg_label = tk.Label(
            msg_frame,
            text=message,
            font=FONT_DIALOG,
            bg=self.colors.bg,
            fg=self.colors.fg,
            justify=tk.LEFT,
            wraplength=MESSAGE_TEXT_WRAPLENGTH,
        )
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )
        ok_btn = tk.Button(
            dialog,
            text="OK",
            font=FONT_DIALOG,
            command=dialog.destroy,
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
            padx=MESSAGE_BUTTON_PADX,
            pady=MESSAGE_BUTTON_INNER_PADY,
        )
        ok_btn.pack(pady=MESSAGE_BUTTON_PADY)
        ok_btn.focus_set()

        dialog.bind(MESSAGE_RETURN_BIND, lambda e: dialog.destroy())
        dialog.bind(MESSAGE_ESCAPE_BIND, lambda e: dialog.destroy())

    def on_window_resize(self, event: tk.Event) -> None:
        """
        Handle window resize.
        Обработать изменение размера окна.

        Args:
            event: Tkinter configure event / Событие configure Tkinter
        """
        if event.widget != self.root:
            return
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(RESIZE_DEBOUNCE_MS, self.draw_color_strip)

    def _build_display_name(
        self, preset: Preset, is_active: bool, is_fav: bool
    ) -> tuple[str, tuple[str, ...]]:
        """
        Build a display name and tags tuple for a preset based on active/favorite state.
        Строит отображаемое имя и кортеж тегов для пресета по его активному/избранному состоянию.

        Args:
            preset (Preset): Preset / Пресет
            is_active (bool): Whether the preset matches the current RGB / Совпадает ли с текущим RGB
            is_fav (bool): Whether the preset is in favorites / Находится ли в избранном

        Returns / Возвращает:
            Tuple[str, Tuple[str, ...]]: (display_name, tags) / (имя, теги)
        """
        r, g, b = preset.rgb.r, preset.rgb.g, preset.rgb.b
        base_name = PRESET_DISPLAY_FORMAT.format(id=preset.id, name=preset.name, r=r, g=g, b=b)
        if is_active and is_fav:
            return f"{MARKER_ACTIVE_PREFIX}{MARKER_FAVORITE_PREFIX}{base_name}", (
                "fav",
                "active_text",
            )
        if is_active:
            return f"{MARKER_ACTIVE_PREFIX}{base_name}", ("active_text",)
        if is_fav:
            return f"{MARKER_FAVORITE_PREFIX}{base_name}", ("fav",)
        return base_name, ()

    def update_ui_from_config(self) -> None:
        """Update UI from config / Обновить UI из конфига."""
        for item in self.preset_tree.get_children():
            self.preset_tree.delete(item)
        self.all_presets = []
        # M2: rebuild dict by id / перестраиваем словарь по id
        self.all_presets_by_id = {}
        # M5: invalidate presets cache / инвалидируем кэш пресетов
        self._presets_cache = None
        favorites_ids = self.config.favorites
        presets = self.config.get_presets()

        for p in presets:
            is_fav = p.id in favorites_ids
            # Initial tree uses inactive state (active markers applied in update_active_indicator)
            # Исходное дерево использует неактивное состояние (активные маркеры применяются в update_active_indicator)
            display_name, tags = self._build_display_name(p, is_active=False, is_fav=is_fav)
            item_id = self.preset_tree.insert(
                "", "end", iid=str(p.id), text=display_name, tags=tags
            )
            entry = {
                "id": item_id,
                "text": display_name.lower(),
                "tags": tags,
                "comment": p.comment,
            }
            self.all_presets.append(entry)
            self.all_presets_by_id[item_id] = entry

        self.preset_tree.tag_configure("fav", font=(FONT_TREEVIEW[0], FONT_TREEVIEW[1], "bold"))
        self.preset_tree.tag_configure("active_text", foreground=COLOR_ACTIVE_BORDER)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        for i in range(MAX_FAVORITES):
            btn = self.fav_buttons[i]
            if i < len(favorites_ids) and favorites_ids[i] is not None:
                pid = favorites_ids[i]
                preset = get_preset_by_id(presets, pid)
                if preset:
                    preset_color = preset.rgb.to_hex()
                    brightness = preset.rgb.brightness()
                    text_color = (
                        COLOR_TEXT_WHITE
                        if brightness < COLOR_BRIGHTNESS_THRESHOLD
                        else COLOR_TEXT_BLACK
                    )

                    hover_factor = HOVER_FACTOR_DARK if self.colors.is_dark else HOVER_FACTOR_LIGHT
                    hover_r = max(0, min(1, preset.rgb.r * hover_factor))
                    hover_g = max(0, min(1, preset.rgb.g * hover_factor))
                    hover_b = max(0, min(1, preset.rgb.b * hover_factor))
                    hover_color = f"#{int(hover_r * 255):02x}{int(hover_g * 255):02x}{int(hover_b * 255):02x}"

                    btn.config(
                        text=tr("inactive_preset", preset.id, preset.name),
                        state=tk.NORMAL,
                        fg=text_color,
                        bg=preset_color,
                        activebackground=hover_color,
                        activeforeground=text_color,
                        relief="solid",
                        bd=FAV_BUTTON_BORDER_THICKNESS,
                        highlightthickness=FAV_BUTTON_INACTIVE_HIGHLIGHT,
                        highlightbackground=inactive_border,
                        highlightcolor=inactive_border,
                        font=FONT_FAVORITE,
                    )
                else:
                    btn.config(
                        text=tr("error_id"),
                        state=tk.DISABLED,
                        fg=COLOR_TEXT_GRAY,
                        bg=self.colors.empty_slot_bg,
                        relief="solid",
                        bd=FAV_BUTTON_BORDER_THICKNESS,
                        highlightthickness=0,
                    )
            else:
                btn.config(
                    text=tr("empty_slot"),
                    state=tk.DISABLED,
                    fg=COLOR_TEXT_GRAY,
                    bg=self.colors.empty_slot_bg,
                    relief="solid",
                    bd=FAV_BUTTON_BORDER_THICKNESS,
                    highlightthickness=0,
                )

        self.update_active_indicator()
        self._setup_treeview_tooltip()

    def _setup_treeview_tooltip(self) -> None:
        """Setup tooltip event bindings for treeview / Настроить bindings подсказок."""
        self.preset_tree.bind(DIALOG_MOTION_BIND, self._on_tree_motion, add="+")
        self.preset_tree.bind(DIALOG_LEAVE_BIND, self._hide_tooltip, add="+")
        self.preset_tree.bind(DIALOG_LEFT_CLICK_BIND, self._hide_tooltip, add="+")

    def _on_tree_motion(self, event: tk.Event) -> None:
        """
        Handle mouse motion over treeview.
        Обработать движение мыши над treeview.

        Args:
            event: Tkinter motion event / Событие motion Tkinter
        """
        item = self.preset_tree.identify_row(event.y)

        if item == self.tooltip_current_item and self.tooltip_window:
            return

        if self.tooltip_timer:
            self.root.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None

        self._hide_tooltip()

        if not item:
            self.tooltip_current_item = None
            return

        self.tooltip_current_item = item

        # M2: O(1) lookup via dict instead of linear scan / O(1) поиск через словарь вместо линейного
        preset_data = self.all_presets_by_id.get(item)

        if preset_data and preset_data.get("comment"):
            self.tooltip_timer = self.root.after(
                TOOLTIP_DELAY_MS, lambda: self._show_tooltip(event, preset_data["comment"])
            )

    def _show_tooltip(self, event: tk.Event, text: str) -> None:
        """
        Show tooltip window.
        Показать окно подсказки.

        Args:
            event: Tkinter event / Событие Tkinter
            text (str): Tooltip text / Текст подсказки
        """
        self._hide_tooltip()

        x = event.x_root + TOOLTIP_OFFSET_X
        y = event.y_root + TOOLTIP_OFFSET_Y

        self.tooltip_window = tw = tk.Toplevel(self.root)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background=TOOLTIP_BG,
            foreground=TOOLTIP_FG,
            relief=tk.SOLID,
            borderwidth=1,
            font=FONT_TOOLTIP,
            wraplength=TOOLTIP_MAX_WIDTH,
            padx=TOOLTIP_PADDING,
            pady=TOOLTIP_PADDING,
        )
        label.pack()

    def _hide_tooltip(self, event: tk.Event | None = None) -> None:
        """
        Hide tooltip window.
        Скрыть окно подсказки.

        Args:
            event: Optional Tkinter event / Опциональное событие Tkinter
        """
        if self.tooltip_timer:
            self.root.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None

        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None

        self.tooltip_current_item = None

    def update_active_indicator(self) -> None:
        """Update active preset indicator / Обновить индикатор активного пресета."""
        current_rgb = RGB(
            r=round(self.r_val.get(), 2),
            g=round(self.g_val.get(), 2),
            b=round(self.b_val.get(), 2),
        )
        favorites_ids = self.config.favorites
        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        # M5: use cached presets list, rebuild only when invalidated / используем кэш пресетов
        if self._presets_cache is None:
            self._presets_cache = self.config.get_presets()
        presets = self._presets_cache

        for i in range(MAX_FAVORITES):
            btn = self.fav_buttons[i]
            if btn["state"] == tk.DISABLED:
                continue
            if i < len(favorites_ids) and favorites_ids[i] is not None:
                pid = favorites_ids[i]
                preset = get_preset_by_id(presets, pid)
                if preset:
                    # C5: use _rgb_match helper / используем _rgb_match
                    is_active = _rgb_match(preset.rgb, current_rgb)

                    if is_active:
                        base_text = tr("inactive_preset", preset.id, preset.name)
                        btn.config(
                            relief="flat",
                            bd=0,
                            highlightthickness=FAV_BUTTON_ACTIVE_HIGHLIGHT,
                            highlightbackground=COLOR_ACTIVE_BORDER,
                            highlightcolor=COLOR_ACTIVE_BORDER,
                            text=f"{MARKER_ACTIVE_PREFIX}{base_text}{MARKER_ACTIVE_SUFFIX}",
                        )
                    else:
                        btn.config(
                            relief="solid",
                            bd=FAV_BUTTON_BORDER_THICKNESS,
                            highlightthickness=FAV_BUTTON_INACTIVE_HIGHLIGHT,
                            highlightbackground=inactive_border,
                            highlightcolor=inactive_border,
                            text=tr("inactive_preset", preset.id, preset.name),
                        )

        for p in presets:
            item_id = str(p.id)
            # C5: use _rgb_match helper / используем _rgb_match
            is_active = _rgb_match(p.rgb, current_rgb)
            is_fav = p.id in favorites_ids
            # H4: use _build_display_name helper / используем _build_display_name
            display_name, tags = self._build_display_name(p, is_active=is_active, is_fav=is_fav)
            self.preset_tree.item(item_id, text=display_name, tags=tags)

    def _filter_presets(self) -> None:
        """Filter presets by search / Фильтровать пресеты по поиску."""
        query = self.search_var.get().strip().lower()
        if query == tr("search_placeholder").lower():
            query = ""
        for item in self.preset_tree.get_children():
            self.preset_tree.detach(item)
        for preset in self.all_presets:
            if not query or query in preset["text"]:
                self.preset_tree.reattach(preset["id"], "", "end")

    def toggle_right_panel(self, event: tk.Event | None = None) -> None:
        """
        Toggle right panel.
        Переключить правую панель.

        Args:
            event: Optional Tkinter event / Опциональное событие Tkinter
        """
        self.right_panel_visible = not self.right_panel_visible
        logger.debug("Preset panel visibility: %s", self.right_panel_visible)
        current_h = self.root.winfo_height()
        if self.right_panel_visible:
            self.paned.add(self.library_frame, after=self.toggle_strip)
            self.paned.sash_place(1, CONTENT_FIXED_WIDTH + STRIP_WIDTH, 0)
            self.draw_toggle_arrow(True)
            new_w = CONTENT_FIXED_WIDTH + STRIP_WIDTH + LIBRARY_WIDTH
            self.root.minsize(CONTENT_FIXED_WIDTH + STRIP_WIDTH + MIN_LIBRARY_WIDTH, 0)
            self.root.maxsize(new_w, current_h)
        else:
            self._hide_library_no_resize()
            new_w = CONTENT_FIXED_WIDTH + STRIP_WIDTH
            self.root.minsize(CONTENT_FIXED_WIDTH + STRIP_WIDTH, 0)
            self.root.maxsize(new_w, current_h)
        # Only change width, keep height. Do NOT pass position — let the WM keep
        # the top-left corner in place on its own. Passing +x+y along with
        # minsize changes causes many WMs to reposition the window.
        # / Меняем только ширину, высота прежняя. НЕ передаём позицию — пусть WM
        # сам держит верхний левый угол. Передача +x+y вместе с minsize заставляет
        # многие WM сдвигать окно.
        self.root.geometry(f"{new_w}x{current_h}")
        self.config.ui.right_panel_visible = self.right_panel_visible

    def _apply_window_size(self, new_w: int, new_h: int) -> None:
        """
        Apply a new window size while preserving the current top-left position.
        Применяет новый размер окна, сохраняя текущую позицию (верхний левый угол).

        Also re-locks both `minsize` and `maxsize` to (new_w, new_h) so the
        fixed-size invariant (Variant 4) keeps holding after the resize —
        otherwise the user could drag-resize the window once the programmatic
        geometry call completes.
        / Также перефиксирует `minsize` и `maxsize` в (new_w, new_h), чтобы
        инвариант фиксированного размера (Variant 4) продолжал выполняться после
        изменения размера — иначе пользователь смог бы менять размер окна
        перетаскиванием после программного вызова geometry.

        Args:
            new_w: New window width in pixels / Новая ширина окна в пикселях
            new_h: New window height in pixels / Новая высота окна в пикселях
        """
        try:
            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
        except Exception:
            cur_x = cur_y = 0
        # Clamp width/height to >= 1 to avoid TclError on zero-size requests.
        # / Ограничиваем ширину/высоту >= 1, чтобы избежать TclError при нулевых размерах.
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        self.root.minsize(new_w, new_h)
        self.root.maxsize(new_w, new_h)
        self.root.geometry(f"{new_w}x{new_h}+{cur_x}+{cur_y}")

    def _hide_library_no_resize(self) -> None:
        """Hide presets panel without resize / Скрыть панель пресетов без изменения размера."""
        self.paned.forget(self.library_frame)
        self.draw_toggle_arrow(False)

    def load_monitor_gamma(self) -> None:
        """Load monitor gamma / Загрузить гамму монитора."""
        monitor_gammas = self.config.system.monitor_gammas
        if self.current_monitor in monitor_gammas:
            rgb_list = monitor_gammas[self.current_monitor]
            rgb = RGB.from_list(rgb_list)
            logger.info(
                "Loaded gamma for %s: R=%.2f G=%.2f B=%.2f",
                self.current_monitor,
                rgb.r,
                rgb.g,
                rgb.b,
            )
            self.apply_preset_values(rgb)
        else:
            # При первом запуске или отсутствии сохранённой гаммы — нейтральный белый
            # At first launch or no saved gamma — neutral white
            rgb = RGB(r=1.0, g=1.0, b=1.0)
            logger.info("No saved gamma for %s, using neutral white", self.current_monitor)
            self.apply_preset_values(rgb)

    def save_monitor_gamma(self, rgb: RGB) -> None:
        """
        Save monitor gamma. / Сохранить гамму монитора.

        Args:
            rgb (RGB): RGB values / Значения RGB
        """
        self.config.system.monitor_gammas[self.current_monitor] = rgb.to_list()
        # last_rgb хранит только последнее значение для ТЕКУЩЕГО монитора
        # last_rgb stores only the last value for the CURRENT monitor
        self.config.system.last_rgb = rgb.to_list()
        logger.debug(
            "Saved gamma for %s: R=%.2f G=%.2f B=%.2f", self.current_monitor, rgb.r, rgb.g, rgb.b
        )

    def on_tree_double_click(self, event: tk.Event) -> None:
        """
        Apply preset on double-click. / Применить пресет по двойному клику.

        Args:
            event: Tkinter double-click event / Событие двойного клика Tkinter
        """
        selection = self.preset_tree.selection()
        if not selection:
            return
        pid = int(selection[0])
        preset = get_preset_by_id(self.config.get_presets(), pid)
        if preset:
            logger.info("Applied preset #%s '%s' via double-click", pid, preset.name)
            self.apply_preset_values(preset.rgb)

    def on_tree_right_click(self, event: tk.Event) -> None:
        """
        Show context menu.
        Показать контекстное меню.

        Args:
            event: Tkinter right-click event / Событие правого клика Tkinter
        """
        item = self.preset_tree.identify_row(event.y)
        if not item:
            return
        self.preset_tree.selection_set(item)
        pid = int(item)
        if hasattr(self, "current_menu") and self.current_menu:
            try:
                self.current_menu.destroy()
            except Exception:
                pass
            self.current_menu = None
        favorites = self.config.favorites
        has_free_slot = any(
            i >= len(favorites) or favorites[i] is None for i in range(MAX_FAVORITES)
        )

        # Border color: contrast with the menu background so the menu doesn't blend in.
        # In dark theme use a light border; in light theme use a dark border.
        # / Цвет рамки: контрастный с фоном меню, чтобы оно не сливалось.
        # В тёмной теме светлая рамка, в светлой — тёмная.
        menu_border_color = (
            COLOR_INACTIVE_BORDER_LIGHT if self.colors.is_dark else COLOR_INACTIVE_BORDER_DARK
        )
        # tk.Menu accepts `relief` and `borderwidth` (NOT `highlightthickness` /
        # `highlightbackground` — those are for other widgets and raise TclError).
        # `bordercolor` works on newer Tk; on older Tk it raises TclError (caught).
        # / tk.Menu принимает `relief` и `borderwidth` (НЕ `highlightthickness` /
        # `highlightbackground` — это для других виджетов, вызывают TclError).
        # `bordercolor` работает в новых Tk; в старых вызывает TclError (ловим).
        try:
            menu = tk.Menu(
                self.root,
                tearoff=0,
                bg=self.colors.bg,
                fg=self.colors.fg,
                activebackground=self.colors.select_bg,
                activeforeground=self.colors.select_fg,
                font=FONT_SEARCH,  # scaled font / масштабируемый шрифт
                relief="solid",  # visible border / видимая рамка
                borderwidth=1,
                # activeborderwidth: minimal inner padding (1). Higher values (4)
                # create a bulky 3D-button look that doesn't fit the flat design.
                # / activeborderwidth: минимальный внутренний отступ (1). Большие значения (4)
                # создают громоздкий 3D-кнопка вид, не вписывающийся в flat-дизайн.
                activeborderwidth=1,
            )
            # Try to set border color (supported on newer Tk versions only).
            # / Пытаемся задать цвет рамки (только в новых версиях Tk).
            try:
                menu.configure(bordercolor=menu_border_color)
            except tk.TclError:
                pass  # bordercolor not supported — border stays default / не поддерживается
        except tk.TclError:
            # Fallback: some Tk versions don't accept relief/borderwidth on Menu.
            # / Fallback: некоторые версии Tk не принимают relief/borderwidth на Menu.
            menu = tk.Menu(
                self.root,
                tearoff=0,
                bg=self.colors.bg,
                fg=self.colors.fg,
                activebackground=self.colors.select_bg,
                activeforeground=self.colors.select_fg,
                font=FONT_SEARCH,
                activeborderwidth=1,  # minimal inner padding / минимальный отступ
            )
        add_state = tk.NORMAL if has_free_slot else tk.DISABLED
        menu.add_command(
            label=tr("add_to_favorites"),
            command=lambda: self.add_to_favorites(pid),
            state=add_state,
        )
        menu.add_command(label=tr("edit"), command=lambda: self.edit_preset(pid))
        menu.add_separator()
        menu.add_command(label=tr("delete_preset"), command=lambda: self.delete_preset(pid))
        self.current_menu = menu
        menu.post(event.x_root, event.y_root)

        def close_menu(e: tk.Event) -> None:
            if hasattr(self, "current_menu") and self.current_menu:
                try:
                    self.current_menu.destroy()
                except Exception:
                    pass
                self.current_menu = None

        self.root.bind(DIALOG_LEFT_CLICK_BIND, close_menu, add="+")

    def add_to_favorites(self, pid: int) -> None:
        """
        Add to favorites.
        Добавить в избранное.

        Args:
            pid (int): Preset ID / ID пресета
        """
        favorites = self.config.favorites
        if pid in favorites:
            self.show_message(tr("info"), tr("already_in_favorites"), MessageType.INFO)
            return
        for i in range(MAX_FAVORITES):
            if i >= len(favorites) or favorites[i] is None:
                while len(favorites) <= i:
                    favorites.append(None)
                favorites[i] = pid
                preset = get_preset_by_id(self.config.get_presets(), pid)
                preset_name = preset.name if preset else str(pid)
                logger.info("Added preset #%s '%s' to favorites slot %s", pid, preset_name, i + 1)
                break
        self.config.favorites = favorites
        try:
            save_config(self.config)
        except ConfigSaveError as e:
            logger.error("Failed to save config after add_to_favorites: %s", e)
            self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
        self.update_ui_from_config()

    def _build_text_input_dialog(
        self,
        title: str,
        name_label_key: str,
        initial_name: str,
        initial_comment: str,
        on_save: callable,
        save_btn_initial_state: str = tk.NORMAL,
    ) -> tk.Toplevel:
        """
        Build a themed Toplevel dialog with a name Entry and a comment Text field.
        Строит тематизированный Toplevel-диалог с полем имени (Entry) и комментарием (Text).

        Args:
            title (str): Dialog title / Заголовок диалога
            name_label_key (str): Translation key for the name label / Ключ перевода для метки имени
            initial_name (str): Initial name value / Начальное значение имени
            initial_comment (str): Initial comment value / Начальное значение комментария
            on_save (callable): Callback invoked with (name_entry, comment_text, dialog) when Save is pressed /
                                Колбэк, вызываемый с (name_entry, comment_text, dialog) при нажатии Сохранить
            save_btn_initial_state (str): Initial state of the Save button (NORMAL/DISABLED) /
                                          Начальное состояние кнопки Сохранить (NORMAL/DISABLED)

        Returns / Возвращает:
            tk.Toplevel: The created dialog window (caller owns lifecycle) /
                        Созданное окно диалога (жизненным циклом управляет вызывающий)
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_set()
        dialog.configure(bg=self.colors.bg)
        dialog.resizable(False, False)
        # Width is fixed (DIALOG_WIDTH), height is auto-sized to content.
        # / Ширина фиксированная (DIALOG_WIDTH), высота — по содержимому.

        tk.Label(
            dialog, text=tr(name_label_key), font=FONT_DIALOG, bg=self.colors.bg, fg=self.colors.fg
        ).pack(pady=DIALOG_LABEL_PADY)
        name_entry = tk.Entry(
            dialog,
            font=FONT_DIALOG,
            bg=DIALOG_FIELD_BG,
            fg=DIALOG_FIELD_FG,
            insertbackground=DIALOG_FIELD_CURSOR,
            relief="solid",
            bd=1,
        )
        name_entry.insert(0, initial_name)
        name_entry.pack(pady=DIALOG_ENTRY_PADY, padx=COMMENT_TEXT_PADX, fill=tk.X)
        name_entry.focus_set()
        if initial_name:
            name_entry.select_range(0, tk.END)

        tk.Label(
            dialog,
            text=tr("new_comment_label"),
            font=FONT_DIALOG,
            bg=self.colors.bg,
            fg=self.colors.fg,
        ).pack(pady=(5, 2))
        comment_text = tk.Text(
            dialog,
            height=COMMENT_TEXT_HEIGHT,
            font=FONT_DIALOG,
            wrap=tk.WORD,
            bg=DIALOG_FIELD_BG,
            fg=DIALOG_FIELD_FG,
            insertbackground=DIALOG_FIELD_CURSOR,
            relief="solid",
            bd=1,
        )
        comment_text.pack(pady=2, padx=COMMENT_TEXT_PADX, fill=tk.X)
        comment_text.insert(TEXT_START_INDEX, initial_comment)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        save_btn = tk.Button(
            dialog,
            text=tr("save"),
            font=FONT_DIALOG,
            command=lambda: on_save(name_entry, comment_text, dialog),
            state=save_btn_initial_state,
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
            padx=MESSAGE_BUTTON_PADX,
            pady=MESSAGE_BUTTON_INNER_PADY,
        )
        save_btn.pack(pady=DIALOG_BUTTON_PADY)

        def validate(*args) -> None:
            save_btn.config(state=tk.NORMAL if name_entry.get().strip() else tk.DISABLED)

        name_entry.bind(DIALOG_KEYRELEASE_BIND, validate)
        name_entry.bind(
            DIALOG_RETURN_BIND,
            lambda e: save_btn.invoke() if save_btn["state"] == tk.NORMAL else None,
        )
        # Close dialog on Escape.
        # / Закрытие диалога по Escape.
        dialog.bind(MESSAGE_ESCAPE_BIND, lambda e: dialog.destroy())
        dialog.after(DIALOG_VALIDATE_DELAY_MS, validate)

        # Auto-size: fixed width, height computed from content.
        # / Авто-размер: фиксированная ширина, высота по содержимому.
        dialog.update_idletasks()
        req_h = dialog.winfo_reqheight()
        req_w = DIALOG_WIDTH
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - req_w // 2
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - req_h // 2
        dialog.geometry(f"{req_w}x{req_h}+{x}+{y}")
        dialog.minsize(req_w, req_h)

        return dialog

    def edit_preset(self, pid: int) -> None:
        """
        Open a combined edit dialog: name + comment + RGB values.
        Открыть объединённый диалог редактирования: имя + комментарий + RGB.

        Replaces the former rename_preset — a single form edits all preset fields,
        including the RGB values via ttk.Spinbox (0.00–1.00, step 0.01).
        / Заменяет прежний rename_preset — одна форма редактирует все поля пресета,
        включая значения RGB через ttk.Spinbox (0.00–1.00, шаг 0.01).

        Args:
            pid (int): Preset ID / ID пресета
        """
        preset = get_preset_by_id(self.config.get_presets(), pid)
        if not preset:
            return
        self._build_edit_dialog(
            title=tr("edit_title"),
            name_label_key="new_name_label",
            initial_name=preset.name,
            initial_comment=preset.comment,
            initial_rgb=preset.rgb,
            on_save=self._make_edit_save_callback(preset),
        )

    def _build_edit_dialog(
        self,
        title: str,
        name_label_key: str,
        initial_name: str,
        initial_comment: str,
        initial_rgb: RGB,
        on_save: callable,
    ) -> tk.Toplevel:
        """
        Build a themed Toplevel dialog with name, comment, and 3 RGB spinboxes.
        Строит тематизированный Toplevel-диалог с именем, комментарием и 3 спинбоксами RGB.

        Args:
            title (str): Dialog title / Заголовок диалога
            name_label_key (str): Translation key for the name label / Ключ перевода для метки имени
            initial_name (str): Initial name value / Начальное значение имени
            initial_comment (str): Initial comment value / Начальное значение комментария
            initial_rgb (RGB): Initial RGB values / Начальные значения RGB
            on_save (callable): Callback invoked with (name_entry, comment_text, rgb_vars, dialog) /
                                Колбэк с (name_entry, comment_text, rgb_vars, dialog)

        Returns / Возвращает:
            tk.Toplevel: The created dialog window / Созданное окно диалога
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_set()
        dialog.configure(bg=self.colors.bg)
        dialog.resizable(False, False)
        # Width is fixed (DIALOG_WIDTH), height is auto-sized to content.
        # / Ширина фиксированная (DIALOG_WIDTH), высота — по содержимому.

        # Name field / Поле имени
        tk.Label(
            dialog, text=tr(name_label_key), font=FONT_DIALOG, bg=self.colors.bg, fg=self.colors.fg
        ).pack(pady=DIALOG_LABEL_PADY)
        name_entry = tk.Entry(
            dialog,
            font=FONT_DIALOG,
            bg=DIALOG_FIELD_BG,
            fg=DIALOG_FIELD_FG,
            insertbackground=DIALOG_FIELD_CURSOR,
            relief="solid",
            bd=1,
        )
        name_entry.insert(0, initial_name)
        name_entry.pack(pady=DIALOG_ENTRY_PADY, padx=COMMENT_TEXT_PADX, fill=tk.X)
        name_entry.focus_set()
        if initial_name:
            name_entry.select_range(0, tk.END)

        # Comment field / Поле комментария
        tk.Label(
            dialog,
            text=tr("new_comment_label"),
            font=FONT_DIALOG,
            bg=self.colors.bg,
            fg=self.colors.fg,
        ).pack(pady=(5, 2))
        comment_text = tk.Text(
            dialog,
            height=COMMENT_TEXT_HEIGHT,
            font=FONT_DIALOG,
            wrap=tk.WORD,
            bg=DIALOG_FIELD_BG,
            fg=DIALOG_FIELD_FG,
            insertbackground=DIALOG_FIELD_CURSOR,
            relief="solid",
            bd=1,
        )
        comment_text.pack(pady=2, padx=COMMENT_TEXT_PADX, fill=tk.X)
        comment_text.insert(TEXT_START_INDEX, initial_comment)

        # RGB spinboxes row / Ряд спинбоксов RGB
        tk.Label(
            dialog,
            text=tr("rgb_label"),
            font=FONT_DIALOG,
            bg=self.colors.bg,
            fg=self.colors.fg,
        ).pack(pady=(8, 2))
        rgb_frame = tk.Frame(dialog, bg=self.colors.bg)
        rgb_frame.pack(pady=2, padx=COMMENT_TEXT_PADX, fill=tk.X)
        r_var = tk.DoubleVar(value=round(initial_rgb.r, 2))
        g_var = tk.DoubleVar(value=round(initial_rgb.g, 2))
        b_var = tk.DoubleVar(value=round(initial_rgb.b, 2))
        rgb_vars = (r_var, g_var, b_var)
        channel_colors = (COLOR_CHANNEL_RED, COLOR_CHANNEL_GREEN, COLOR_CHANNEL_BLUE)
        channel_labels = ("R", "G", "B")
        for i, (var, color, label) in enumerate(zip(rgb_vars, channel_colors, channel_labels)):
            cell = tk.Frame(rgb_frame, bg=self.colors.bg)
            # Each cell takes 1/3 of the rgb_frame width — spinboxes scale with dialog.
            # / Каждая ячейка занимает 1/3 ширины rgb_frame — спинбоксы масштабируются с диалогом.
            cell.grid(row=0, column=i, padx=2, sticky="ew")
            rgb_frame.grid_columnconfigure(i, weight=1)
            # No separate Label — the spinbox fills the entire cell. The channel
            # letter (R/G/B) is shown as a colored prefix in the spinbox's
            # textvariable (e.g. "R: 1.00"). This avoids the Label taking space
            # and making the spinbox narrower than the Name field above.
            # / Без отдельного Label — спинбокс заполняет всю ячейку. Буква канала
            # (R/G/B) показывается как цветной префикс в textvariable спинбокса
            # (напр. "R: 1.00"). Это не даёт Label'у занимать место и делать
            # спинбокс у́же поля Название выше.
            tk.Label(
                cell, text=label, font=FONT_DIALOG, fg=color, bg=self.colors.bg
            ).pack(side=tk.LEFT, padx=(0, 2))
            sb = ttk.Spinbox(
                cell,
                from_=0.00,
                to=1.00,
                increment=SLIDER_STEP,
                format="%.2f",
                font=FONT_DIALOG,
                textvariable=var,
            )
            sb.pack(side=tk.LEFT, padx=0, fill=tk.X, expand=True)

        inactive_border = (
            COLOR_INACTIVE_BORDER_DARK if self.colors.is_dark else COLOR_INACTIVE_BORDER_LIGHT
        )

        save_btn = tk.Button(
            dialog,
            text=tr("save"),
            font=FONT_DIALOG,
            command=lambda: on_save(name_entry, comment_text, rgb_vars, dialog),
            bg=self.colors.bg,
            fg=self.colors.fg,
            activebackground=self.colors.select_bg,
            activeforeground=self.colors.select_fg,
            relief="flat",
            bd=0,
            highlightthickness=GENERAL_BUTTON_HIGHLIGHT,
            highlightbackground=inactive_border,
            padx=MESSAGE_BUTTON_PADX,
            pady=MESSAGE_BUTTON_INNER_PADY,
        )
        save_btn.pack(pady=DIALOG_BUTTON_PADY)

        def validate(*args) -> None:
            save_btn.config(state=tk.NORMAL if name_entry.get().strip() else tk.DISABLED)

        name_entry.bind(DIALOG_KEYRELEASE_BIND, validate)
        name_entry.bind(
            DIALOG_RETURN_BIND,
            lambda e: save_btn.invoke() if save_btn["state"] == tk.NORMAL else None,
        )
        # Close dialog on Escape.
        # / Закрытие диалога по Escape.
        dialog.bind(MESSAGE_ESCAPE_BIND, lambda e: dialog.destroy())
        dialog.after(DIALOG_VALIDATE_DELAY_MS, validate)

        # Auto-size the dialog: width is fixed (DIALOG_WIDTH), height is computed
        # from the content's required height. This replaces the old fixed geometry
        # that could clip spinboxes or leave excess space depending on UI scale.
        # / Авто-размер диалога: ширина фиксированная (DIALOG_WIDTH), высота
        # вычисляется по требуемой высоте содержимого. Заменяет старую фиксированную
        # геометрию, которая могла обрезать спинбоксы или оставлять лишнее место
        # в зависимости от UI scale.
        dialog.update_idletasks()
        req_h = dialog.winfo_reqheight()
        req_w = DIALOG_WIDTH
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - req_w // 2
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - req_h // 2
        dialog.geometry(f"{req_w}x{req_h}+{x}+{y}")
        dialog.minsize(req_w, req_h)

        return dialog

    def _make_edit_save_callback(self, preset: Preset):
        """Return an on_save callback bound to a specific preset. /
        Возвращает колбэк on_save, привязанный к конкретному пресету."""

        def on_save(
            name_entry: tk.Entry,
            comment_text: tk.Text,
            rgb_vars: tuple,
            dialog: tk.Toplevel,
        ) -> None:
            self._do_edit_preset(name_entry, comment_text, rgb_vars, preset, dialog)

        return on_save

    def _do_edit_preset(
        self,
        name_entry: tk.Entry,
        comment_text: tk.Text,
        rgb_vars: tuple,
        preset: Preset,
        dialog: tk.Toplevel,
    ) -> None:
        """
        Apply edited name, comment, and RGB values to the preset.
        Применяет отредактированные имя, комментарий и значения RGB к пресету.

        Args:
            name_entry: Name entry widget / Виджет ввода имени
            comment_text: Comment text widget / Виджет текста комментария
            rgb_vars: Tuple of (r_var, g_var, b_var) DoubleVars /
                      Кортеж (r_var, g_var, b_var) DoubleVar
            preset (Preset): Preset being edited / Редактируемый пресет
            dialog: Dialog window / Окно диалога
        """
        new_name = name_entry.get().strip()
        if not new_name:
            return
        # Clamp RGB values to [0.0, 1.0] and round to 2 decimals (matching slider resolution).
        # / Клампим RGB в [0.0, 1.0] и округляем до 2 знаков (как у слайдеров).
        r_val = max(0.0, min(1.0, round(float(rgb_vars[0].get()), 2)))
        g_val = max(0.0, min(1.0, round(float(rgb_vars[1].get()), 2)))
        b_val = max(0.0, min(1.0, round(float(rgb_vars[2].get()), 2)))
        new_rgb = RGB(r=r_val, g=g_val, b=b_val)

        old_name = preset.name
        rgb_changed = not _rgb_match(preset.rgb, new_rgb)
        preset.name = new_name
        preset.comment = comment_text.get(TEXT_START_INDEX, TEXT_END_INDEX).strip()
        preset.rgb = new_rgb

        # Update config / Обновляем конфиг
        presets = self.config.get_presets()
        for p in presets:
            if p.id == preset.id:
                p.name = preset.name
                p.comment = preset.comment
                p.rgb = preset.rgb
                break
        self.config.set_presets(presets)

        try:
            save_config(self.config)
        except ConfigSaveError as e:
            logger.error("Failed to save config after edit: %s", e)
            self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
        self.update_ui_from_config()
        # If RGB changed and this preset was the active one, re-apply it live.
        # / Если RGB изменился и этот пресет был активным — применяем заново.
        if rgb_changed:
            self.apply_preset_values(new_rgb)
        logger.info(
            "Preset #%s edited: '%s' -> '%s', RGB=(%.2f, %.2f, %.2f)",
            preset.id,
            old_name,
            new_name,
            r_val,
            g_val,
            b_val,
        )
        dialog.destroy()

    def delete_preset(self, pid: int) -> None:
        """
        Delete preset.
        Удалить пресет.

        Args:
            pid (int): Preset ID / ID пресета
        """
        presets = self.config.get_presets()
        preset = get_preset_by_id(presets, pid)
        if not preset:
            return

        presets = [p for p in presets if p.id != pid]
        self.config.set_presets(presets)
        self.config.favorites = [fid for fid in self.config.favorites if fid != pid]
        try:
            save_config(self.config)
        except ConfigSaveError as e:
            logger.error("Failed to save config after delete: %s", e)
            self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
        self.update_ui_from_config()
        logger.info("Preset #%s '%s' deleted", pid, preset.name)

    def activate_favorite_slot(self, slot_index: int) -> None:
        """
        Activate favorite slot.
        Активировать слот избранного.

        Args:
            slot_index (int): Slot index (0-4) / Индекс слота (0-4)
        """
        if self.fav_buttons[slot_index]["state"] == tk.DISABLED:
            return
        favorites_ids = self.config.favorites
        if slot_index < len(favorites_ids) and favorites_ids[slot_index] is not None:
            pid = favorites_ids[slot_index]
            preset = get_preset_by_id(self.config.get_presets(), pid)
            if preset:
                self.apply_preset_values(preset.rgb)
                logger.debug("Favorite slot %s activated: %s", slot_index + 1, preset.name)

    def remove_from_favorites(self, slot_index: int) -> None:
        """
        Remove from favorites.
        Удалить из избранного.

        Args:
            slot_index (int): Slot index (0-4) / Индекс слота (0-4)
        """
        favorites_ids = self.config.favorites
        if slot_index < len(favorites_ids) and favorites_ids[slot_index] is not None:
            removed_pid = favorites_ids[slot_index]
            favorites_ids.pop(slot_index)
            self.config.favorites = favorites_ids
            try:
                save_config(self.config)
            except ConfigSaveError as e:
                logger.error("Failed to save config after remove_from_favorites: %s", e)
                self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
            self.update_ui_from_config()
            logger.debug("Preset #%s removed from favorite slot %s", removed_pid, slot_index + 1)

    def _set_slider_labels(self, rgb: RGB) -> None:
        """
        Update slider value labels from an RGB instance.
        Обновляет текстовые метки слайдеров из значений RGB.

        Args:
            rgb (RGB): RGB values / Значения RGB
        """
        self.r_label.config(text=tr("red_value", rgb.r))
        self.g_label.config(text=tr("green_value", rgb.g))
        self.b_label.config(text=tr("blue_value", rgb.b))

    def _apply_gamma_async(self, rgb: RGB) -> None:
        """
        Run apply_gamma in a daemon thread; report result back on the Tk main loop.
        Запускает apply_gamma в daemon-потоке; возвращает результат в главный поток Tk.

        Args:
            rgb (RGB): RGB values to apply / Значения RGB для применения
        """
        monitor = self.current_monitor
        future: Future[tuple[bool, str]] = Future()

        def worker() -> None:
            try:
                result = apply_gamma(monitor, rgb)
                future.set_result(result)
            except Exception as e:  # pragma: no cover - defensive / защитный
                logger.error("Async gamma worker crashed: %s", e)
                future.set_result((False, f"Worker error: {e}"))

        def on_done() -> None:
            try:
                success, msg = future.result()
            except Exception as e:
                logger.error("Failed to retrieve async gamma result: %s", e)
                return
            if success:
                self.save_monitor_gamma(rgb)
                self.update_active_indicator()
            else:
                logger.warning("Failed to apply gamma: %s", msg)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        # Poll the future on the Tk main loop until it completes / Опрашиваем future в главном потоке Tk
        def poll() -> None:
            if future.done():
                on_done()
            else:
                self.root.after(50, poll)

        self.root.after(50, poll)

    def apply_preset_values(self, rgb: RGB) -> None:
        """
        Apply RGB values.
        Применить значения RGB.

        Args:
            rgb (RGB): RGB values / Значения RGB
        """
        self.r_val.set(rgb.r)
        self.g_val.set(rgb.g)
        self.b_val.set(rgb.b)
        # M15: use _set_slider_labels helper / используем _set_slider_labels
        self._set_slider_labels(rgb)
        self.apply_manual()

    def apply_manual(self) -> None:
        """Apply current slider values, throttled (async xrandr).

        UI feedback (slider labels) is updated immediately on every call so the user
        sees value changes in real time while holding ± or dragging the slider.
        The xrandr call is THROTTLED (not debounced) — it runs immediately, but no
        more often than every THROTTLE_MS milliseconds, so we don't spam the X server
        on auto-repeat (50 ms) / drag.

        / UI-отклик (подписи слайдеров) обновляется немедленно при каждом вызове —
        пользователь видит изменение значений в реальном времени при зажатии ± или
        перетаскивании. Вызов xrandr ТРОТТЛИТСЯ (не дебаунсится) — он запускается
        немедленно, но не чаще чем раз в THROTTLE_MS миллисекунд, чтобы не спамить
        X-сервер при auto-repeat (50 мс) / перетаскивании.
        """
        if not self.current_monitor:
            return
        # 1. Immediate UI feedback — update slider labels right away.
        # / Немедленный UI-отклик — обновляем подписи слайдеров сразу.
        rgb = RGB(r=self.r_val.get(), g=self.g_val.get(), b=self.b_val.get())
        self._set_slider_labels(rgb)
        # 2. Throttled xrandr — apply immediately if not throttled, otherwise schedule
        # a trailing call (so the final value is always applied after the last event).
        # / Троттлинг xrandr — применяем немедленно, если не троттлится, иначе
        # планируем финальный вызов (чтобы последнее значение точно применилось).
        try:
            now_ms = int(self.root.tk.call("clock", "milliseconds"))
        except Exception:
            now_ms = 0
        last = getattr(self, "_last_gamma_apply_ms", 0)
        if now_ms - last >= APPLY_GAMMA_THROTTLE_MS:
            # Enough time elapsed — apply immediately.
            # / Прошло достаточно времени — применяем немедленно.
            self._last_gamma_apply_ms = now_ms
            self._apply_gamma_async(rgb)
            # Cancel any pending trailing call — we just applied.
            # / Отменяем запланированный финальный вызов — только что применили.
            if self._pending_gamma is not None:
                try:
                    self.root.after_cancel(self._pending_gamma)
                except Exception:
                    pass
                self._pending_gamma = None
        else:
            # Throttled — schedule a trailing apply so the final value is not lost.
            # / Троттлится — планируем финальное применение, чтобы последнее значение не потерялось.
            if self._pending_gamma is not None:
                try:
                    self.root.after_cancel(self._pending_gamma)
                except Exception:
                    pass
            self._pending_gamma = self.root.after(
                APPLY_GAMMA_THROTTLE_MS, self._do_apply_manual
            )

    def _do_apply_manual(self) -> None:
        """Trailing gamma application (called after throttle window expires). /
        Финальное применение гаммы (вызывается после истечения окна троттлинга)."""
        self._pending_gamma = None
        if not self.current_monitor:
            return
        rgb = RGB(r=self.r_val.get(), g=self.g_val.get(), b=self.b_val.get())
        # Labels already updated in apply_manual() — no need to repeat here.
        # / Подписи уже обновлены в apply_manual() — повторно не нужно.
        try:
            self._last_gamma_apply_ms = int(self.root.tk.call("clock", "milliseconds"))
        except Exception:
            pass
        # C1: offload blocking xrandr call to a worker thread / выносим блокирующий вызов xrandr в поток
        self._apply_gamma_async(rgb)

    def _adjust_slider(self, var: tk.DoubleVar, delta: float) -> None:
        """
        Adjust slider value by step.
        Изменить значение слайдера на шаг.

        Args:
            var: Tkinter variable / Переменная Tkinter
            delta (float): Value change / Изменение значения
        """
        current = var.get()
        new_value = round(current + delta, 2)
        if new_value < SLIDER_MIN:
            new_value = SLIDER_MIN
        elif new_value > SLIDER_MAX:
            new_value = SLIDER_MAX
        var.set(new_value)
        self.apply_manual()

    def on_monitor_change(self) -> None:
        """Handle monitor change / Обработать смену монитора."""
        old_monitor = self.current_monitor
        self.current_monitor = self.monitor_var.get()
        self.config.system.monitor = self.current_monitor

        if old_monitor != self.current_monitor:
            self.config.system.last_rgb = [1.0, 1.0, 1.0]
            try:
                save_config(self.config)
            except ConfigSaveError as e:
                logger.error("Failed to save config on monitor change: %s", e)
                self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)

        self.load_monitor_gamma()
        self.update_active_indicator()
        logger.info("Switched to monitor: %s", self.current_monitor)

    def export_presets(self) -> None:
        """Export presets / Экспортировать пресеты."""
        file_path = self._pick_file(mode="save")
        if file_path:
            try:
                with open(file_path, FILE_MODE_WRITE, encoding=FILE_ENCODING) as f:
                    json.dump(self.config.presets, f, indent=2, ensure_ascii=False)
                self.show_message(
                    tr("success"), tr("export_success", file_path), MessageType.SUCCESS
                )
                logger.info("Presets exported to %s", file_path)
            except Exception as e:
                self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
                logger.error("Export error: %s", e)

    def import_presets(self) -> None:
        """Import presets / Импортировать пресеты."""
        file_path = self._pick_file(mode="open")
        if not file_path:
            return
        try:
            with open(file_path, FILE_MODE_READ, encoding=FILE_ENCODING) as f:
                imported_data = json.load(f)
            if not isinstance(imported_data, list):
                raise ValueError("File must contain a list of presets (JSON array).")

            existing_presets = self.config.get_presets()
            existing_ids = {p.id for p in existing_presets}
            max_id = max(existing_ids) if existing_ids else 0
            existing_signatures = {
                tuple(round(v, 2) for v in p.rgb.to_list()) for p in existing_presets
            }
            new_presets = []
            skipped_count = 0
            invalid_count = 0  # Счётчик невалидных пресетов / Counter for invalid presets

            for p_dict in imported_data:
                if not isinstance(p_dict, dict) or "name" not in p_dict or "rgb" not in p_dict:
                    continue
                if not isinstance(p_dict["rgb"], list) or len(p_dict["rgb"]) != 3:
                    continue

                # Валидация RGB / Validate RGB
                rgb_values = p_dict["rgb"]
                try:
                    r, g, b = float(rgb_values[0]), float(rgb_values[1]), float(rgb_values[2])
                except (ValueError, TypeError):
                    invalid_count += 1
                    continue

                # Clamp значений к допустимому диапазону / Clamp values to valid range
                r = max(SLIDER_MIN, min(SLIDER_MAX, r))
                g = max(SLIDER_MIN, min(SLIDER_MAX, g))
                b = max(SLIDER_MIN, min(SLIDER_MAX, b))
                p_dict["rgb"] = [r, g, b]

                signature = tuple(round(v, 2) for v in p_dict["rgb"])
                if signature in existing_signatures:
                    skipped_count += 1
                    continue
                max_id += 1
                preset = Preset(
                    id=max_id,
                    name=p_dict["name"],
                    rgb=RGB.from_list(p_dict["rgb"]),
                    comment=p_dict.get("comment", ""),
                )
                existing_ids.add(preset.id)
                existing_signatures.add(signature)
                new_presets.append(preset)

            msg_parts = []
            if new_presets:
                existing_presets.extend(new_presets)
                self.config.set_presets(existing_presets)
                try:
                    save_config(self.config)
                except ConfigSaveError as e:
                    logger.error("Failed to save config after import: %s", e)
                    self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
                self.update_ui_from_config()
                msg_parts.append(tr("import_added", len(new_presets)))
            if skipped_count > 0:
                msg_parts.append(tr("import_skipped", skipped_count))
            if invalid_count > 0:
                msg_parts.append(
                    f"[WARN] Invalid RGB values clamped: {invalid_count}"
                )  # Добавлено / Added
            if msg_parts:
                self.show_message(
                    tr("import_completed"), "\n".join(msg_parts), MessageType.SUCCESS
                )
            else:
                self.show_message(tr("warning"), tr("import_empty"), MessageType.WARNING)
            logger.info(
                "Import from %s: added %s, skipped %s, invalid %s",
                file_path,
                len(new_presets),
                skipped_count,
                invalid_count,
            )
        except json.JSONDecodeError:
            self.show_message(tr("error"), tr("import_invalid_json"), MessageType.ERROR)
            logger.error("Import error: invalid JSON in %s", file_path)
        except Exception as e:
            self.show_message(tr("error"), tr("import_error", e), MessageType.ERROR)
            logger.error("Import error: %s", e)

    def save_current_as_new(self) -> None:
        """Open save dialog with comment field / Открыть диалог сохранения с полем комментария."""
        # H2: use shared dialog builder; start with disabled Save (empty name) /
        # H2: используем общий построитель; кнопка Сохранить изначально выключена (пустое имя)
        self._build_text_input_dialog(
            title=tr("new_preset_title"),
            name_label_key="new_preset_label",
            initial_name="",
            initial_comment="",
            on_save=self._do_save_with_comment,
            save_btn_initial_state=tk.DISABLED,
        )

    def _do_save_with_comment(
        self, name_entry: tk.Entry, comment_text: tk.Text, dialog: tk.Toplevel
    ) -> None:
        """
        Save new preset with comment.
        Сохранить новый пресет с комментарием.

        Args:
            name_entry: Name entry widget / Виджет ввода имени
            comment_text: Comment text widget / Виджет текста комментария
            dialog: Dialog window / Окно диалога
        """
        name = name_entry.get().strip()
        if name:
            presets = self.config.get_presets()
            new_id = get_next_id(presets)
            comment = comment_text.get(TEXT_START_INDEX, TEXT_END_INDEX).strip()
            new_preset = Preset(
                id=new_id,
                name=name,
                rgb=RGB(r=self.r_val.get(), g=self.g_val.get(), b=self.b_val.get()),
                comment=comment,
            )
            presets.append(new_preset)
            self.config.set_presets(presets)

            favs = self.config.favorites
            for i in range(MAX_FAVORITES):
                if i >= len(favs) or favs[i] is None:
                    while len(favs) <= i:
                        favs.append(None)
                    favs[i] = new_id
                    break
            try:
                save_config(self.config)
            except ConfigSaveError as e:
                logger.error("Failed to save config after creating new preset: %s", e)
                self.show_message(tr("error"), tr("save_file_error", e), MessageType.ERROR)
            self.update_ui_from_config()
            logger.info(
                "Created new preset #%s '%s' with RGB %s", new_id, name, new_preset.rgb.to_list()
            )
        dialog.destroy()

    def on_closing(self) -> None:
        """Handle window close / Обработать закрытие окна."""
        self._hide_tooltip()
        self.config.ui.window_geometry = self.root.geometry()
        try:
            save_config(self.config)
        except ConfigSaveError as e:
            logger.error("Failed to save config on close: %s", e)
        logger.info("Program closed")
        self.root.destroy()


# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА
# =============================================================================


def main() -> int:
    """Entry point / Точка входа."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("Gamma — Color Temperature Manager v%s started", APP_VERSION)

    # Acquire singleton lock for both CLI and GUI modes / Берём singleton-блокировку и для CLI, и для GUI
    if not acquire_single_instance_lock():
        logger.info("Another instance already running, exiting")
        return 0

    parser = argparse.ArgumentParser(
        description="Gamma — Color Temperature Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Launch GUI / Запустить GUI
  %(prog)s --monitors                   # List monitors / Показать мониторы
  %(prog)s --restore                    # Restore last gamma and exit / Восстановить гамму и выйти
  %(prog)s --slot 1                     # Apply preset from favorite slot 1 / Применить пресет из слота 1
  %(prog)s --next                       # Apply next preset from favorites (cyclic) / Следующий пресет по кругу
  %(prog)s --preset 6500K               # Apply preset by name (or ID) / Применить пресет по имени или ID
  %(prog)s --slot 1 --monitor eDP-1     # Apply preset to specific monitor / Применить пресет на конкретный монитор
    """,
    )

    parser.add_argument(
        "--next", action="store_true", help="Apply next preset from favorites (cyclic)"
    )
    parser.add_argument(
        "--slot",
        type=int,
        choices=list(range(1, MAX_FAVORITES + 1)),
        help="Apply preset from favorite slot (1-5)",
    )
    parser.add_argument("--preset", type=str, help="Apply preset by ID or name")
    parser.add_argument(
        "--monitors",
        action="store_true",
        help="List available monitors / Показать доступные мониторы",
    )
    parser.add_argument(
        "--monitor", type=str, help="Explicitly specify monitor name (e.g., eDP-1, HDMI-A-0)"
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore last applied gamma and exit / Восстановить последнюю гамму и выйти",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Delay in seconds before applying gamma (default: 3) / Задержка в секундах перед применением гаммы (по умолчанию: 3)",
    )

    args = parser.parse_args()

    if args.next or args.slot or args.preset:
        logger.info("CLI mode: apply preset, args=%s", vars(args))
        config = load_config()
        monitors = get_monitors()
        available_monitors = [m.name for m in monitors]
        logger.info("Available monitors: %s", available_monitors)
        monitor = None
        if args.monitor:
            if args.monitor in available_monitors:
                monitor = args.monitor
            else:
                logger.error("Monitor '%s' not found", args.monitor)
                print(f"Error: monitor '{args.monitor}' not found.", file=sys.stderr)
                if available_monitors:
                    print(f"\nAvailable monitors:", file=sys.stderr)
                    for m in available_monitors:
                        print(f"{CLI_BULLET}{m}", file=sys.stderr)
                else:
                    print("\nNo monitors detected. Check connection.", file=sys.stderr)
                return 1
        else:
            saved_monitor = config.system.monitor
            if saved_monitor and saved_monitor in available_monitors:
                monitor = saved_monitor
            elif available_monitors:
                monitor = available_monitors[0]
                logger.warning("Saved monitor '%s' unavailable, using %s", saved_monitor, monitor)
                print(f"Warning: saved monitor '{saved_monitor}' is unavailable.", file=sys.stderr)
                print(f"Using first available: {monitor}", file=sys.stderr)
            else:
                logger.error("No monitors detected")
                print("Error: no monitors detected.", file=sys.stderr)
                print("Check monitor connection and try again.", file=sys.stderr)
                return 1

        favorites = config.favorites
        presets = config.get_presets()
        target_preset = None
        if args.slot:
            slot_index = args.slot - 1
            if slot_index < len(favorites) and favorites[slot_index] is not None:
                pid = favorites[slot_index]
                target_preset = get_preset_by_id(presets, pid)
                if not target_preset:
                    logger.error("Preset with ID %s not found in presets", pid)
                    print(f"Error: preset with ID {pid} not found in presets.", file=sys.stderr)
                    return 1
            else:
                logger.error("Slot %s is empty or does not exist", args.slot)
                print(f"Error: slot {args.slot} is empty or does not exist.", file=sys.stderr)
                return 1
        elif args.preset:
            for p in presets:
                if str(p.id) == args.preset or p.name == args.preset:
                    target_preset = p
                    break
            if not target_preset:
                logger.error("Preset '%s' not found", args.preset)
                print(f"Error: preset '{args.preset}' not found.", file=sys.stderr)
                return 1
        elif args.next:
            filled_slots = [
                (i, favorites[i]) for i in range(len(favorites)) if favorites[i] is not None
            ]
            if not filled_slots:
                logger.error("Favorites are empty")
                print("Error: favorites are empty. Add presets via GUI.", file=sys.stderr)
                return 1
            current_rgb = None
            monitor_gammas = config.system.monitor_gammas
            if monitor in monitor_gammas:
                current_rgb = RGB.from_list(monitor_gammas[monitor])
            last_slot_index = -1
            if current_rgb:
                for slot_idx, pid in filled_slots:
                    preset = get_preset_by_id(presets, pid)
                    if preset and _rgb_match(preset.rgb, current_rgb):
                        last_slot_index = slot_idx
                        break
            if last_slot_index == -1:
                last_slot_index = config.system.last_cli_slot
            next_slot = None
            for i, (slot_idx, pid) in enumerate(filled_slots):
                if slot_idx > last_slot_index:
                    next_slot = (slot_idx, pid)
                    break
            if next_slot is None:
                next_slot = filled_slots[0]
            slot_idx, pid = next_slot
            target_preset = get_preset_by_id(presets, pid)
            if not target_preset:
                logger.error("Preset with ID %s not found in presets", pid)
                print(f"Error: preset with ID {pid} not found in presets.", file=sys.stderr)
                return 1
            config.system.last_cli_slot = slot_idx

        if target_preset:
            success, msg = apply_gamma(monitor, target_preset.rgb)
            if success:
                print(
                    f"{CLI_SUCCESS_PREFIX}Applied: {target_preset.name} (RGB: {target_preset.rgb.r:.2f}, {target_preset.rgb.g:.2f}, {target_preset.rgb.b:.2f}) to monitor {monitor}"
                )
                config.system.monitor = monitor
                config.system.monitor_gammas[monitor] = target_preset.rgb.to_list()
                config.system.last_rgb = target_preset.rgb.to_list()
                try:
                    save_config(config)
                except ConfigSaveError as e:
                    logger.error("Failed to save config after CLI apply: %s", e)
                    print(f"Error: failed to save config: {e}", file=sys.stderr)
                logger.info("[OK] CLI: Applied '%s' to %s", target_preset.name, monitor)
            else:
                print(f"{CLI_ERROR_PREFIX}Error: {msg}", file=sys.stderr)
                logger.error("[ERROR] CLI: Gamma apply error: %s", msg)
                return 1

    elif args.restore:
        logger.info("CLI mode: restore gamma to all monitors")
        delay = getattr(args, "delay", 3)
        if delay > 0:
            logger.info("Waiting %s seconds for monitors to initialize...", delay)
            print(f"{CLI_WAIT_PREFIX}Waiting {delay}s for monitors...")
            try:
                time.sleep(delay)
            except KeyboardInterrupt:
                # User pressed Ctrl+C during the startup delay — exit cleanly.
                # Пользователь нажал Ctrl+C во время стартовой задержки — чистый выход.
                print("\nInterrupted during startup delay.", file=sys.stderr)
                logger.info("Interrupted during restore startup delay")
                return 130
        config = load_config()
        monitors = []
        for attempt in range(RESTORE_MAX_ATTEMPTS):
            monitors = get_monitors()
            if len(monitors) >= 1:
                break
            logger.warning(
                "Attempt %s/%s: no monitors found, waiting...", attempt + 1, RESTORE_MAX_ATTEMPTS
            )
            try:
                time.sleep(RESTORE_RETRY_DELAY)
            except KeyboardInterrupt:
                print("\nInterrupted during monitor detection.", file=sys.stderr)
                logger.info("Interrupted during restore monitor detection")
                return 130
        available_monitors = [m.name for m in monitors]
        logger.info("Available monitors: %s", available_monitors)
        if not available_monitors:
            logger.error("No monitors detected after retries")
            print(f"{CLI_ERROR_PREFIX}Error: no monitors detected.", file=sys.stderr)
            return 1
        monitor_gammas = config.system.monitor_gammas
        last_rgb_list = config.system.last_rgb
        last_rgb = RGB.from_list(last_rgb_list)
        applied_count = 0
        for monitor in monitors:
            monitor_name = monitor.name
            if monitor_name in monitor_gammas:
                rgb = RGB.from_list(monitor_gammas[monitor_name])
            else:
                rgb = last_rgb
            preset_name = PRESET_NAME_CUSTOM
            target_rgb_tuple = (round(rgb.r, 2), round(rgb.g, 2), round(rgb.b, 2))
            for p in config.get_presets():
                preset_tuple = (round(p.rgb.r, 2), round(p.rgb.g, 2), round(p.rgb.b, 2))
                if preset_tuple == target_rgb_tuple:
                    preset_name = p.name
                    break
            success, msg = apply_gamma(monitor_name, rgb)
            if success:
                logger.info(
                    "[OK] Restored gamma for %s (%s): R=%.2f G=%.2f B=%.2f",
                    monitor_name,
                    preset_name,
                    rgb.r,
                    rgb.g,
                    rgb.b,
                )
                print(
                    f"{CLI_SUCCESS_PREFIX}{monitor_name}: {preset_name} (RGB: {rgb.r:.2f}, {rgb.g:.2f}, {rgb.b:.2f})"
                )
                config.system.monitor_gammas[monitor_name] = rgb.to_list()
                applied_count += 1
            else:
                logger.error("[ERROR] Failed to apply gamma to %s: %s", monitor_name, msg)
                print(f"{CLI_ERROR_PREFIX}{monitor_name}: {msg}", file=sys.stderr)
        if applied_count > 0:
            try:
                save_config(config)
            except ConfigSaveError as e:
                logger.error("Failed to save config after CLI restore: %s", e)
                print(f"Error: failed to save config: {e}", file=sys.stderr)
            logger.info("[OK] Applied gamma to %s monitor(s)", applied_count)
            print(f"\n{CLI_SUCCESS_PREFIX}Applied to {applied_count} monitor(s)")
        else:
            logger.warning("Failed to apply gamma to any monitor")
            print(f"\n{CLI_WARNING_PREFIX}Failed to apply gamma to any monitor.", file=sys.stderr)
        return 0

    elif args.monitors:
        logger.info("CLI mode: list monitors")
        monitors = get_monitors()
        available_monitors = [m.name for m in monitors]
        if not available_monitors:
            print(f"{CLI_ERROR_PREFIX}No monitors detected")
            return 1
        print(f"\n{CLI_INFO_PREFIX}Available monitors ({len(available_monitors)}):")
        print(CLI_SEPARATOR_CHAR * CLI_SEPARATOR_LENGTH)
        for i, monitor in enumerate(monitors, 1):
            print(CLI_MONITOR_FORMAT.format(i=i, name=monitor.name, mode=monitor.mode))
        print(CLI_SEPARATOR_CHAR * CLI_SEPARATOR_LENGTH)
        config = load_config()
        saved_monitor = config.system.monitor
        monitor_gammas = config.system.monitor_gammas
        if monitor_gammas:
            print(f"\n{CLI_SAVE_PREFIX}Saved gamma settings:")
            for mon_name, rgb_list in monitor_gammas.items():
                status = CLI_CHECK if mon_name in available_monitors else CLI_CROSS
                rgb = RGB.from_list(rgb_list)
                print(
                    CLI_GAMMA_FORMAT.format(
                        status=status, name=mon_name, r=rgb.r, g=rgb.g, b=rgb.b
                    )
                )
        if saved_monitor:
            print(f"\n{CLI_TARGET_PREFIX}Current monitor: {saved_monitor}")
        print()
        return 0

    else:
        logger.info("GUI mode")
        # Singleton lock is already acquired at the top of main() /
        # Singleton-блокировка уже получена в начале main()
        root = tk.Tk()
        app = GammaApp(root)
        logger.info("GUI initialized successfully")
        # Allow Ctrl+C in the terminal to close the GUI gracefully.
        # По умолчанию tk mainloop блокирует SIGINT; этот handler
        # позволяет Ctrl+C в терминале корректно закрыть окно.
        def _on_sigint(signum, frame):
            logger.info("GUI: SIGINT received, closing")
            try:
                root.after(0, root.destroy)
            except Exception:
                pass
        signal.signal(signal.SIGINT, _on_sigint)
        root.mainloop()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        # Graceful Ctrl+C handling — exit with standard SIGINT code 130.
        # Аккуратная обработка Ctrl+C — выход со стандартным кодом SIGINT 130.
        # Covers both CLI (sleep/subprocess) and GUI (Ctrl+C in terminal) cases.
        # Покрывает как CLI (sleep/subprocess), так и GUI (Ctrl+C в терминале).
        try:
            logger.info("Interrupted by user (KeyboardInterrupt)")
        except Exception:
            pass
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
