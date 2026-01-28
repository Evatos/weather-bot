from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌡 Погода сейчас")],
            [KeyboardButton(text="📅 Прогноз погоды")],
            [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_profile_keyboard():
    """Меню настройки профиля"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Изменить город")],
            [KeyboardButton(text="📊 Изменить количество дней")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard
