from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import db

router = Router(name="leaderboard_router")


def get_leaderboard_kb() -> InlineKeyboardMarkup:
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


async def render_leaderboard_text() -> str:
    top_users = await db.get_leaderboard(limit=10)

    text = "🏆 <b>Таблица лидеров GameBot</b>\n\n"
    text += "Топ самых богатых игроков по балансу монет:\n\n"

    if not top_users:
        text += "<i>Пока никто не попал в таблицу лидеров. Станьте первым!</i>\n"
        return text

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, user in enumerate(top_users):
        rank_icon = medals[i] if i < len(medals) else f"{i + 1}."
        name = user.get("first_name") or user.get("username") or f"Игрок {user['user_id']}"
        # Экранируем HTML символы в имени
        name = name.replace("<", "&lt;").replace(">", "&gt;")
        bal = user.get("balance", 0)
        wins = user.get("total_wins", 0)
        games = user.get("total_games", 0)

        text += f"{rank_icon} <b>{name}</b> — <code>{bal:,}</code> 🪙 (побед: {wins}/{games})\n"

    text += "\n<i>Играйте, выигрывайте с максимальными коэффициентами и займите 1 место!</i>"
    return text


@router.message(Command("top"))
async def cmd_top(message: Message, state: FSMContext):
    await state.clear()
    text = await render_leaderboard_text()
    await message.answer(text, reply_markup=get_leaderboard_kb())


@router.callback_query(F.data == "menu:leaderboard")
async def cb_leaderboard(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = await render_leaderboard_text()
    try:
        await callback.message.edit_text(text, reply_markup=get_leaderboard_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_leaderboard_kb())
    await callback.answer()
