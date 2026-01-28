from aiogram import Dispatcher
from . import start, weather, profile


def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    dp.include_router(start.router)
    dp.include_router(weather.router)
    dp.include_router(profile.router)
