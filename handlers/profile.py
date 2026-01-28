from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from database import get_user_profile, save_user_profile
from keyboards import get_main_keyboard, get_profile_keyboard
from states import WeatherStates
from utils import logger

router = Router()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    """Показать профиль пользователя"""
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


@router.message(F.text == "📍 Изменить город")
async def change_city_start(message: types.Message, state: FSMContext):
    """Начать изменение города"""
    await state.set_state(WeatherStates.waiting_for_profile_city)
    await message.answer(
        "Введи название города по умолчанию:",
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(WeatherStates.waiting_for_profile_city)
async def change_city_save(message: types.Message, state: FSMContext):
    """Сохранить новый город"""
    city = message.text
    user_id = message.from_user.id

    save_user_profile(user_id, city=city)

    await message.answer(
        f"✅ Город по умолчанию изменён на: <b>{city}</b>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await state.clear()


@router.message(F.text == "📊 Изменить количество дней")
async def change_days_start(message: types.Message, state: FSMContext):
    """Начать изменение количества дней"""
    await state.set_state(WeatherStates.waiting_for_profile_days)
    await message.answer(
        "Сколько дней показывать в прогнозе? (1-14):",
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(WeatherStates.waiting_for_profile_days)
async def change_days_save(message: types.Message, state: FSMContext):
    """Сохранить новое количество дней"""
    try:
        days = int(message.text)
        if days < 1 or days > 14:
            await message.answer("Количество дней должно быть от 1 до 14!")
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
