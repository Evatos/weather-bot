import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BotCommand

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="current", description="Узнать погоду на сегодня"),
        BotCommand(command="forecast", description="Узнать прогноз погоды"),
        BotCommand(command="help", description="Помощь")
    ]

    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Этот бот поможет тебе узнать температуру в любом городе мира!\n"
        "Для начала просто напиши /current {город}\n"
        "Или /forecast {город} {количество дней}"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Ты чё? не смог осилить 2 команды? чел, ты..."
    )

@dp.message(Command("current"))
async def cmd_weather(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("Укажите город!")
        return

    city = command.args

    url = f"http://api.weatherapi.com/v1/current.json"
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
                    last_updated = data["current"]["last_updated"]

                    weather_text = (
                        f"<b>{location}, {country}</b>\n\n"
                        f"Температура: <b>{temp_c}</b>\n"
                        f"Обновлено: <b>{last_updated}</b>"
                    )

                    await message.answer(weather_text, parse_mode="HTML")
                else:
                    await message.answer("Город не найден!")
    except Exception as e:
        await message.answer(f"Error: {str(e)}")

@dp.message(Command("forecast"))
async def cmd_forecast(message: types.Message, command: CommandObject):

    if not command.args:
        await message.answer(
            "Укажи город и количество дней!\n"
            "Например /forecast London 3"
        )

    args = command.args.split()

    if len(args) < 2:
        await message.answer("Укажи город и количество дней")
        return

    city = args[0]

    try:
        days = int(args[1])
        if days < 1 or days > 14:
            await message.answer("Количество дней должно быть от 1 до 14!")
    except ValueError:
        await message.answer("Количество дней должно быть числом!")
        return

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

                    forecast_text = f"<b>{location}, {country}</b>\n"
                    forecast_text += f"Прогноз на {days} дн.\n\n"

                    for day_data in forecast_days:
                        date = day_data["date"]
                        max_temp = day_data["day"]["maxtemp_c"]
                        min_temp = day_data["day"]["mintemp_c"]
                        avg_temp = day_data["day"]["avgtemp_c"]


                        forecast_text += (
                            f"<b>{date}</b>\n"
                            f"Максимальная температура: <b>{max_temp}</b>\n"
                            f"Минимальная температура: <b>{min_temp}</b>\n"
                            f"Средняя температура: <b>{avg_temp}</b>\n\n"
                        )

                    await message.answer(forecast_text, parse_mode="HTML")
                else:
                    await message.answer("Город не найден!")
    except Exception as e:
        await message.answer(f"Error: {str(e)}")

async def main():
    await set_commands(bot)

    print("Bot is active")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())