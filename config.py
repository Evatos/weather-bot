import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

WEATHER_API_BASE_URL = "http://api.weatherapi.com/v1"
WEATHER_API_CURRENT = f"{WEATHER_API_BASE_URL}/current.json"
WEATHER_API_FORECAST = f"{WEATHER_API_BASE_URL}/forecast.json"

DATABASE_NAME = "weather_bot.db"

LOG_FILE = "bot.log"
LOG_LEVEL = "INFO"
