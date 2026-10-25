import asyncio
from typing import Set
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.games import get_game, GAMES
from bot.keyboards import (
    get_games_selection_kb,
    get_game_interface_kb,
    get_after_game_kb,
    get_cancel_bet_kb,
    get_main_menu_kb,
)
from bot.states import BetState
from config import MIN_BET, MAX_BET, DEFAULT_BET

router = Router(name="game_router")

# Множество user_id игроков, у которых в данный момент идет бросок (защита от спама)
active_players: Set[int] = set()


@router.callback_query(F.data == "menu:games")
async def cb_games_list(callback: CallbackQuery, state: FSMContext):
    """Показывает список доступных игр."""
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0

    text = (
        f"🎮 <b>Игровой зал Telegram GameBot</b>\n\n"
        f"💰 Ваш баланс: <code>{balance:,}</code> 🪙\n\n"
        f"Выберите интерактивную игру:\n"
        f"• 🏀 <b>Баскетбол</b> (3-очковый x3, обычный x1.5)\n"
        f"• ⚽ <b>Футбол</b> (в девятку x3, гол x2 / x1.5)\n"
        f"• 🎳 <b>Боулинг</b> (страйк x3.5, 9 кеглей x2)\n"
        f"• 🎯 <b>Дартс</b> (яблочко x4, красное кольцо x2.5)\n"
        f"• 🎰 <b>Слоты 777</b> (джекпот x10, лимоны x5)\n"
        f"• 🎲 <b>Кости</b> (выпало 6 -> x3, 5 -> x2)\n"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_games_selection_kb())
    except Exception:
        await callback.message.answer(text, reply_markup=get_games_selection_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("select_game:"))
async def cb_select_game(callback: CallbackQuery, state: FSMContext):
    """Открывает экран выбранной игры."""
    await state.clear()
    game_code = callback.data.split(":")[1]
    game = get_game(game_code)
    if not game:
        await callback.answer("Игра не найдена!", show_alert=True)
        return

    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0
    saved_bet = await db.get_user_bet(callback.from_user.id)

    # Выбираем ставку: сохраненная ставка, но не больше баланса (если баланс > 0)
    current_bet = min(saved_bet, balance) if balance > 0 else MIN_BET
    if current_bet < MIN_BET:
        current_bet = MIN_BET

    await show_game_interface(callback, game_code, current_bet, balance)
    await callback.answer()


@router.callback_query(F.data.startswith("set_bet:"))
async def cb_set_bet(callback: CallbackQuery):
    """Изменение ставки через быстрые кнопки."""
    parts = callback.data.split(":")
    game_code = parts[1]
    new_bet = int(parts[2])

    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0

    if new_bet > balance and balance > 0:
        new_bet = balance

    await db.set_user_bet(callback.from_user.id, new_bet)
    await show_game_interface(callback, game_code, new_bet, balance)
    await callback.answer(f"Ставка: {new_bet:,} 🪙")

    await show_game_interface(callback, game_code, new_bet, balance)
    await callback.answer(f"Ставка: {new_bet:,} 🪙")


