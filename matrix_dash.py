import random
import sys
import time
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QElapsedTimer, QEvent, QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


class MatrixDashboard(QWidget):
    def __init__(self, preview=False):
        super().__init__()
        self.preview = preview
        self.setWindowTitle("Matrix Dashboard")
        self.setWindowFlag(Qt.FramelessWindowHint)
        if not self.preview:
            self.setCursor(Qt.BlankCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self.font_size = 16
        self.matrix_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.drops = []
        self.stream_lengths = []
        self.stream_chars = []
        self.last_mouse_position = None
        self.title_text = "SYSTEM DASHBOARD"
        self.todo_list = [
            "1. 深度优化底层算力模型 (开会摸鱼)",
            "2. 清理系统多余缓存数据 (倒杯咖啡)",
            "3. 部署自动化运行脚本 (准备下班)",
        ]

        self.matrix_font = QFont("Consolas", self.font_size)
        self.title_font = QFont("Consolas", 24, QFont.Bold)
        self.time_font = QFont("Consolas", 14)
        self.progress_font = QFont("Consolas", 12)
        self.todo_font = QFont("Microsoft YaHei", 12)
        self.footer_font = QFont("Consolas", 10)
        self.green = QColor("#00FF00")
        self.white = QColor("#FFFFFF")
        self.panel_background = QColor(0, 0, 0, 220)
        self.progress_background = QColor("#001A00")
        self.progress_border = QColor("#006600")
        self.info_time = ""
        self.info_progress = 0.0
        self.last_info_update = 0.0
        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()
        self.refresh_info()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.advance_animation)
        self.animation_timer.start(100)

        # showFullScreen can emit resizeEvent, so all state must be ready first.
        if not self.preview:
            self.showFullScreen()

    def resizeEvent(self, event):
        columns = max(1, self.width() // self.font_size + 1)
        if len(self.drops) != columns:
            old_columns = len(self.drops)
            if columns > old_columns:
                self.drops.extend(
                    random.randint(-self.height() // self.font_size, 0)
                    for _ in range(columns - old_columns)
                )
                self.stream_lengths.extend(random.randint(8, 28) for _ in range(columns - old_columns))
                self.stream_chars.extend(
                    [random.choice(self.matrix_chars) for _ in range(length)]
                    for length in self.stream_lengths[old_columns:]
                )
            else:
                del self.drops[columns:]
                del self.stream_lengths[columns:]
                del self.stream_chars[columns:]
        self.update_fonts()
        super().resizeEvent(event)

    def update_fonts(self):
        scale = min(self.width() / 1920, self.height() / 1080)
        scale = max(0.65, min(scale, 1.35))
        self.matrix_font.setPointSize(max(9, round(16 * scale)))
        self.title_font.setPointSize(max(15, round(24 * scale)))
        self.time_font.setPointSize(max(9, round(14 * scale)))
        self.progress_font.setPointSize(max(8, round(12 * scale)))
        self.todo_font.setPointSize(max(8, round(12 * scale)))
        self.footer_font.setPointSize(max(7, round(10 * scale)))

    def advance_animation(self):
        elapsed = min(self.elapsed_timer.restart() / 1000.0, 0.25)
        rows_per_second = 12.5
        for column, drop in enumerate(self.drops):
            if drop * self.font_size > self.height() and random.random() > 0.975:
                self.drops[column] = random.randint(-20, 0)
                self.stream_lengths[column] = random.randint(8, 28)
                self.stream_chars[column] = [
                    random.choice(self.matrix_chars)
                    for _ in range(self.stream_lengths[column])
                ]
            else:
                self.drops[column] += rows_per_second * elapsed
                self.stream_chars[column][0] = random.choice(self.matrix_chars)

        if time.monotonic() - self.last_info_update >= 1.0:
            self.refresh_info()
        self.update()

    def refresh_info(self):
        self.info_time = time.strftime("TIME: %Y-%m-%d %H:%M:%S")
        self.info_progress = self.day_progress()
        self.last_info_update = time.monotonic()

    def keyPressEvent(self, event):
        if not self.preview:
            self.close()

    def mousePressEvent(self, event):
        if not self.preview:
            self.close()

    def mouseMoveEvent(self, event):
        if self.preview:
            return
        position = event.position().toPoint()
        if self.last_mouse_position is not None and position != self.last_mouse_position:
            self.close()
        self.last_mouse_position = position

    def event(self, event):
        if not self.preview and event.type() == QEvent.WindowDeactivate:
            self.close()
        return super().event(event)

    def day_progress(self):
        now = time.localtime()
        seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        return seconds / (24 * 60 * 60)

    def draw_matrix(self, painter):
        painter.setFont(self.matrix_font)
        for column, drop in enumerate(self.drops):
            x = column * self.font_size
            for offset in range(self.stream_lengths[column]):
                row = int(drop) - offset
                y = row * self.font_size
                if -self.font_size <= y <= self.height():
                    painter.setPen(self.white if offset == 0 else self.green)
                    painter.drawText(QPointF(x, y), self.stream_chars[column][offset])

    def draw_dashboard(self, painter):
        scale = min(self.width() / 1920, self.height() / 1080)
        scale = max(0.65, min(scale, 1.35))
        panel_width = min(self.width() * 0.86, 720 * scale)
        panel_height = min(self.height() * 0.72, 360 * scale)
        panel = QRectF(
            (self.width() - panel_width) / 2,
            (self.height() - panel_height) / 2,
            panel_width,
            panel_height,
        )
        margin = max(16, 32 * scale)
        green = self.green
        painter.setPen(QPen(green, 2))
        painter.setBrush(self.panel_background)
        painter.drawRect(panel)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(green)
        painter.setFont(self.title_font)
        title_rect = QRectF(panel.left() + margin, panel.top() + margin / 2,
                            panel.width() - margin * 2, 45 * scale)
        painter.drawText(title_rect, Qt.AlignCenter, self.title_text)

        painter.setFont(self.time_font)
        time_rect = QRectF(panel.left() + margin, panel.top() + 65 * scale,
                           panel.width() - margin * 2, 28 * scale)
        painter.drawText(time_rect, Qt.AlignCenter, self.info_time)

        painter.setFont(self.progress_font)
        progress = self.info_progress
        progress_y = panel.top() + 108 * scale
        label_rect = QRectF(panel.left() + margin, progress_y, 105 * scale, 24 * scale)
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, "DAY PROGRESS")

        # Draw a geometric bar instead of block characters, whose glyph heights
        # can differ between installed fonts.
        available_width = panel.width() - margin * 2
        bar_width = max(40 * scale, available_width - 200 * scale)
        bar_rect = QRectF(label_rect.right() + 10 * scale, progress_y + 4 * scale,
                          bar_width, 16 * scale)
        painter.setPen(QPen(self.progress_border, 1))
        painter.setBrush(self.progress_background)
        painter.drawRect(bar_rect)
        painter.setPen(Qt.NoPen)
        painter.setBrush(green)
        painter.drawRect(QRectF(bar_rect.left() + 1, bar_rect.top() + 1,
                                max(0, (bar_rect.width() - 2) * progress), bar_rect.height() - 2))

        painter.setPen(green)
        percent_rect = QRectF(bar_rect.right() + 10 * scale, progress_y,
                              75 * scale, 24 * scale)
        painter.drawText(percent_rect, Qt.AlignVCenter | Qt.AlignRight, f"{progress * 100:.2f}%")

        painter.setPen(QPen(green, 1, Qt.DashLine))
        divider_y = panel.top() + 150 * scale
        painter.drawLine(panel.left() + margin, divider_y, panel.right() - margin, divider_y)
        painter.setPen(green)
        painter.setFont(self.todo_font)
        todo_rect = QRectF(panel.left() + margin, divider_y + 14 * scale,
                           panel.width() - margin * 2, 30 * scale)
        for index, item in enumerate(self.todo_list):
            painter.drawText(todo_rect.translated(0, index * 30 * scale),
                             Qt.AlignVCenter | Qt.AlignLeft, item)

        painter.setFont(self.footer_font)
        footer_rect = QRectF(panel.left() + margin, panel.bottom() - 30 * scale,
                             panel.width() - margin * 2, 20 * scale)
        painter.drawText(footer_rect, Qt.AlignCenter, "PRESS ANY KEY TO EXIT")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), Qt.black)
        self.draw_matrix(painter)
        self.draw_dashboard(painter)
        painter.end()


