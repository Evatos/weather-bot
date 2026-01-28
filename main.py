import asyncio
import aiohttp
import os
import sqlite3
import logging
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ============= База данных =============
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('weather_bot.db')
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


def get_user_profile(user_id):
    """Получить профиль пользователя"""
    conn = sqlite3.connect('weather_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT default_city, default_days FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def save_user_profile(user_id, city=None, days=None):
    """Сохранить или обновить профиль"""
    conn = sqlite3.connect('weather_bot.db')
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


# ============= Состояния =============
class WeatherStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_forecast_city = State()
    waiting_for_forecast_days = State()
    waiting_for_profile_city = State()
    waiting_for_profile_days = State()


# ============= Клавиатуры =============
def get_main_keyboard():
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
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Изменить город")],
            [KeyboardButton(text="📊 Изменить количество дней")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard


# ============= Команды =============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} started the bot")

    # Создаём профиль если не существует
    profile = get_user_profile(user_id)
    if not profile:
        save_user_profile(user_id, city=None, days=3)

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я помогу тебе узнать погоду.\n\n"
        "Выбери действие:",
        reply_markup=get_main_keyboard()
    )


# ============= Текущая погода =============
@dp.message(F.text == "🌡 Погода сейчас")
async def current_weather_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile and profile[0]:  # Если есть сохранённый город
        city = profile[0]
        await get_current_weather(message, city)
    else:
        await state.set_state(WeatherStates.waiting_for_city)
        await message.answer(
            "Введи название города:",
            reply_markup=types.ReplyKeyboardRemove()
        )


@dp.message(WeatherStates.waiting_for_city)
async def current_weather_get_city(message: types.Message, state: FSMContext):
    city = message.text
    await get_current_weather(message, city)
    await state.clear()


async def get_current_weather(message: types.Message, city: str):
    """Получить текущую погоду"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested current weather for {city}")

    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "aqi": "no"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    location = data["location"]["name"]
                    country = data["location"]["country"]
                    temp_c = data["current"]["temp_c"]
                    temp_f = data["current"]["temp_f"]

                    weather_text = (
                        f"🌍 <b>{location}, {country}</b>\n\n"
                        f"🌡 Температура: {temp_c}°C ({temp_f}°F)"
                    )

                    await message.answer(weather_text, parse_mode="HTML", reply_markup=get_main_keyboard())
                    logger.info(f"Successfully sent weather for {city} to user {user_id}")
                else:
                    await message.answer("Город не найден! Попробуй ещё раз.", reply_markup=get_main_keyboard())
                    logger.warning(f"City not found: {city}")

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_main_keyboard())
        logger.error(f"Error fetching weather: {e}", exc_info=True)


# ============= Прогноз погоды =============
@dp.message(F.text == "📅 Прогноз погоды")
async def forecast_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile and profile[0]:  # Если есть сохранённые настройки
        city = profile[0]
        days = profile[1] or 3
        await get_forecast(message, city, days)
    else:
        await state.set_state(WeatherStates.waiting_for_forecast_city)
        await message.answer(
            "Введи название города:",
            reply_markup=types.ReplyKeyboardRemove()
        )


@dp.message(WeatherStates.waiting_for_forecast_city)
async def forecast_get_city(message: types.Message, state: FSMContext):
    city = message.text
    await state.update_data(city=city)
    await state.set_state(WeatherStates.waiting_for_forecast_days)
    await message.answer("На сколько дней прогноз? (1-10):")


@dp.message(WeatherStates.waiting_for_forecast_days)
async def forecast_get_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days < 1 or days > 10:
            await message.answer("Количество дней должно быть от 1 до 10!")
            return
    except ValueError:
        await message.answer("Введи число!")
        return

    data = await state.get_data()
    city = data['city']

    await get_forecast(message, city, days)
    await state.clear()


async def get_forecast(message: types.Message, city: str, days: int):
    """Получить прогноз погоды"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested forecast for {city}, {days} days")

    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "days": days,
        "aqi": "no",
        "alerts": "no"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    location = data["location"]["name"]
                    country = data["location"]["country"]
                    forecast_days = data["forecast"]["forecastday"]

                    forecast_text = f"🌍 <b>{location}, {country}</b>\n"
                    forecast_text += f"📅 Прогноз на {days} дн.:\n\n"

                    for day_data in forecast_days:
                        date = day_data["date"]
                        max_temp = day_data["day"]["maxtemp_c"]
                        min_temp = day_data["day"]["mintemp_c"]
                        avg_temp = day_data["day"]["avgtemp_c"]

                        forecast_text += (
                            f"📆 <b>{date}</b>\n"
                            f"   🌡 Макс: {max_temp}°C | Мин: {min_temp}°C | Средн: {avg_temp}°C\n\n"
                        )

                    await message.answer(forecast_text, parse_mode="HTML", reply_markup=get_main_keyboard())
                    logger.info(f"Successfully sent forecast to user {user_id}")
                else:
                    await message.answer("Город не найден!", reply_markup=get_main_keyboard())
                    logger.warning(f"City not found: {city}")

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_main_keyboard())
        logger.error(f"Error fetching forecast: {e}", exc_info=True)


# ============= Профиль =============
@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile:
        city = profile[0] or "не указан"
        days = profile[1] or 3

        profile_text = (
            f"👤 <b>Твой профиль</b>\n\n"
            f"📍 Город по умолчанию: <b>{city}</b>\n"
            f"📊 Дней в прогнозе: <b>{days}</b>\n\n"
            f"Теперь при запросе погоды будут использоваться эти настройки!\n"
            f"Ты можешь изменить их в любой момент."
        )
    else:
        profile_text = "У тебя ещё нет сохранённого профиля."

    await message.answer(profile_text, parse_mode="HTML", reply_markup=get_profile_keyboard())


@dp.message(F.text == "📍 Изменить город")
async def change_city_start(message: types.Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting_for_profile_city)
    await message.answer(
        "Введи название города по умолчанию:",
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message(WeatherStates.waiting_for_profile_city)
async def change_city_save(message: types.Message, state: FSMContext):
    city = message.text
    user_id = message.from_user.id

    save_user_profile(user_id, city=city)

    await message.answer(
        f"✅ Город по умолчанию изменён на: <b>{city}</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await state.clear()


@dp.message(F.text == "📊 Изменить количество дней")
async def change_days_start(message: types.Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting_for_profile_days)
    await message.answer(
        "Сколько дней показывать в прогнозе? (1-10):",
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message(WeatherStates.waiting_for_profile_days)
async def change_days_save(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days < 1 or days > 10:
            await message.answer("Количество дней должно быть от 1 до 10!")
            return

        user_id = message.from_user.id
        save_user_profile(user_id, days=days)

        await message.answer(
            f"✅ Количество дней изменено на: <b>{days}</b>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

    except ValueError:
        await message.answer("Введи число!")


@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())


# ============= Помощь =============
@dp.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: types.Message):
    await message.answer(
        "🤖 <b>Как пользоваться ботом:</b>\n\n"
        "🌡 <b>Погода сейчас</b> - текущая температура\n"
        "📅 <b>Прогноз погоды</b> - прогноз на несколько дней\n"
        "👤 <b>Мой профиль</b> - настрой город и количество дней по умолчанию\n\n"
        "<b>Совет:</b> Настрой профиль, и бот будет автоматически показывать погоду для твоего города!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


# ============= Запуск =============
async def main():
    init_db()
    logger.info("Bot started!")
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
