from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont

class MarqueeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.text = ""  # Текст для прокрутки
        self.offset = 5  # Текущее смещение для анимации
        self.speed = 5  # Скорость прокрутки (пикселей за тик)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(30)  # 30 мс интервал обновления

    def initUI(self):
        screens = QApplication.screens()
        screen = screens[1] if len(screens) > 1 else screens[0]
        geometry = screen.geometry()
        self.screen_width = geometry.width()
        self.screen_height = geometry.height()
        self.setGeometry(geometry.x(), geometry.y(), self.screen_width, int(self.screen_height * 0.1))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.bg_color = QColor("black")
        self.text_color = QColor("white")
        self.font = QFont("Arial", 20)
        self.dragPos = None

    def set_text(self, text):
        self.text = text
        self.offset = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        painter.setPen(self.text_color)
        painter.setFont(self.font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(self.text) if hasattr(fm, "horizontalAdvance") else fm.width(self.text)
        if text_width == 0:
            return
        offset = self.offset % text_width
        x = -offset
        y = (self.height() + fm.ascent() - fm.descent()) // 2
        while x < self.width():
            painter.drawText(x, y, self.text)
            x += text_width

    def update_position(self):
        self.offset += self.speed
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPos)
            event.accept()