import ctypes
import json
import logging
import random
import sys
import time
from ctypes import wintypes
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QEvent, QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


APP_DIR = Path.home() / "AppData" / "Roaming" / "MatrixDashboard"
CONFIG_PATH = APP_DIR / "config.json"
LOG_PATH = APP_DIR / "matrix_dash.log"

# Centralized animation and layout parameters keep the paint loop readable.
MATRIX_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MIN_SCALE = 0.65
MAX_SCALE = 1.35
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
STREAM_MIN_LENGTH = 8
STREAM_MAX_LENGTH = 28
ROWS_PER_SECOND = 12.5
PREVIEW_SYNC_INTERVAL = 500
SECONDS_PER_DAY = 86400


def get_logger():
    """Create the application logger once and keep runtime files out of the repo."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("matrix_dashboard")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


LOGGER = get_logger()


@dataclass
class AppConfig:
    title: str = "SYSTEM DASHBOARD"
    todos: tuple = (
        "1. 深度优化底层算力模型 (开会摸鱼)",
        "2. 清理系统多余缓存数据 (倒杯咖啡)",
        "3. 部署自动化运行脚本 (准备下班)",
    )
    font_size: int = 16
    animation_interval: int = 100

    @classmethod
    def load(cls):
        """Load user settings while keeping safe bounds for every editable value."""
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return cls(
                title=str(data.get("title", cls.title))[:80] or cls.title,
                todos=tuple(str(item)[:160] for item in data.get("todos", cls.todos) if str(item).strip())[:8]
                or cls.todos,
                font_size=max(10, min(24, int(data.get("font_size", cls.font_size)))),
                animation_interval=max(90, min(120, int(data.get("animation_interval", cls.animation_interval)))),
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            LOGGER.warning("Unable to load configuration: %s", exc)
            return cls()

    def save(self):
        """Persist the validated configuration in the user's application data folder."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


@lru_cache(maxsize=None)
def font_family(preferred, fallback):
    """Return the preferred installed font, or its fallback."""
    families = set(QFontDatabase.families())
    return preferred if preferred in families else fallback


