from aiogram import Router, types, F
from aiogram.filters import Command

from database import get_user_profile, save_user_profile
from keyboards import get_main_keyboard
from utils import logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} started the bot")

    profile = get_user_profile(user_id)
    if not profile:
        save_user_profile(user_id, city=None, days=3)

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я помогу тебе узнать погоду.\n\n"
        "Выбери действие:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: types.Message):
    """Обработчик кнопки помощи"""
    await message.answer(
        "🤖 <b>Как пользоваться ботом:</b>\n\n"
        "🌡 <b>Погода сейчас</b> - текущая температура\n"
        "📅 <b>Прогноз погоды</b> - прогноз на несколько дней\n"
        "👤 <b>Мой профиль</b> - настрой город и количество дней по умолчанию\n\n"
        "<b>Совет:</b> Настрой профиль, и бот будет автоматически показывать погоду для твоего города!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    """Возврат в главное меню"""
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())
