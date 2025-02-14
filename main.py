import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QInputDialog, QListWidgetItem, QTabWidget,
    QColorDialog, QFontComboBox, QComboBox, QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont


def generate_welcome_message():
    """
    Генерирует приветственное сообщение вида:
    "Рады приветствовать Вас в отеле Довиль! Сегодня <день недели>, <число> <месяц>.
     Температура воздуха от <temp_min>°C до <temp_max>°C, <описание погоды>."
    Описание погоды переводится с английского.
    """
    weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    now = datetime.now()
    weekday = weekdays[now.weekday()]
    day = now.day
    month = months[now.month]
    greeting = f"Рады приветствовать Вас в отеле Довиль! Сегодня {weekday}, {day} {month}. |"

    # Получение информации о погоде
    try:
        from pyowm import OWM
        API_KEY = "59ff4e66ae7a38fcb9a7a637165a4172"  # Замените на свой API ключ
        owm = OWM(API_KEY)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place("Anapa, RU")
        w = observation.weather
        temp_data = w.temperature("celsius")
        temp_min = temp_data.get("temp_min")
        temp_max = temp_data.get("temp_max")
        detailed_status = w.detailed_status  # Например, "clear sky"
        weather_map = {
            "clear sky": "ясно",
            "few clouds": "малооблачно",
            "scattered clouds": "рассеянные облака",
            "broken clouds": "облачно",
            "overcast clouds": "пасмурно",
            "shower rain": "ливень",
            "rain": "дождь",
            "thunderstorm": "гроза",
            "snow": "снег",
            "mist": "туман"
        }
        status_ru = weather_map.get(detailed_status.lower(), detailed_status)
        if temp_min is not None and temp_max is not None:
            weather_info = f" Температура воздуха от {temp_min:.0f}°C до {temp_max:.0f}°C, {status_ru}."
            print(weather_info)
        else:
            weather_info = ""
    except Exception as e:
        weather_info = ""
        print(e)
    return greeting + weather_info