class MatrixDashboard(QWidget):
    """Full-screen dashboard or an embedded Windows screen-saver preview."""
    def __init__(self, config, preview=False, screen=None, preview_handle=None):
        super().__init__()
        self.config = config
        self.preview = preview
        self.preview_handle = preview_handle
        self.screen = screen
        self.cell_size = config.font_size
        self.drops = []
        self.stream_lengths = []
        self.stream_chars = []
        self.last_mouse_position = None
        self.info_time = ""
        self.info_progress = 0.0
        self.last_info_update = 0.0
        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()

        self.matrix_chars = MATRIX_CHARS
        self.matrix_font = QFont(font_family("Consolas", "Courier New"), self.cell_size)
        self.title_font = QFont(font_family("Consolas", "Courier New"), 24, QFont.Bold)
        self.time_font = QFont(font_family("Consolas", "Courier New"), 14)
        self.progress_font = QFont(font_family("Consolas", "Courier New"), 12)
        self.todo_font = QFont(font_family("Microsoft YaHei UI", "Microsoft YaHei"), 12)
        self.footer_font = QFont(font_family("Consolas", "Courier New"), 10)
        self.green = QColor("#00FF00")
        self.white = QColor("#FFFFFF")
        self.panel_background = QColor(0, 0, 0, 220)
        self.progress_background = QColor("#001A00")
        self.progress_border = QColor("#006600")

        self.refresh_info()
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.advance_animation)
        self.animation_timer.start(config.animation_interval)
        self.preview_timer = None
        if self.preview:
            self.preview_timer = QTimer(self)
            self.preview_timer.timeout.connect(self.sync_preview)
            self.preview_timer.start(PREVIEW_SYNC_INTERVAL)

        self.setWindowTitle("Matrix Dashboard")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        if self.preview:
            self.setAttribute(Qt.WA_NativeWindow)
        else:
            self.setCursor(Qt.BlankCursor)

    def resizeEvent(self, event):
        """Resize columns without resetting the existing streams."""
        self.update_fonts()
        columns = max(1, self.width() // self.cell_size + 1)
        if len(self.drops) < columns:
            count = columns - len(self.drops)
            self.drops.extend(random.randint(-self.height() // self.cell_size, 0) for _ in range(count))
            lengths = [random.randint(STREAM_MIN_LENGTH, STREAM_MAX_LENGTH) for _ in range(count)]
            self.stream_lengths.extend(lengths)
            self.stream_chars.extend(self.create_stream(length) for length in lengths)
        elif len(self.drops) > columns:
            del self.drops[columns:]
            del self.stream_lengths[columns:]
            del self.stream_chars[columns:]
        super().resizeEvent(event)

    def update_fonts(self):
        scale = self.layout_scale()
        self.cell_size = max(10, round(self.config.font_size * scale))
        self.matrix_font.setPointSize(self.cell_size)
        self.title_font.setPointSize(max(15, round(24 * scale)))
        self.time_font.setPointSize(max(9, round(14 * scale)))
        self.progress_font.setPointSize(max(8, round(12 * scale)))
        self.todo_font.setPointSize(max(8, round(12 * scale)))
        self.footer_font.setPointSize(max(7, round(10 * scale)))

    def advance_animation(self):
        """Advance the animation according to elapsed time, not timer frequency."""
        elapsed = min(self.elapsed_timer.restart() / 1000.0, 0.25)
        for column, drop in enumerate(self.drops):
            if drop * self.cell_size > self.height() + self.stream_lengths[column] * self.cell_size and random.random() > 0.975:
                self.drops[column] = random.randint(-20, 0)
                self.stream_lengths[column] = random.randint(STREAM_MIN_LENGTH, STREAM_MAX_LENGTH)
                self.stream_chars[column] = self.create_stream(self.stream_lengths[column])
            else:
                self.drops[column] += ROWS_PER_SECOND * elapsed
                self.stream_chars[column][0] = random.choice(self.matrix_chars)
        if time.monotonic() - self.last_info_update >= 1:
            self.refresh_info()
        self.update()

    def refresh_info(self):
        """Refresh low-frequency dashboard data once per second."""
        self.info_time = time.strftime("TIME: %Y-%m-%d %H:%M:%S")
        now = time.localtime()
        self.info_progress = (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec) / SECONDS_PER_DAY
        self.last_info_update = time.monotonic()

    def create_stream(self, length):
        """Create one cached stream; animation frames only change its head."""
        return [random.choice(self.matrix_chars) for _ in range(length)]

    def layout_scale(self):
        """Calculate a bounded scale from the 1920x1080 reference layout."""
        return max(
            MIN_SCALE,
            min(min(self.width() / BASE_WIDTH, self.height() / BASE_HEIGHT), MAX_SCALE),
        )

    def keyPressEvent(self, event):
        # Screen-saver mode exits on input; preview mode belongs to the host dialog.
        if not self.preview:
            self.close()

    def mousePressEvent(self, event):
        if not self.preview:
            self.close()

    def mouseMoveEvent(self, event):
        if self.preview:
            return
        position = event.position().toPoint()
        if self.last_mouse_position is not None and (position - self.last_mouse_position).manhattanLength() >= 5:
            self.close()
        self.last_mouse_position = position

    def event(self, event):
        if not self.preview and event.type() == QEvent.WindowDeactivate:
            self.close()
        return super().event(event)

    def draw_matrix(self, painter):
        """Draw cached characters and avoid regenerating complete streams."""
        painter.setFont(self.matrix_font)
        for column, drop in enumerate(self.drops):
            x = column * self.cell_size
            for offset, character in enumerate(self.stream_chars[column]):
                y = (int(drop) - offset) * self.cell_size
                if -self.cell_size <= y <= self.height():
                    painter.setPen(self.white if offset == 0 else self.green)
                    painter.drawText(QPointF(x, y), character)

    def draw_dashboard(self, painter):
        """Draw the responsive dashboard and clip long todo text to its cell."""
        scale = self.layout_scale()
        panel_width = min(self.width() * 0.88, 720 * scale)
        panel_height = min(self.height() * 0.76, max(300 * scale, (170 + len(self.config.todos) * 30) * scale))
        panel = QRectF((self.width() - panel_width) / 2, (self.height() - panel_height) / 2, panel_width, panel_height)
        margin = max(16, 32 * scale)
        painter.setPen(QPen(self.green, max(1, round(2 * scale))))
        painter.setBrush(self.panel_background)
        painter.drawRect(panel)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self.green)

        title_rect = QRectF(panel.left() + margin, panel.top() + 10 * scale, panel.width() - margin * 2, 42 * scale)
        painter.setFont(self.title_font)
        painter.drawText(title_rect, Qt.AlignCenter, self.config.title)
        painter.setFont(self.time_font)
        painter.drawText(QRectF(panel.left() + margin, panel.top() + 58 * scale, panel.width() - margin * 2, 28 * scale), Qt.AlignCenter, self.info_time)

        painter.setFont(self.progress_font)
        progress_y = panel.top() + 102 * scale
        content_width = panel.width() - margin * 2
        label_width = 110 * scale
        percent_width = 78 * scale
        bar_width = max(30 * scale, content_width - label_width - percent_width - 20 * scale)
        label_rect = QRectF(panel.left() + margin, progress_y, label_width, 24 * scale)
        bar_rect = QRectF(label_rect.right() + 8 * scale, progress_y + 4 * scale, bar_width, 16 * scale)
        percent_rect = QRectF(bar_rect.right() + 8 * scale, progress_y, percent_width, 24 * scale)
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, "DAY PROGRESS")
        painter.setPen(QPen(self.progress_border, 1))
        painter.setBrush(self.progress_background)
        painter.drawRect(bar_rect)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.green)
        painter.drawRect(QRectF(bar_rect.left() + 1, bar_rect.top() + 1, max(0, (bar_rect.width() - 2) * self.info_progress), bar_rect.height() - 2))
        painter.setPen(self.green)
        painter.drawText(percent_rect, Qt.AlignVCenter | Qt.AlignRight, f"{self.info_progress * 100:.2f}%")

        divider_y = panel.top() + 142 * scale
        painter.setPen(QPen(self.green, 1, Qt.DashLine))
        painter.drawLine(panel.left() + margin, divider_y, panel.right() - margin, divider_y)
        painter.setPen(self.green)
        painter.setFont(self.todo_font)
        metrics = painter.fontMetrics()
        todo_width = panel.width() - margin * 2
        for index, item in enumerate(self.config.todos):
            text = metrics.elidedText(item, Qt.ElideRight, int(todo_width))
            rect = QRectF(panel.left() + margin, divider_y + 10 * scale + index * 30 * scale, todo_width, 26 * scale)
            painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.setFont(self.footer_font)
        footer_rect = QRectF(panel.left() + margin, panel.bottom() - 30 * scale, todo_width, 20 * scale)
        painter.drawText(footer_rect, Qt.AlignCenter, "PRESS ANY KEY TO EXIT")

    def sync_preview(self):
        """Keep the embedded child aligned with the host preview client area."""
        if self.preview_handle:
            rect = get_preview_rect(self.preview_handle)
            if rect:
                self.setGeometry(0, 0, rect.right, rect.bottom)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), Qt.black)
        self.draw_matrix(painter)
        self.draw_dashboard(painter)
        painter.end()


def get_preview_rect(handle):
    """Return the preview host's client size, or None when its HWND is gone."""
    user32 = ctypes.windll.user32
    rect = wintypes.RECT()
    if not user32.IsWindow(handle) or not user32.GetClientRect(handle, ctypes.byref(rect)):
        return None
    return rect


def embed_in_preview(window, preview_handle):
    """Convert the Qt top-level window into a child of Windows' preview host."""
    if not get_preview_rect(preview_handle):
        return False
    user32 = ctypes.windll.user32
    hwnd = int(window.winId())
    parent = ctypes.c_void_p(preview_handle)
    user32.SetParent(ctypes.c_void_p(hwnd), parent)
    get_style = user32.GetWindowLongPtrW
    set_style = user32.SetWindowLongPtrW
    style = int(get_style(ctypes.c_void_p(hwnd), -16))
    style = (style | 0x40000000 | 0x10000000) & ~0x80000000
    set_style(ctypes.c_void_p(hwnd), -16, ctypes.c_void_p(style))
    rect = get_preview_rect(preview_handle)
    window.setGeometry(0, 0, rect.right, rect.bottom)
    return True


class ConfigDialog(QDialog):
    """Small configuration UI used by the Windows screen-saver /c entry point."""
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Matrix Dashboard Settings")
        self.title_edit = QLineEdit(config.title)
        self.todos_edit = QPlainTextEdit("\n".join(config.todos))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(config.font_size)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(90, 120)
        self.interval_spin.setValue(config.animation_interval)
        form = QFormLayout()
        form.addRow("Title", self.title_edit)
        form.addRow("Todo items", self.todos_edit)
        form.addRow("Matrix font", self.font_spin)
        form.addRow("Animation interval (ms)", self.interval_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def result_config(self):
        todos = tuple(line.strip()[:160] for line in self.todos_edit.toPlainText().splitlines() if line.strip())[:8]
        return AppConfig(self.title_edit.text().strip()[:80] or "SYSTEM DASHBOARD", todos or AppConfig().todos, self.font_spin.value(), self.interval_spin.value())


def run_screensaver(app, config):
    """Create one independent full-screen window per available display."""
    windows = []
    for screen in app.screens():
        window = MatrixDashboard(config, screen=screen)
        window.setGeometry(screen.geometry())
        window.showFullScreen()
        windows.append(window)
    return app.exec()


def main():
    """Dispatch Windows screen-saver modes without changing their argument contract."""
    args = sys.argv[1:]
    mode = args[0].lower() if args else "/s"
    app = QApplication(sys.argv)
    config = AppConfig.load()
    if mode == "/c":
        dialog = ConfigDialog(config)
        if dialog.exec() == QDialog.Accepted:
            try:
                dialog.result_config().save()
            except OSError as exc:
                LOGGER.exception("Unable to save configuration: %s", exc)
        return 0
    if mode == "/p":
        if len(args) < 2:
            LOGGER.warning("Preview mode requires a window handle")
            return 0
        try:
            handle = int(args[1], 0)
        except ValueError:
            LOGGER.warning("Invalid preview handle: %s", args[1])
            return 0
        window = MatrixDashboard(config, preview=True, preview_handle=handle)
        window.show()
        if not embed_in_preview(window, handle):
            LOGGER.warning("Unable to embed preview window: %s", handle)
            window.close()
            return 0
        return app.exec()
    if mode != "/s":
        LOGGER.warning("Unknown screen saver mode: %s", mode)
        return 0
    return run_screensaver(app, config)


if __name__ == "__main__":
    raise SystemExit(main())
