import sqlite3
from config import DATABASE_NAME
from utils import logger


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            default_city TEXT,
            default_days INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def get_user_profile(user_id: int) -> tuple | None:
    """
    Получить профиль пользователя

    Args:
        user_id: ID пользователя в Telegram

    Returns:
        Tuple (default_city, default_days) или None
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT default_city, default_days FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def save_user_profile(user_id: int, city: str = None, days: int = None):
    """
    Сохранить или обновить профиль пользователя

    Args:
        user_id: ID пользователя
        city: Город по умолчанию
        days: Количество дней для прогноза
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Проверяем существует ли пользователь
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()

    if exists:
        if city:
            cursor.execute('UPDATE users SET default_city = ? WHERE user_id = ?', (city, user_id))
        if days:
            cursor.execute('UPDATE users SET default_days = ? WHERE user_id = ?', (days, user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, default_city, default_days) VALUES (?, ?, ?)',
                       (user_id, city, days or 3))

    conn.commit()
    conn.close()
    logger.info(f"Profile saved for user {user_id}: city={city}, days={days}")