def embed_in_preview(window, preview_handle):
    """Attach the Qt window to the HWND supplied by Windows screen saver preview."""
    user32 = ctypes.windll.user32
    hwnd = int(window.winId())
    parent = ctypes.c_void_p(preview_handle)

    get_client_rect = user32.GetClientRect
    get_client_rect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.RECT)]
    get_client_rect.restype = ctypes.c_bool
    rect = wintypes.RECT()
    if not get_client_rect(parent, ctypes.byref(rect)):
        return False

    set_parent = user32.SetParent
    set_parent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    set_parent.restype = ctypes.c_void_p
    set_parent(ctypes.c_void_p(hwnd), parent)

    get_style = user32.GetWindowLongPtrW
    set_style = user32.SetWindowLongPtrW
    get_style.argtypes = [ctypes.c_void_p, ctypes.c_int]
    set_style.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    get_style.restype = ctypes.c_void_p
    set_style.restype = ctypes.c_void_p
    style = int(get_style(ctypes.c_void_p(hwnd), -16))
    style = (style | 0x40000000 | 0x10000000) & ~0x80000000  # WS_CHILD | WS_VISIBLE, no WS_POPUP
    set_style(ctypes.c_void_p(hwnd), -16, ctypes.c_void_p(style))
    window.setGeometry(0, 0, rect.right - rect.left, rect.bottom - rect.top)
    return True


def main():
    args = [arg.lower() for arg in sys.argv[1:]]
    mode = args[0] if args else "/s"
    preview_handle = None
    if mode == "/p":
        if len(sys.argv) < 3:
            return 0
        try:
            preview_handle = int(sys.argv[2], 0)
        except ValueError:
            return 0
    elif mode not in ("/s", "/c"):
        return 0

    app = QApplication(sys.argv)
    window = MatrixDashboard(preview=mode == "/p")
    if preview_handle is not None and not embed_in_preview(window, preview_handle):
        window.close()
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
