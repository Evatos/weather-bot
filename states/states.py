from aiogram.fsm.state import State, StatesGroup


class WeatherStates(StatesGroup):
    """Состояния для FSM бота погоды"""
    waiting_for_city = State()
    waiting_for_forecast_city = State()
    waiting_for_forecast_days = State()
    waiting_for_profile_city = State()
    waiting_for_profile_days = State()
