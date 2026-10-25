import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import db
from bot.keyboards import get_back_to_menu_kb
from config import DAILY_BONUS_MIN, DAILY_BONUS_MAX, BAILOUT_AMOUNT, BAILOUT_THRESHOLD

router = Router(name="bonus_router")


def get_bonus_action_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 В игровой зал", callback_data="menu:games"),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


@router.message(Command("bonus"))
async def cmd_bonus(message: Message, state: FSMContext):
    await state.clear()
    await process_daily_bonus(message.from_user.id, message)


@router.callback_query(F.data == "menu:bonus")
async def cb_bonus(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await process_daily_bonus(callback.from_user.id, callback)
    await callback.answer()


async def process_daily_bonus(user_id: int, event: Message | CallbackQuery):
    bonus_amount = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
    success, new_balance, remaining_seconds = await db.claim_daily_bonus(
        user_id, bonus_amount
    )

    if success:
        text = (
            f"🎁 <b>Ежедневный бонус получен!</b>\n\n"
            f"Вам начислено: <b>+{bonus_amount:,}</b> 🪙\n"
            f"💳 Новый баланс: <code>{new_balance:,}</code> 🪙\n\n"
            f"<i>Следующий бонус будет доступен через 24 часа. Удачи в играх!</i>"
        )
    else:
        hours = remaining_seconds // 3600 if remaining_seconds else 0
        minutes = (remaining_seconds % 3600) // 60 if remaining_seconds else 0
        text = (
            f"⏳ <b>Вы уже забирали ежедневный бонус!</b>\n\n"
            f"До следующего бонуса осталось: <b>{hours} ч. {minutes} мин.</b>\n"
            f"💰 Ваш текущий баланс: <code>{new_balance:,}</code> 🪙\n\n"
            f"<i>Заходите завтра за новой порцией монет!</i>"
        )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_bonus_action_kb())
    else:
        try:
            await event.message.edit_text(text, reply_markup=get_bonus_action_kb())
        except Exception:
            await event.message.answer(text, reply_markup=get_bonus_action_kb())


@router.message(Command("bailout"))
async def cmd_bailout(message: Message, state: FSMContext):
    await state.clear()
    await process_bailout(message.from_user.id, message)


@router.callback_query(F.data == "menu:bailout")
async def cb_bailout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await process_bailout(callback.from_user.id, callback)
    await callback.answer()


async def process_bailout(user_id: int, event: Message | CallbackQuery):
    success, new_balance, reason = await db.claim_bailout(user_id)

    if success:
        text = (
            f"🆘 <b>Второе дыхание активировано!</b>\n\n"
            f"{reason}\n"
            f"💳 Ваш баланс пополнен до: <code>{new_balance:,}</code> 🪙\n\n"
            f"<i>Не унывайте, в этот раз фортуна обязательно улыбнется!</i>"
        )
    else:
        text = (
            f"ℹ️ <b>Помощь банкроту недоступна</b>\n\n"
            f"{reason}\n"
            f"💰 Текущий баланс: <code>{new_balance:,}</code> 🪙"
        )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_bonus_action_kb())
    else:
        try:
            await event.message.edit_text(text, reply_markup=get_bonus_action_kb())
        except Exception:
            await event.message.answer(text, reply_markup=get_bonus_action_kb())
