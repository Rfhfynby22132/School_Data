import sqlite3
from config import DATABASE

class Data1:
    def __init__(self, database):
        self.database = database
        self.create_table()

    def create_table(self):
        """Создаёт таблицу movie, если её нет"""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS movie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class TEXT,
                    day TEXT,
                    time TEXT,
                    lessons TEXT
                )
            """)
        conn.close()

    def _execute(self, sql, params=()):
        """Выполняет один запрос (INSERT, UPDATE, DELETE)"""
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(sql, params)
        conn.close()

    def _fetchall(self, sql, params=()):
        """Выполняет SELECT и возвращает все строки"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    # ---------- УЧЕНИКИ ----------
    def get_all_schedule(self):
        """Возвращает всё расписание"""
        return self._fetchall("SELECT * FROM movie ORDER BY day, time")

    def get_schedule_by_day(self, day):
        """Возвращает расписание на конкретный день (например, 'Понедельник')"""
        return self._fetchall("SELECT * FROM movie WHERE day = ? ORDER BY time", (day,))

    # ---------- УЧИТЕЛЯ ----------
    def add_schedule_entry(self, class_name, day, time, lessons):
        """Добавляет новый урок"""
        try:
            sql = "INSERT INTO movie (class, day, time, lessons) VALUES (?, ?, ?, ?)"
            self._execute(sql, (class_name, day, time, lessons))
            return True, f"✅ Урок добавлен: {class_name}, {day}, {time}, {lessons}"
        except Exception as e:
            return False, f"❌ Ошибка БД: {e}"

    def edit_schedule_entry(self, entry_id, new_class, new_day, new_time, new_lessons):
        """Редактирует существующий урок по id"""
        try:
            sql = "UPDATE movie SET class=?, day=?, time=?, lessons=? WHERE id=?"
            self._execute(sql, (new_class, new_day, new_time, new_lessons, entry_id))
            return True, f"✅ Урок с id {entry_id} обновлён"
        except Exception as e:
            return False, f"❌ Ошибка при редактировании: {e}"

    def delete_schedule_entry(self, entry_id):
        """Удаляет урок по id"""
        try:
            self._execute("DELETE FROM movie WHERE id=?", (entry_id,))
            return True, f"✅ Урок с id {entry_id} удалён"
        except Exception as e:
            return False, f"❌ Ошибка удаления: {e}"

    def get_schedule_by_class_day_time(self, class_name, day, time):
        """Ищет урок для проверки перед редактированием"""
        rows = self._fetchall(
            "SELECT * FROM movie WHERE class=? AND day=? AND time=?",
            (class_name, day, time)
        )
        return rows[0] if rows else None

    # ---------- ДЛЯ АВТООБНОВЛЕНИЯ (пример) ----------
    def clear_all_schedule(self):
        """Очищает всё расписание (используется при обновлении)"""
        self._execute("DELETE FROM movie")