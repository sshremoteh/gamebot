from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.keyboards import get_main_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="profile_router")


def get_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 В игровой зал", callback_data="menu:games"),
                InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="menu:bonus"),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


async def render_profile_text(user_id: int, user_info: dict) -> str:
    history = await db.get_user_history(user_id, limit=5)

    balance = user_info["balance"]
    total_games = user_info["total_games"]
    total_wins = user_info["total_wins"]
    total_losses = user_info["total_losses"]
    won_amount = user_info["total_won_amount"]
    lost_amount = user_info["total_lost_amount"]
    biggest_win = user_info["biggest_win"]

    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0
    net_total = won_amount - lost_amount

    profit_emoji = "📈" if net_total >= 0 else "📉"
    profit_sign = "+" if net_total > 0 else ""

    text = (
        f"👤 <b>Профиль игрока: {user_info.get('first_name', 'Игрок')}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💰 <b>Баланс:</b> <code>{balance:,}</code> 🪙\n\n"
        f"📊 <b>Статистика игр:</b>\n"
        f"• Всего сыграно: <b>{total_games}</b>\n"
        f"• Побед: <b>{total_wins}</b> | Поражений: <b>{total_losses}</b>\n"
        f"• Процент побед: <b>{win_rate:.1f}%</b>\n"
        f"• Рекордный выигрыш: <b>{biggest_win:,}</b> 🪙\n"
        f"• {profit_emoji} Общий профит: <b>{profit_sign}{net_total:,}</b> 🪙\n\n"
    )

    if history:
        text += "📜 <b>Последние 5 игр:</b>\n"
        for item in history:
            net = item["net_profit"]
            sign = "+" if net > 0 else ""
            res_icon = "🟢" if net > 0 else ("🟡" if item["payout"] > 0 else "🔴")
            text += (
                f"{res_icon} {item['emoji']} Ставка: <code>{item['bet']:,}</code> | "
                f"x{item['multiplier']:.1f} → <b>{sign}{net:,}</b> 🪙\n"
            )
    else:
        text += "<i>Вы еще не сыграли ни одной игры. Самое время испытать удачу!</i>\n"

    return text


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if not user:
        user, _ = await db.get_or_create_user(
            message.from_user.id, message.from_user.username, message.from_user.first_name
        )

    text = await render_profile_text(message.from_user.id, user)
    await message.answer(text, reply_markup=get_profile_kb())


@router.callback_query(F.data == "menu:profile")
async def cb_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    if not user:
        user, _ = await db.get_or_create_user(
            callback.from_user.id, callback.from_user.username, callback.from_user.first_name
        )

    text = await render_profile_text(callback.from_user.id, user)
    try:
        await callback.message.edit_text(text, reply_markup=get_profile_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_profile_kb())
    await callback.answer()
