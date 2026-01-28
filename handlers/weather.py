import aiohttp
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config import WEATHER_API_KEY, WEATHER_API_CURRENT, WEATHER_API_FORECAST
from database import get_user_profile
from keyboards import get_main_keyboard
from states import WeatherStates
from utils import logger

router = Router()


@router.message(F.text == "🌡 Погода сейчас")
async def current_weather_start(message: types.Message, state: FSMContext):
    """Начало запроса текущей погоды"""
    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile and profile[0]:
        city = profile[0]
        await get_current_weather(message, city)
    else:
        await state.set_state(WeatherStates.waiting_for_city)
        await message.answer(
            "Введи название города:",
            reply_markup=types.ReplyKeyboardRemove()
        )


@router.message(WeatherStates.waiting_for_city)
async def current_weather_get_city(message: types.Message, state: FSMContext):
    """Получение города для текущей погоды"""
    city = message.text
    await get_current_weather(message, city)
    await state.clear()


async def get_current_weather(message: types.Message, city: str):
    """Получить и отправить текущую погоду"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested current weather for {city}")

    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "aqi": "no"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_CURRENT, params=params) as response:
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


@router.message(F.text == "📅 Прогноз погоды")
async def forecast_start(message: types.Message, state: FSMContext):
    """Начало запроса прогноза"""
    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile and profile[0]:
        city = profile[0]
        days = profile[1] or 3
        await get_forecast(message, city, days)
    else:
        await state.set_state(WeatherStates.waiting_for_forecast_city)
        await message.answer(
            "Введи название города:",
            reply_markup=types.ReplyKeyboardRemove()
        )


@router.message(WeatherStates.waiting_for_forecast_city)
async def forecast_get_city(message: types.Message, state: FSMContext):
    """Получение города для прогноза"""
    city = message.text
    await state.update_data(city=city)
    await state.set_state(WeatherStates.waiting_for_forecast_days)
    await message.answer("На сколько дней прогноз? (1-14):")


@router.message(WeatherStates.waiting_for_forecast_days)
async def forecast_get_days(message: types.Message, state: FSMContext):
    """Получение количества дней для прогноза"""
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
    """Получить и отправить прогноз погоды"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested forecast for {city}, {days} days")

    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "days": days,
        "aqi": "no",
        "alerts": "no"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_FORECAST, params=params) as response:
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
                            f"   🌡 Макс: {max_temp}°C\n"
                            f"   🌡 Мин: {min_temp}°C\n"
                            f"   🌡 Средн: {avg_temp}°C\n\n"
                        )

                    await message.answer(forecast_text, parse_mode="HTML", reply_markup=get_main_keyboard())
                    logger.info(f"Successfully sent forecast to user {user_id}")
                else:
                    await message.answer("Город не найден!", reply_markup=get_main_keyboard())
                    logger.warning(f"City not found: {city}")

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=get_main_keyboard())
        logger.error(f"Error fetching forecast: {e}", exc_info=True)
