from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QInputDialog, \
    QListWidgetItem, QTabWidget, QColorDialog, QFontComboBox, QComboBox, QSpinBox, QFormLayout, QTableWidget, \
    QTableWidgetItem
from PyQt5.QtCore import Qt, QTimer

from datetime import datetime, timedelta

from utils import generate_welcome_message

class ControlWindow(QMainWindow):
    def __init__(self, db_manager, marquee_window):
        super().__init__()
        self.db_manager = db_manager
        self.marquee_window = marquee_window
        self.initUI()
        self.load_lines()
        self.update_welcome_message()
        self.schedule_midnight_update()
        self.setup_hourly_update()
        self.apply_dark_theme()

    def initUI(self):
        self.setWindowTitle("Управление бегущей строкой")
        self.resize(1000, 800)
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

        # Вкладка "Расписание"
        self.schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(self.schedule_tab)

        self.table = QTableWidget(14, 5)  # Теперь 4 столбца с добавлением места проведения
        self.table.setHorizontalHeaderLabels(['Неделя', 'День', 'Мероприятие', 'Время', 'Место'])
        schedule_layout.addWidget(self.table)

        # Кнопки для работы с расписанием
        buttons_layout = QHBoxLayout()
        self.btn_add_event = QPushButton("Добавить мероприятие")
        self.btn_edit_event = QPushButton("Редактировать")
        self.btn_delete_event = QPushButton("Удалить")
        self.btn_form_schedule = QPushButton("Сформировать")
        buttons_layout.addWidget(self.btn_add_event)
        buttons_layout.addWidget(self.btn_edit_event)
        buttons_layout.addWidget(self.btn_delete_event)
        buttons_layout.addWidget(self.btn_form_schedule)
        schedule_layout.addLayout(buttons_layout)

        self.btn_add_event.clicked.connect(self.add_event)
        self.btn_edit_event.clicked.connect(self.edit_event)
        self.btn_delete_event.clicked.connect(self.delete_event)
        self.btn_form_schedule.clicked.connect(self.form_schedule)

        self.tabs.addTab(self.schedule_tab, "Расписание")

        self.load_schedule()

    def load_schedule(self):
        self.table.setRowCount(0)  # Очищаем таблицу перед загрузкой новых данных
        row = 0
        days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        for week in range(1, 3):
            for day in range(1, 8):
                events = self.db_manager.get_events_for_week_day(week, day)
                if events:  # Если есть события для этого дня
                    # Добавляем заголовок дня
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(f"{week}"))
                    self.table.setItem(row, 1, QTableWidgetItem(days_of_week[day - 1]))
                    row += 1
                    # Добавляем события
                    for event_name, event_time, location, event_id in sorted(events, key=lambda x: x[1]):
                        self.table.insertRow(row)
                        self.table.setItem(row, 2, QTableWidgetItem(event_name))
                        self.table.setItem(row, 3, QTableWidgetItem(event_time))
                        self.table.setItem(row, 4, QTableWidgetItem(location))
                        self.table.item(row, 2).setData(Qt.UserRole, event_id)  # Сохраняем ID события
                        row += 1
                else:  # Если нет событий, добавляем пустую строку
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(f"{week}"))
                    self.table.setItem(row, 1, QTableWidgetItem(days_of_week[day - 1]))
                    row += 1

    def add_event(self):
        week, ok = QInputDialog.getItem(self, "Неделя", "Выберите неделю:", ["1", "2"], 0, False)
        if not ok:
            return
        day, ok = QInputDialog.getItem(self, "День", "Выберите день недели:", ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"], 0, False)
        if not ok:
            return
        day = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"].index(day) + 1
        event_name, ok = QInputDialog.getText(self, "Мероприятие", "Введите название мероприятия:")
        if not ok:
            return
        hour, ok = QInputDialog.getItem(self, "Час", "Выберите час:", [str(h).zfill(2) for h in range(24)], 0, False)
        if not ok:
            return
        minute, ok = QInputDialog.getItem(self, "Минута", "Выберите минуту:", [str(m).zfill(2) for m in range(0, 60, 5)], 0, False)
        if not ok:
            return
        event_time = f"{hour}:{minute}"
        location, ok = QInputDialog.getText(self, "Место", "Введите место проведения:")
        if not ok:
            return
        self.db_manager.add_event(int(week), day, event_name, event_time, location)
        self.load_schedule()

    def edit_event(self):
        current_row = self.table.currentRow()
        if current_row == -1:
            return
        event_id = self.table.item(current_row, 2).data(Qt.UserRole)
        if event_id is None:
            return
        new_name, ok = QInputDialog.getText(self, "Редактировать мероприятие", "Новое название:", text=self.table.item(current_row, 2).text())
        if not ok:
            return
        new_time, ok = QInputDialog.getText(self, "Редактировать время", "Новое время (формат: HH:MM):", text=self.table.item(current_row, 3).text())
        if not ok:
            return
        new_location, ok = QInputDialog.getText(self, "Редактировать место", "Новое место проведения:", text=self.table.item(current_row, 4).text())
        if not ok:
            return
        self.db_manager.update_event(event_id, new_name, new_time, new_location)
        self.load_schedule()

    def delete_event(self):
        current_row = self.table.currentRow()
        if current_row == -1:
            return
        event_id = self.table.item(current_row, 2).data(Qt.UserRole)
        if event_id:
            self.db_manager.delete_event(event_id)
            self.load_schedule()

    def form_schedule(self):
        today = datetime.now()
        current_week = 1 if today.weekday() < 7 else 2  # Определяем текущую неделю в 2-недельном цикле
        current_day = today.weekday() + 1  # День недели от 1 до 7
        events = self.db_manager.get_events_for_week_day(current_week, current_day)
        message = "🎉 Сегодня в программе: "
        formatted_events = self.filter_current_events(events)
        message += " ".join(formatted_events)
        self.update_schedule_message_in_marquee(message)

    def filter_current_events(self, events):
        now = datetime.now()
        current_time = now.time()
        return [f"{event[0]} - {event[1]}, {event[2]} | " for event in events if datetime.strptime(event[1], "%H:%M").time() >= current_time]


    def update_schedule_message_in_marquee(self, message):
        # Ищем строку с расписанием среди текущих строк
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if "Сегодня в программе:" in item.text():
                item.setText(message)
                self.db_manager.update_line(item.data(Qt.UserRole), message)
                self.update_marquee()
                return
        # Если строка не найдена, добавляем новую
        line_id = self.db_manager.add_line(message)
        item = QListWidgetItem(message)
        item.setData(Qt.UserRole, line_id)
        self.list_widget.addItem(item)
        self.update_marquee()

    def setup_hourly_update(self):
        self.hourly_timer = QTimer(self)
        self.hourly_timer.timeout.connect(self.form_schedule)
        self.hourly_timer.start(3600000)  # 1 час в миллисекундах

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

    def apply_dark_theme(self):
        # Определяем стиль для тёмной темы
        dark_stylesheet = """
        QMainWindow {
            background-color: #333333;
        }
        QWidget {
            color: #ffffff;
            background-color: #444444;
        }
        QPushButton {
            background-color: #555555;
            border: 1px solid #666666;
            padding: 5px;
            color: #ffffff;
            border-radius: 5px; /* Скругление углов кнопок */
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QPushButton:pressed {
            background-color: #777777;
        }
        QTabWidget::pane {
            border: 1px solid #666666;
            background-color: #333333;
        }
        QTabBar::tab {
            background-color: #555555;
            color: #ffffff;
            border: 1px solid #666666;
            padding: 5px;
        }
        QTabBar::tab:selected {
            background-color: #444444;
        }
        QListWidget {
            background-color: #333333;
            border: 1px solid #666666;
        }
        QListWidget::item {
            color: #ffffff;
        }
        QListWidget::item:selected {
            background-color: #555555;
        }
        QTableWidget {
            background-color: #333333;
            color: #ffffff;
            gridline-color: #666666;
        }
        QTableWidget::item {
            background-color: #444444;
        }
        QTableWidget::item:selected {
            background-color: #555555;
        }
        QComboBox, QSpinBox, QFontComboBox {
            background-color: #444444;
            color: #ffffff;
            border: 1px solid #666666;
        }
        QHeaderView::section {
            background-color: #555555; /* Фон заголовков таблицы */
            color: #ffffff; /* Цвет текста заголовков */
            border: 1px solid #666666;
            padding: 4px;
        }
        """
        # Применяем стиль к главному окну
        self.setStyleSheet(dark_stylesheet)
        # Убедимся, что заголовки таблицы видны
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #555555; color: #ffffff; }")


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