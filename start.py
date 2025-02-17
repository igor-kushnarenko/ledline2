import sys

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QApplication
from database import DatabaseManager
from marquee_window import MarqueeWindow
from control_window import ControlWindow


def main():
    app = QApplication(sys.argv)
    db_manager = DatabaseManager()

    # Инициализация MarqueeWindow с настройками из базы данных
    marquee_window = MarqueeWindow()
    # Здесь вы будете применять настройки, такие как шрифт, цвета, скорость из базы данных
    bg = db_manager.get_setting("bg_color", "black")
    marquee_window.bg_color = QColor(bg)
    text_color = db_manager.get_setting("text_color", "white")
    marquee_window.text_color = QColor(text_color)
    font_family = db_manager.get_setting("font_family", "Arial")
    font_size = int(db_manager.get_setting("font_size", "20"))
    marquee_window.font = QFont(font_family, font_size)
    marquee_window.speed = int(db_manager.get_setting("speed", "2"))
    marquee_window.show()
    control_window = ControlWindow(db_manager, marquee_window)
    control_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()