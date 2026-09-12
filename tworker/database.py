# tworker/database.py
import sqlite3
import os
from datetime import datetime
from settings import settings

# --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
# Определяем абсолютный путь к папке, где находится этот файл
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Создаем полный путь к файлу базы данных
DB_PATH = os.path.join(BASE_DIR, 'workers.db')

def init_db():
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- Таблица воркеров ---
    try:
        # Добавляем колонку роли, если ее нет
        cursor.execute("ALTER TABLE workers ADD COLUMN role TEXT DEFAULT 'worker'")
    except sqlite3.OperationalError:
        pass # Колонка уже существует
    
    try:
        # Убедимся, что колонка join_date существует
        cursor.execute("ALTER TABLE workers ADD COLUMN join_date TEXT")
    except sqlite3.OperationalError:
        pass # Колонка уже существует

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            status TEXT DEFAULT 'worker',
            join_date TEXT,
            role TEXT DEFAULT 'worker'
        )
    ''')
    
    # --- Таблица для настроек ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # --- Инициализация настроек по умолчанию ---
    # Устанавливаем режим вывода по умолчанию "авто"
    cursor.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)", ('withdrawal_mode', 'auto'))
    # Назначаем роль администратора супер-админу
    cursor.execute("UPDATE workers SET role = 'admin' WHERE user_id = ?", (settings.bot.super_admin_id,))
    
    conn.commit()
    conn.close()

def set_setting(key: str, value: str):
    """Устанавливает значение для ключа в настройках."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = None) -> str:
    """Получает значение ключа из настроек."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM workers WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    # Супер-админ всегда является админом
    if user_id == settings.bot.super_admin_id:
        return True
    return result[0] == 'admin' if result else False

def add_worker(user_id: int, username: str, first_name: str):
    """Добавляет нового воркера или обновляет существующего."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Проверяем, есть ли уже такой воркер
    cursor.execute("SELECT join_date, role FROM workers WHERE user_id = ?", (user_id,))
    existing_worker = cursor.fetchone()
    
    if existing_worker:
        # Если воркер есть, обновляем только имя и никнейм, сохраняя дату и роль
        join_date_to_use = existing_worker[0] or join_date
        role_to_use = existing_worker[1] or 'worker'
        cursor.execute(
            """UPDATE workers SET username = ?, first_name = ?, join_date = ?, role = ?
               WHERE user_id = ?""",
            (username, first_name, join_date_to_use, role_to_use, user_id)
        )
    else:
        # Если воркера нет, создаем новую запись
        cursor.execute(
            """INSERT INTO workers (user_id, username, first_name, join_date, role) 
               VALUES (?, ?, ?, ?, 'worker')""",
            (user_id, username, first_name, join_date)
        )
    
    conn.commit()
    conn.close()

def is_worker(user_id: int) -> bool:
    """Проверяет, является ли пользователь воркером."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM workers WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_worker_data(user_id: int):
    """Получает данные воркера по его ID."""
    # Используем абсолютный путь
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, join_date FROM workers WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data