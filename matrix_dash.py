import random
import sys
import time

from PySide6.QtCore import QEvent, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


class MatrixDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matrix Dashboard")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setCursor(Qt.BlankCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self.font_size = 16
        self.matrix_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.drops = []
        self.stream_lengths = []
        self.last_mouse_position = None
        self.title_text = "SYSTEM DASHBOARD"
        self.todo_list = [
            "1. 深度优化底层算力模型 (开会摸鱼)",
            "2. 清理系统多余缓存数据 (倒杯咖啡)",
            "3. 部署自动化运行脚本 (准备下班)",
        ]

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(80)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update)
        self.clock_timer.start(1000)

        # Set up all state before showing the window; showFullScreen can emit resizeEvent.
        self.showFullScreen()

    def resizeEvent(self, event):
        columns = max(1, self.width() // self.font_size + 1)
        self.drops = [random.randint(-self.height() // self.font_size, 0) for _ in range(columns)]
        self.stream_lengths = [random.randint(8, 28) for _ in range(columns)]
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        self.close()

    def mousePressEvent(self, event):
        self.close()

    def mouseMoveEvent(self, event):
        position = event.position().toPoint()
        if self.last_mouse_position is not None and position != self.last_mouse_position:
            self.close()
        self.last_mouse_position = position

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            self.close()
        return super().event(event)

    def day_progress(self):
        now = time.localtime()
        seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        return seconds / (24 * 60 * 60)

    def draw_matrix(self, painter):
        painter.setFont(QFont("Consolas", self.font_size))
        for column, drop in enumerate(self.drops):
            x = column * self.font_size
            for offset in range(self.stream_lengths[column]):
                row = drop - offset
                y = row * self.font_size
                if -self.font_size <= y <= self.height():
                    painter.setPen(QColor("#FFFFFF" if offset == 0 else "#00FF00"))
                    painter.drawText(QPointF(x, y), random.choice(self.matrix_chars))

            if drop * self.font_size > self.height() and random.random() > 0.975:
                self.drops[column] = random.randint(-20, 0)
                self.stream_lengths[column] = random.randint(8, 28)
            else:
                self.drops[column] += 1

    def draw_dashboard(self, painter):
        cx, cy = self.width() // 2, self.height() // 2
        green = QColor("#00FF00")
        painter.setPen(QPen(green, 2))
        painter.setBrush(QColor(0, 0, 0, 220))
        painter.drawRect(cx - 280, cy - 160, 560, 320)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(green)
        painter.setFont(QFont("Consolas", 24, QFont.Bold))
        painter.drawText(QPointF(cx - 150, cy - 120), self.title_text)

        painter.setFont(QFont("Consolas", 14))
        painter.drawText(QPointF(cx - 150, cy - 70), time.strftime("TIME: %Y-%m-%d %H:%M:%S"))

        painter.setFont(QFont("Consolas", 12))
        progress = self.day_progress()
        painter.setPen(green)
        painter.drawText(QPointF(cx - 230, cy - 35), "DAY PROGRESS")

        # Draw a geometric bar instead of block characters, whose glyph heights
        # can differ between installed fonts.
        bar_x, bar_y, bar_width, bar_height = cx - 120, cy - 49, 260, 16
        painter.setPen(QPen(QColor("#006600"), 1))
        painter.setBrush(QColor("#001A00"))
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(green)
        painter.drawRect(bar_x + 1, bar_y + 1, max(0, int((bar_width - 2) * progress)), bar_height - 2)

        painter.setPen(green)
        painter.drawText(QPointF(cx + 150, cy - 35), f"{progress * 100:.2f}%")

        painter.setPen(QPen(green, 1, Qt.DashLine))
        painter.drawLine(cx - 240, cy, cx + 240, cy)
        painter.setPen(green)
        painter.setFont(QFont("Microsoft YaHei", 12))
        for index, item in enumerate(self.todo_list):
            painter.drawText(QPointF(cx - 230, cy + 55 + index * 30), item)

        painter.setFont(QFont("Consolas", 10))
        painter.drawText(QPointF(cx - 120, cy + 140), "PRESS ANY KEY TO EXIT")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))
        self.draw_matrix(painter)
        self.draw_dashboard(painter)
        painter.end()


def main():
    argument = sys.argv[1].lower() if len(sys.argv) > 1 else "/s"
    if argument not in ("/s", "/c") and not argument.startswith("/p"):
        return 0

    app = QApplication(sys.argv)
    window = MatrixDashboard()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
