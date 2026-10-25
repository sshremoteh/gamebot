from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.keyboards import get_main_menu_kb
from config import STARTING_BALANCE

router = Router(name="start_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user, is_new = await db.get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    greeting = (
        f"👋 <b>Добро пожаловать в Telegram GameBot, {message.from_user.first_name}!</b>\n\n"
        f"🎮 Здесь вы можете играть на настоящих <b>интерактивных эмодзи Telegram</b>:\n"
        f"• 🏀 <b>Баскетбол</b> — трехочковый умножает ставку в <b>x3</b>, обычный в <b>x1.5</b>!\n"
        f"• ⚽ <b>Футбол</b> — мощный удар в «девятку» дает <b>x3</b>!\n"
        f"• 🎳 <b>Боулинг</b> — сокрушительный страйк приносит <b>x3.5</b>!\n"
        f"• 🎯 <b>Дартс</b> — точное попадание в яблочко (Bullseye) умножает ставку в <b>x4</b>!\n"
        f"• 🎰 <b>Слоты 777</b> — сорвите ДЖЕКПОТ с множителем <b>x10</b>!\n"
        f"• 🎲 <b>Кости</b> — классический бросок кубика до <b>x3</b>!\n\n"
    )

    if is_new:
        greeting += (
            f"🎁 <b>Вам начислен стартовый бонус: {STARTING_BALANCE:,} монет! 🪙</b>\n"
            f"Делайте ставки, проверяйте удачу и поднимайтесь в топ игроков!\n\n"
        )
    else:
        greeting += f"💰 <b>Ваш текущий баланс:</b> <code>{user['balance']:,}</code> 🪙\n\n"

    greeting += "Выберите действие в меню ниже 👇"

    await message.answer(greeting, reply_markup=get_main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else STARTING_BALANCE

    text = (
        f"🏠 <b>Главное меню GameBot</b>\n\n"
        f"👤 Игрок: <b>{callback.from_user.first_name}</b>\n"
        f"💰 Баланс: <code>{balance:,}</code> 🪙\n\n"
        f"Выберите раздел:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_main_menu_kb())
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Команды бота:</b>\n\n"
        "• /start — Главное меню и перезапуск\n"
        "• /profile — Мой профиль и статистика\n"
        "• /bonus — Ежедневный бонус монет\n"
        "• /top — Таблица лидеров\n"
        "• /rules — Правила и коэффициенты игр\n"
        "• /bailout — Второе дыхание (если закончились монеты)\n\n"
        "<i>Все игры основаны на официальной физике анимированных эмодзи Telegram (Dice API). "
        "Результат каждого броска генерируется серверами Telegram честно и независимо!</i>"
    )
    await message.answer(text, reply_markup=get_main_menu_kb())