# Класс для работы с базой данных SQLite
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("marquee.db")
        self.create_lines_table()
        self.create_settings_table()

    def create_lines_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marquee_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                position INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def create_settings_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marquee_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.conn.commit()
        defaults = {
            "bg_color": "black",
            "text_color": "white",
            "font_family": "Arial",
            "font_size": "20",
            "speed": "2"
        }
        for key, val in defaults.items():
            if self.get_setting(key) is None:
                self.set_setting(key, val)

    def get_lines(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, text FROM marquee_lines ORDER BY position ASC")
        return cursor.fetchall()

    def add_line(self, text):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(position) FROM marquee_lines")
        max_pos = cursor.fetchone()[0]
        if max_pos is None:
            max_pos = 0
        else:
            max_pos += 1
        cursor.execute("INSERT INTO marquee_lines (text, position) VALUES (?, ?)", (text, max_pos))
        self.conn.commit()
        return cursor.lastrowid

    def update_line(self, line_id, text):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE marquee_lines SET text = ? WHERE id = ?", (text, line_id))
        self.conn.commit()

    def delete_line(self, line_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM marquee_lines WHERE id = ?", (line_id,))
        self.conn.commit()
        self.reorder_lines_after_deletion()

    def reorder_lines_after_deletion(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM marquee_lines ORDER BY position ASC")
        rows = cursor.fetchall()
        for new_pos, row in enumerate(rows):
            cursor.execute("UPDATE marquee_lines SET position = ? WHERE id = ?", (new_pos, row[0]))
        self.conn.commit()

    def reorder_lines(self, id_list):
        cursor = self.conn.cursor()
        for pos, line_id in enumerate(id_list):
            cursor.execute("UPDATE marquee_lines SET position = ? WHERE id = ?", (pos, line_id))
        self.conn.commit()

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO marquee_settings (key, value)
            VALUES (?, ?)
        ''', (key, str(value)))
        self.conn.commit()

    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM marquee_settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return default


# Окно для бегущей строки с непрерывным повтором текста
class MarqueeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.text = ""  # Текст для прокрутки
        self.offset = 0  # Текущее смещение для анимации
        self.speed = 2  # Скорость прокрутки (пикселей за тик)
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


# Окно управления бегущей строкой с вкладками "Строки" и "Настройки"
class ControlWindow(QMainWindow):
    def __init__(self, db_manager, marquee_window):
        super().__init__()
        self.db_manager = db_manager
        self.marquee_window = marquee_window
        self.initUI()
        self.load_lines()
        self.update_welcome_message()
        self.schedule_midnight_update()

    def initUI(self):
        self.setWindowTitle("Управление бегущей строкой")
        self.resize(500, 400)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Вкладка "Строки"
        self.text_tab = QWidget()
        text_layout = QVBoxLayout(self.text_tab)
        self.list_widget = QListWidget()
        text_layout.addWidget(self.list_widget)
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Редактировать")
        self.btn_delete = QPushButton("Удалить")
        self.btn_up = QPushButton("Вверх")
        self.btn_down = QPushButton("Вниз")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        text_layout.addLayout(btn_layout)
        self.btn_add.clicked.connect(self.add_line)
        self.btn_edit.clicked.connect(self.edit_line)
        self.btn_delete.clicked.connect(self.delete_line)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.model().rowsMoved.connect(self.on_rows_moved)
        self.tabs.addTab(self.text_tab, "Строки")

        # Вкладка "Настройки"
        self.custom_tab = QWidget()
        custom_layout = QFormLayout(self.custom_tab)
        self.btn_bg_color = QPushButton("Выбрать цвет")
        self.btn_bg_color.clicked.connect(self.choose_bg_color)
        custom_layout.addRow("Цвет фона:", self.btn_bg_color)
        self.btn_text_color = QPushButton("Выбрать цвет")
        self.btn_text_color.clicked.connect(self.choose_text_color)
        custom_layout.addRow("Цвет текста:", self.btn_text_color)
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.change_font)
        custom_layout.addRow("Шрифт:", self.font_combo)
        self.font_size_combo = QComboBox()
        sizes = [str(s) for s in [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64]]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("20")
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        custom_layout.addRow("Размер шрифта:", self.font_size_combo)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 20)
        self.speed_spin.setValue(2)
        self.speed_spin.valueChanged.connect(self.change_speed)
        custom_layout.addRow("Скорость прокрутки:", self.speed_spin)
        self.tabs.addTab(self.custom_tab, "Настройки")

    def load_lines(self):
        self.list_widget.clear()
        lines = self.db_manager.get_lines()
        for line in lines:
            item = QListWidgetItem(line[1])
            item.setData(Qt.UserRole, line[0])
            self.list_widget.addItem(item)
        self.update_marquee()

    def update_marquee(self):
        texts = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        text = "     ".join(texts)
        self.marquee_window.set_text(text)

    def add_line(self):
        text, ok = QInputDialog.getText(self, "Добавить строку", "Введите текст:")
        if ok and text:
            line_id = self.db_manager.add_line(text)
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, line_id)
            self.list_widget.addItem(item)
            self.update_marquee()

    def edit_line(self):
        if self.list_widget.currentRow() == 0:
            return
        item = self.list_widget.currentItem()
        if item:
            current_text = item.text()
            text, ok = QInputDialog.getText(self, "Редактировать строку", "Измените текст:", text=current_text)
            if ok and text:
                item.setText(text)
                line_id = item.data(Qt.UserRole)
                self.db_manager.update_line(line_id, text)
                self.update_marquee()

    def delete_line(self):
        if self.list_widget.currentRow() == 0:
            return
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.takeItem(row)
            line_id = item.data(Qt.UserRole)
            self.db_manager.delete_line(line_id)
            self.update_marquee()

    def move_up(self):
        row = self.list_widget.currentRow()
        if row <= 0:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row - 1, item)
        self.list_widget.setCurrentRow(row - 1)
        self.save_order()

    def move_down(self):
        row = self.list_widget.currentRow()
        if row < 1 or row >= self.list_widget.count() - 1:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row + 1, item)
        self.list_widget.setCurrentRow(row + 1)
        self.save_order()

    def on_rows_moved(self, parent, start, end, destination, row):
        self.save_order()

    def save_order(self):
        id_list = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            line_id = item.data(Qt.UserRole)
            id_list.append(line_id)
        self.db_manager.reorder_lines(id_list)
        self.update_marquee()

    # Методы для настроек
    def choose_bg_color(self):
        color = QColorDialog.getColor(initial=self.marquee_window.bg_color, title="Выберите цвет фона")
        if color.isValid():
            self.marquee_window.bg_color = color
            self.marquee_window.update()
            self.btn_bg_color.setStyleSheet(f"background-color: {color.name()};")
            self.db_manager.set_setting("bg_color", color.name())

    def choose_text_color(self):
        color = QColorDialog.getColor(initial=self.marquee_window.text_color, title="Выберите цвет текста")
        if color.isValid():
            self.marquee_window.text_color = color
            self.marquee_window.update()
            self.btn_text_color.setStyleSheet(f"background-color: {color.name()};")
            self.db_manager.set_setting("text_color", color.name())

    def change_font(self, font):
        current_size = self.marquee_window.font.pointSize()
        self.marquee_window.font = QFont(font.family(), current_size)
        self.marquee_window.update()
        self.db_manager.set_setting("font_family", font.family())

    def change_font_size(self, size_str):
        try:
            size = int(size_str)
            current_font = self.marquee_window.font.family()
            self.marquee_window.font = QFont(current_font, size)
            self.marquee_window.update()
            self.db_manager.set_setting("font_size", size)
        except ValueError:
            pass

    def change_speed(self, speed):
        self.marquee_window.speed = speed
        self.db_manager.set_setting("speed", speed)

    # Методы для приветственной строки
    def update_welcome_message(self):
        msg = generate_welcome_message()
        if self.list_widget.count() == 0:
            line_id = self.db_manager.add_line(msg)
            item = QListWidgetItem(msg)
            item.setData(Qt.UserRole, line_id)
            self.list_widget.insertItem(0, item)
        else:
            first_item = self.list_widget.item(0)
            first_item.setText(msg)
            self.db_manager.update_line(first_item.data(Qt.UserRole), msg)
        self.update_marquee()

    def schedule_midnight_update(self):
        now = datetime.now()
        tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        ms_until_midnight = int((tomorrow - now).total_seconds() * 1000)
        QTimer.singleShot(ms_until_midnight, self.midnight_update)

    def midnight_update(self):
        self.update_welcome_message()
        self.schedule_midnight_update()


def main():
    app = QApplication(sys.argv)
    db_manager = DatabaseManager()
    marquee_window = MarqueeWindow()
    # Загрузка настроек из БД
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
