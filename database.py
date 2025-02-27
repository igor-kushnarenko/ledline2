import sqlite3

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("marquee.db")
        self.create_lines_table()
        self.create_settings_table()
        self.create_schedule_table()  # Новый метод для создания таблицы расписания

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

    def create_schedule_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week INTEGER,   -- 1 или 2 для номера недели
                day INTEGER,    -- 1 to 7 для дня недели
                event_name TEXT,
                event_time TEXT, -- формата HH:MM
                location TEXT    -- место проведения
            )
        ''')
        self.conn.commit()

    def add_event(self, week, day, event_name, event_time, location):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO schedule (week, day, event_name, event_time, location) VALUES (?, ?, ?, ?, ?)",
                       (week, day, event_name, event_time, location))
        self.conn.commit()

    def get_events_for_week_day(self, week, day):
        cursor = self.conn.cursor()
        cursor.execute("SELECT event_name, event_time, location, id FROM schedule WHERE week = ? AND day = ? ORDER BY event_time",
                       (week, day))
        return cursor.fetchall()

    def update_event(self, event_id, event_name, event_time, location):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE schedule SET event_name = ?, event_time = ?, location = ? WHERE id = ?",
                       (event_name, event_time, location, event_id))
        self.conn.commit()

    def delete_event(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM schedule WHERE id = ?", (event_id,))
        self.conn.commit()

    # остальные методы

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