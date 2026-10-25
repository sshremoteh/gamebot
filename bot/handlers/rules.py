from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.games import GAMES, get_game
from bot.keyboards import get_rules_menu_kb, get_game_interface_kb

router = Router(name="rules_router")


def get_game_rules_kb(game_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Перейти к этой игре", callback_data=f"select_game:{game_code}"
                )
            ],
            [
                InlineKeyboardButton(text="📜 Все правила", callback_data="menu:rules"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


def get_all_rules_text() -> str:
    return (
        "📖 <b>Справочник правил и коэффициентов GameBot</b>\n\n"
        "Все игры используют официальные интерактивные эмодзи Telegram (Dice API). "
        "Физика анимации и исход броска определяются на серверах Telegram!\n\n"
        "🏀 <b>Баскетбол:</b>\n"
        "• Чистый 3-очковый (Swish) — <b>x3.0</b>\n"
        "• Обычное попадание (с отскоком) — <b>x1.5</b>\n"
        "• Промах (щит / дужка / мимо) — <b>x0.0</b> (сгорает)\n\n"
        "⚽ <b>Футбол:</b>\n"
        "• Гол в «девятку» — <b>x3.0</b>\n"
        "• Гол в угол ворот — <b>x2.0</b>\n"
        "• Гол по центру — <b>x1.5</b>\n"
        "• Штанга / сейв вратаря / мимо — <b>x0.0</b>\n\n"
        "🎳 <b>Боулинг:</b>\n"
        "• Страйк (все 10 кеглей) — <b>x3.5</b>\n"
        "• 9 кеглей (почти страйк) — <b>x2.0</b>\n"
        "• 5-6 кеглей — <b>x1.4</b>\n"
        "• 3 кегли — <b>x0.8</b> (возврат 80% ставки)\n"
        "• 0-1 кегля — <b>x0.0</b>\n\n"
        "🎯 <b>Дартс:</b>\n"
        "• В яблочко! (Bullseye - центр) — <b>x4.0</b>\n"
        "• Красное кольцо возле центра — <b>x2.5</b>\n"
        "• Внутренний сектор — <b>x1.8</b>\n"
        "• Внешний сектор — <b>x1.2</b>\n"
        "• Обод / мимо — <b>x0.0</b>\n\n"
        "🎰 <b>Слоты 777 (Рулетка):</b>\n"
        "• 7️⃣ 7️⃣ 7️⃣ Джекпот — <b>x10.0</b>\n"
        "• 🍋 🍋 🍋 Три лимона — <b>x5.0</b>\n"
        "• 🍇 🍇 🍇 Три винограда — <b>x4.0</b>\n"
        "• 🍫 🍫 🍫 Три BAR — <b>x3.0</b>\n"
        "• Пара семёрок (7️⃣ 7️⃣) — <b>x2.0</b>\n"
        "• Любая пара одинаковых — <b>x1.4</b>\n"
        "• Все разные — <b>x0.0</b>\n\n"
        "🎲 <b>Кости:</b>\n"
        "• <b>Классический режим:</b> 6 -> <b>x3.0</b>, 5 -> <b>x2.0</b>, 4 -> <b>x1.5</b>, 3 -> <b>x1.0</b>\n"
        "• <b>Режим угадывания чисел:</b>\n"
        "  - 1 число (например: <code>кости 3</code>) — <b>x5.0</b>\n"
        "  - 2 числа (например: <code>кости 3 5</code>) — <b>x3.0</b>\n"
        "  - 3 числа / чет / нечет (например: <code>кости чет</code>) — <b>x2.0</b>\n\n"
        "💬 <b>Быстрая игра словами (как в @spins):</b>\n"
        "• <code>ставка 100</code> — меняет вашу ставку на 100 монет\n"
        "• <code>баскетбол</code> — бросок мяча с текущей ставкой\n"
        "• <code>баскетбол 500</code> — бросок со ставкой 500\n"
        "• <code>футбол</code>, <code>боулинг</code>, <code>дартс</code>, <code>слоты</code>, <code>кости</code>\n"
        "• <code>кости 3</code>, <code>кости 3 5</code>, <code>кости чет</code>\n\n"
        "<i>Нажмите на конкретную игру ниже, чтобы узнать больше:</i>"
    )


@router.message(Command("rules"))
async def cmd_rules(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(get_all_rules_text(), reply_markup=get_rules_menu_kb())


@router.callback_query(F.data == "menu:rules")
async def cb_rules(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = get_all_rules_text()
    try:
        await callback.message.edit_text(text, reply_markup=get_rules_menu_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_rules_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("game_rules:"))
async def cb_single_game_rules(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    game_code = callback.data.split(":")[1]
    game = get_game(game_code)
    if not game:
        await callback.answer("Игра не найдена!", show_alert=True)
        return

    text = f"{game.rules_text}\n\nСтартовый баланс: <b>10,000 🪙</b>"
    try:
        await callback.message.edit_text(text, reply_markup=get_game_rules_kb(game_code))
    except Exception:
        await callback.message.answer(text, reply_markup=get_game_rules_kb(game_code))
    await callback.answer()
