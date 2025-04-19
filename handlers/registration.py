import asyncio
from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.menu import build_menu_text
from database.db import save_user_to_db, delete_user_from_db, get_user_data, on_startup, on_shutdown

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_allergy_confirmation = State()
    waiting_for_allergies = State()
    waiting_for_goal = State()
    waiting_for_timeframe = State()
    waiting_for_confirmation = State()
    waiting_for_delete_confirmation = State()


async def bot_startup():
    on_startup()


async def bot_shutdown():
    on_shutdown()


@router.message(Command("start"))
async def start_handler(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    await state.update_data(user_id=user_id)
    await msg.answer(f"Привет! Добро пожаловать в нашего бота.\nТвой уникальный ID: {user_id}\n\nКак тебя зовут?")
    await state.set_state(RegistrationStates.waiting_for_name)


@router.message(Command("mydata"))
async def mydata_handler(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    loop = asyncio.get_running_loop()
    user_data = await loop.run_in_executor(None, get_user_data, user_id)
    if user_data:
        summary = (f"📋 <b>Ваши данные</b>:\n\n"
                   f"🆔 ID: {user_data['user_id']}\n"
                   f"👤 Имя: {user_data['name']}\n"
                   f"🎂 Возраст: {user_data['age']}\n"
                   f"⚧ Пол: {user_data['gender']}\n"
                   f"⚖ Вес: {user_data['weight']} кг\n"
                   f"📏 Рост: {user_data['height']} см\n"
                   f"🌿 Аллергии: {user_data['allergies']}\n"
                   f"🎯 Цель: {user_data['goal']}\n"
                   f"⏳ Срок: {user_data['timeframe']}")
        await msg.answer(summary)
    else:
        await msg.answer("Вы еще не зарегистрированы. Введите /start для регистрации.")


@router.message(Command("regenerate"))
async def regenerate_handler(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    loop = asyncio.get_running_loop()
    user_data = await loop.run_in_executor(None, get_user_data, user_id)

    if not user_data:
        await msg.reply("Вы еще не зарегистрированы. Введите /start для регистрации.")
        return

    processing_msg = await msg.reply("⏳ Составляю новый план питания...")
    menu_text = await build_menu_text(user_data)
    await processing_msg.delete()
    await msg.reply(menu_text)


@router.message(Command("delete"))
async def delete_handler(msg: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, удалить")],
            [KeyboardButton(text="Нет, отменить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await msg.answer("Вы уверены, что хотите удалить свой аккаунт? Все данные будут потеряны.", reply_markup=keyboard)
    await state.set_state(RegistrationStates.waiting_for_delete_confirmation)


@router.message(StateFilter(RegistrationStates.waiting_for_delete_confirmation))
async def process_delete_confirmation(message: types.Message, state: FSMContext):
    if message.text == "Да, удалить":
        user_id = message.from_user.id
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, delete_user_from_db, user_id)
        await message.reply("Ваш аккаунт успешно удален из базы данных.\n"
                            "Если хотите начать заново, введите /start.")
        await state.clear()
    elif message.text == "Нет, отменить":
        await message.reply(
            "Удаление отменено. Напишите 'Вперёд к цели' для меню, /mydata для данных, /regenerate для нового плана или /delete для удаления.")
        await state.set_state(RegistrationStates.waiting_for_confirmation)
    else:
        await message.reply("Пожалуйста, выберите 'Да, удалить' или 'Нет, отменить'.")

@router.message(StateFilter(RegistrationStates.waiting_for_name))
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.reply("Сколько тебе лет?")
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(StateFilter(RegistrationStates.waiting_for_age))
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 10 or int(message.text) > 100:
        await message.reply("Пожалуйста, введи корректный возраст (от 10 до 100 лет).")
        return
    await state.update_data(age=int(message.text))
    await message.reply("Какой у тебя пол? (М/Ж)")
    await state.set_state(RegistrationStates.waiting_for_gender)

@router.message(StateFilter(RegistrationStates.waiting_for_gender))
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text.strip().lower()
    if gender not in ["м", "ж"]:
        await message.reply("Пожалуйста, введи 'М' (мужской) или 'Ж' (женский).")
        return
    await state.update_data(gender="Мужской" if gender == "м" else "Женский")
    await message.reply("Какой у тебя текущий вес (в кг)?")
    await state.set_state(RegistrationStates.waiting_for_weight)

@router.message(StateFilter(RegistrationStates.waiting_for_weight))
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(',', '.'))
        await state.update_data(weight=weight)
        await message.reply("Какой у тебя рост (в см)?")
        await state.set_state(RegistrationStates.waiting_for_height)
    except ValueError:
        await message.reply("Пожалуйста, введи корректный вес (например, 70.5).")

@router.message(StateFilter(RegistrationStates.waiting_for_height))
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = int(message.text)
        await state.update_data(height=height)
        await message.reply("У тебя есть аллергии? (Да/Нет)")
        await state.set_state(RegistrationStates.waiting_for_allergy_confirmation)
    except ValueError:
        await message.reply("Пожалуйста, введи корректное число.")

@router.message(StateFilter(RegistrationStates.waiting_for_allergy_confirmation))
async def process_allergy_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        await state.set_state(RegistrationStates.waiting_for_allergies)
        await message.reply("Перечисли свои аллергии через запятую (например, молоко, орехи).")
    else:
        await state.update_data(allergies="Нет")
        await message.reply("Какова твоя цель? (Похудение, Набор массы, Поддержание веса)")
        await state.set_state(RegistrationStates.waiting_for_goal)

@router.message(StateFilter(RegistrationStates.waiting_for_allergies))
async def process_allergies(message: types.Message, state: FSMContext):
    await state.update_data(allergies=message.text.strip())
    await message.reply("Какова твоя цель? (Похудение, Набор массы, Поддержание веса)")
    await state.set_state(RegistrationStates.waiting_for_goal)

@router.message(StateFilter(RegistrationStates.waiting_for_goal))
async def process_goal(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text.strip())
    await message.reply("За какое время ты хочешь достичь цели? (3 месяца, Полгода, Год)")
    await state.set_state(RegistrationStates.waiting_for_timeframe)

@router.message(StateFilter(RegistrationStates.waiting_for_timeframe))
async def process_timeframe(message: types.Message, state: FSMContext):
    await state.update_data(timeframe=message.text.strip())
    user_data = await state.get_data()

    summary = (f"✅ Регистрация завершена!\n\n"
               f"🆔 ID: {user_data['user_id']}\n"
               f"👤 Имя: {user_data['name']}\n"
               f"🎂 Возраст: {user_data['age']}\n"
               f"⚧ Пол: {user_data['gender']}\n"
               f"⚖ Вес: {user_data['weight']} кг\n"
               f"📏 Рост: {user_data['height']} см\n"
               f"🌿 Аллергии: {user_data['allergies']}\n"
               f"🎯 Цель: {user_data['goal']}\n"
               f"⏳ Срок: {user_data['timeframe']}")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, save_user_to_db, user_data)

    await message.reply(summary)
    await message.reply(
        "Напишите 'Вперёд к цели' для плана питания, /mydata для ваших данных, /regenerate для нового плана или /delete для удаления.")
    await state.set_state(RegistrationStates.waiting_for_confirmation)


@router.message(StateFilter(RegistrationStates.waiting_for_confirmation))
async def send_menu(message: types.Message, state: FSMContext):
    if message.text.lower().replace("ё", "е").strip() == "вперед к цели":
        user_id = message.from_user.id
        loop = asyncio.get_running_loop()
        user_data = await loop.run_in_executor(None, get_user_data, user_id)

        if not user_data:
            await message.reply("Вы еще не зарегистрированы. Введите /start для регистрации.")
            return

        processing_msg = await message.reply("⏳ Составляю план питания...")
        menu_text = await build_menu_text(user_data)
        await processing_msg.delete()
        await message.reply(menu_text)
    else:
        await message.reply(
            "Напишите 'Вперёд к цели' для плана, /mydata для данных, /regenerate для нового плана или /delete для удаления.")