@router.callback_query(F.data.startswith("custom_bet:"))
async def cb_custom_bet_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода произвольной суммы ставки."""
    game_code = callback.data.split(":")[1]
    game = get_game(game_code)
    if not game:
        await callback.answer("Игра не найдена!", show_alert=True)
        return

    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0

    if balance < MIN_BET:
        await callback.answer(
            f"У вас недостаточно монет для ставки! Мин: {MIN_BET} 🪙",
            show_alert=True,
        )
        return

    await state.set_state(BetState.waiting_for_custom_bet)
    await state.update_data(game_code=game_code)

    text = (
        f"{game.emoji} <b>Ввод своей ставки для игры «{game.name}»</b>\n\n"
        f"💰 Ваш баланс: <code>{balance:,}</code> 🪙\n"
        f"Введите сумму ставки от <b>{MIN_BET}</b> до <b>{min(balance, MAX_BET):,}</b> 🪙:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=get_cancel_bet_kb(game_code))
    except Exception:
        await callback.message.answer(text, reply_markup=get_cancel_bet_kb(game_code))
    await callback.answer()


@router.message(BetState.waiting_for_custom_bet)
async def process_custom_bet_input(message: Message, state: FSMContext):
    """Обработка введенного пользователем числа для ставки."""
    data = await state.get_data()
    game_code = data.get("game_code", "basketball")
    await state.clear()

    user = await db.get_user(message.from_user.id)
    balance = user["balance"] if user else 0

    raw_text = message.text.strip().replace(" ", "").replace(",", "").replace(".", "")
    if not raw_text.isdigit():
        await message.answer(
            "❌ <b>Пожалуйста, введите корректное целое число!</b>",
            reply_markup=get_cancel_bet_kb(game_code),
        )
        return

    bet = int(raw_text)
    if bet < MIN_BET:
        await message.answer(
            f"❌ Минимальная ставка: <b>{MIN_BET}</b> 🪙",
            reply_markup=get_cancel_bet_kb(game_code),
        )
        return

    if bet > balance:
        await message.answer(
            f"❌ Недостаточно средств! Ваш баланс: <b>{balance:,}</b> 🪙",
            reply_markup=get_cancel_bet_kb(game_code),
        )
        return

    if bet > MAX_BET:
        await message.answer(
            f"❌ Максимальная ставка: <b>{MAX_BET:,}</b> 🪙",
            reply_markup=get_cancel_bet_kb(game_code),
        )
        return

    await db.set_user_bet(message.from_user.id, bet)
    game = get_game(game_code)
    text = (
        f"{game.emoji} <b>Игра: {game.name}</b>\n"
        f"<i>{game.description}</i>\n\n"
        f"💰 Баланс: <code>{balance:,}</code> 🪙\n"
        f"🎯 Установлена ставка: <b>{bet:,}</b> 🪙\n\n"
        f"Нажмите кнопку ниже, чтобы сделать бросок 👇"
    )
    await message.answer(
        text, reply_markup=get_game_interface_kb(game_code, bet, balance)
    )


async def show_game_interface(
    callback: CallbackQuery, game_code: str, current_bet: int, balance: int
):
    """Вспомогательная функция для обновления экрана игры."""
    game = get_game(game_code)
    if not game:
        return

    # Защита от ставки больше баланса
    if current_bet > balance and balance > 0:
        current_bet = balance
    elif balance == 0:
        current_bet = MIN_BET

    text = (
        f"{game.emoji} <b>Игра: {game.name}</b>\n"
        f"<i>{game.description}</i>\n\n"
        f"💰 Ваш баланс: <code>{balance:,}</code> 🪙\n"
        f"🎯 Выбранная ставка: <b>{current_bet:,}</b> 🪙\n\n"
    )

    if game_code == "basketball":
        text += (
            "🏆 <i>Чистый 3-очковый (x3.0): +{:,} 🪙\n"
            "🏀 Обычное попадание (x1.5): +{:,} 🪙</i>\n\n"
        ).format(int(current_bet * 3.0), int(current_bet * 1.5))
    elif game_code == "football":
        text += (
            "🚀 <i>В «девятку» (x3.0): +{:,} 🪙\n"
            "⚽ Гол в угол (x2.0): +{:,} 🪙\n"
            "🥅 Обычный гол (x1.5): +{:,} 🪙</i>\n\n"
        ).format(
            int(current_bet * 3.0),
            int(current_bet * 2.0),
            int(current_bet * 1.5),
        )
    elif game_code == "bowling":
        text += (
            "💥 <i>СТРАЙК 10 кеглей (x3.5): +{:,} 🪙\n"
            "🎳 9 кеглей (x2.0): +{:,} 🪙</i>\n\n"
        ).format(int(current_bet * 3.5), int(current_bet * 2.0))
    elif game_code == "darts":
        text += (
            "🎯 <i>В яблочко Bullseye (x4.0): +{:,} 🪙\n"
            "🔴 Около центра (x2.5): +{:,} 🪙</i>\n\n"
        ).format(int(current_bet * 4.0), int(current_bet * 2.5))
    elif game_code == "slots":
        text += (
            "🎰 <i>777 ДЖЕКПОТ (x10.0): +{:,} 🪙\n"
            "🍋 Три лимона (x5.0): +{:,} 🪙\n"
            "✨ Пара семерок (x2.0): +{:,} 🪙</i>\n\n"
        ).format(int(current_bet * 10.0), int(current_bet * 5.0), int(current_bet * 2.0))
    elif game_code == "dice":
        text += (
            "⚅ <i>Шестёрка (x3.0): +{:,} 🪙\n"
            "⚄ Пятёрка (x2.0): +{:,} 🪙</i>\n\n"
        ).format(int(current_bet * 3.0), int(current_bet * 2.0))

    text += "Нажмите кнопку броска ниже или выберите другую сумму ставки 👇"

    reply_markup = get_game_interface_kb(game_code, current_bet, balance)
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("play:"))
async def cb_play_game(callback: CallbackQuery):
    """Запуск броска интерактивного эмодзи Telegram."""
    user_id = callback.from_user.id
    if user_id in active_players:
        await callback.answer(
            "⏳ Ваш предыдущий бросок еще летит! Дождитесь результата.",
            show_alert=True,
        )
        return

    parts = callback.data.split(":")
    game_code = parts[1]
    bet = int(parts[2])

    game = get_game(game_code)
    if not game:
        await callback.answer("Игра не найдена!", show_alert=True)
        return

    # Проверяем и резервируем баланс
    success, remaining_balance, err = await db.reserve_bet(user_id, bet)
    if not success:
        await callback.answer(err, show_alert=True)
        return

    active_players.add(user_id)
    await callback.answer("🎲 Бросок пошел! Смотрите на анимацию...")

    try:
        # Отправляем настоящий анимированный эмодзи Telegram
        dice_msg = await callback.message.bot.send_dice(
            chat_id=callback.message.chat.id, emoji=game.emoji
        )
        dice_value = dice_msg.dice.value

        # Ждем завершения анимации в Telegram клиенте игрока
        await asyncio.sleep(game.animation_duration)

        # Рассчитываем результат по правилам игры
        res = game.calculate(dice_value, bet)

        # Фиксируем выигрыш и обновляем статистику в БД
        final_balance = await db.record_game_outcome(
            user_id=user_id,
            game_code=game_code,
            emoji=game.emoji,
            bet=bet,
            dice_value=dice_value,
            multiplier=res.multiplier,
            payout=res.payout,
            net_profit=res.net_profit,
        )

        # Формируем итоговое сообщение
        if res.is_win:
            result_header = "🎉 <b>ПОБЕДА! ВЫИГРЫШ!</b>"
            financial_info = (
                f"📈 Множитель: <b>x{res.multiplier:.1f}</b>\n"
                f"💵 Ваша ставка: <code>{bet:,}</code> 🪙\n"
                f"💰 Выплата: <b>+{res.payout:,}</b> 🪙\n"
                f"✨ Чистая прибыль: <b>+{res.net_profit:,}</b> 🪙"
            )
        elif res.payout > 0:
            result_header = "⚡ <b>ЧАСТИЧНЫЙ ВОЗВРАТ</b>"
            financial_info = (
                f"📊 Множитель: <b>x{res.multiplier:.1f}</b>\n"
                f"💵 Ваша ставка: <code>{bet:,}</code> 🪙\n"
                f"💰 Возврат: <b>+{res.payout:,}</b> 🪙\n"
                f"📉 Чистый итог: <b>{res.net_profit:,}</b> 🪙"
            )
        else:
            result_header = "💀 <b>ПРОИГРЫШ</b>"
            financial_info = (
                f"📉 Множитель: <b>x0.0</b>\n"
                f"💵 Ставка: <code>{bet:,}</code> 🪙 (сгорела)"
            )

        msg_text = (
            f"{result_header}\n\n"
            f"<b>{res.title}</b>\n"
            f"<i>{res.comment}</i>\n"
            f"📌 <i>{res.details}</i>\n\n"
            f"{financial_info}\n\n"
            f"💳 <b>Ваш новый баланс:</b> <code>{final_balance:,}</code> 🪙"
        )

        await callback.message.answer(
            msg_text, reply_markup=get_after_game_kb(game_code, bet)
        )

    except Exception as e:
        # В случае ошибки возвращаем ставку игроку
        await db.refund_bet(user_id, bet)
        await callback.message.answer(
            f"⚠️ Произошла ошибка во время броска: {e}. Ставка возвращена на ваш баланс.",
            reply_markup=get_main_menu_kb(),
        )
    finally:
        active_players.discard(user_id)
