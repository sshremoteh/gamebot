import asyncio
import re
from typing import Optional, Set, Tuple
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.games import get_game, GAMES, calculate_dice_guess, GameResult
from bot.keyboards import (
    get_after_game_kb,
    get_main_menu_kb,
    get_games_selection_kb,
)
from bot.handlers.game import active_players
from config import MIN_BET, MAX_BET, DEFAULT_BET

router = Router(name="text_games_router")


def parse_bet_value(raw: str, balance: int) -> Optional[int]:
    """Парсит сумму ставки из текста (например: '100', '100 монет', '1к', '2.5k', 'вабанк')."""
    t = raw.lower().strip()
    if t in ("вабанк", "ва-банк", "все", "всё", "all", "allin", "all-in"):
        return balance

    # Очищаем от мусорных слов
    for sub in ("монет", "монеты", "монета", "коинов", "рублей", "руб", "🪙"):
        t = t.replace(sub, "")
    t = t.replace(" ", "").replace(",", ".").strip()

    mult = 1
    if t.endswith(("к", "k")):
        mult = 1000
        t = t[:-1]
    elif t.endswith(("м", "m", "млн")):
        mult = 1000000
        t = re.sub(r"(млн|м|m)$", "", t)

    try:
        val = float(t) * mult
        return int(val)
    except ValueError:
        return None


def parse_dice_text(
    text: str, balance: int, default_bet: int
) -> Tuple[str, Optional[Set[int]], int]:
    """
    Разбирает текстовую команду для костей:
    - 'кости' -> ('classic', None, default_bet)
    - 'кости 3' -> ('guess', {3}, default_bet)
    - 'кости 3 5' -> ('guess', {3, 5}, default_bet)
    - 'кости 3 5 500' -> ('guess', {3, 5}, 500)
    - 'кости чет 1000' -> ('guess', {2, 4, 6}, 1000)
    - 'кости 500' -> ('classic', None, 500)
    """
    tokens = text.lower().strip().split()
    tokens = tokens[1:]  # Убираем само слово 'кости'/'кубик'

    if not tokens:
        return "classic", None, default_bet

    special_words = {
        "чет": {2, 4, 6},
        "чёт": {2, 4, 6},
        "четное": {2, 4, 6},
        "чётное": {2, 4, 6},
        "нечет": {1, 3, 5},
        "нечёт": {1, 3, 5},
        "нечетное": {1, 3, 5},
        "нечётное": {1, 3, 5},
        "больше": {4, 5, 6},
        "меньше": {1, 2, 3},
    }

    targets: Set[int] = set()
    bet: Optional[int] = None
    idx = 0

    while idx < len(tokens):
        tok = tokens[idx]
        if tok in special_words:
            targets.update(special_words[tok])
            idx += 1
        elif tok in ("ставка", "деп", "на") and idx + 1 < len(tokens):
            parsed = parse_bet_value(tokens[idx + 1], balance)
            if parsed is not None:
                bet = parsed
                idx += 2
            else:
                idx += 1
        elif tok.isdigit() and 1 <= int(tok) <= 6 and len(targets) < 5 and bet is None:
            targets.add(int(tok))
            idx += 1
        else:
            parsed = parse_bet_value(tok, balance)
            if parsed is not None:
                bet = parsed
            idx += 1

    final_bet = bet if bet is not None else default_bet
    if targets:
        return "guess", targets, final_bet
    else:
        return "classic", None, final_bet


async def execute_text_throw(
    message: Message,
    game_code: str,
    bet: int,
    custom_calc=None,
    game_header_override=None,
):
    """Общая функция выполнения интерактивного броска по текстовой команде."""
    user_id = message.from_user.id
    if user_id in active_players:
        await message.reply(
            "⏳ Предыдущий бросок еще выполняется! Дождитесь результата."
        )
        return

    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.get_or_create_user(
            user_id, message.from_user.username, message.from_user.first_name
        )

    balance = user["balance"]

    # Валидация ставки
    if bet < MIN_BET:
        await message.reply(
            f"❌ Минимальная ставка: <b>{MIN_BET}</b> 🪙.\n"
            f"Установите ставку командой <code>ставка {MIN_BET}</code>."
        )
        return

    if bet > balance:
        await message.reply(
            f"❌ Недостаточно монет! Ваш баланс: <b>{balance:,}</b> 🪙.\n"
            f"Чтобы изменить ставку, напишите например: <code>ставка {balance:,}</code>"
        )
        return

    if bet > MAX_BET:
        await message.reply(f"❌ Максимальная ставка: <b>{MAX_BET:,}</b> 🪙.")
        return

    game = get_game(game_code)
    if not game:
        return

    # Запоминаем ставку пользователя для следующих бросков
    await db.set_user_bet(user_id, bet)

    # Резервируем ставку
    success, remaining_bal, err = await db.reserve_bet(user_id, bet)
    if not success:
        await message.reply(err)
        return

    active_players.add(user_id)

    try:
        # Отправляем интерактивный эмодзи Telegram
        dice_msg = await message.answer_dice(emoji=game.emoji)
        dice_value = dice_msg.dice.value

        # Ждем завершения анимации
        await asyncio.sleep(game.animation_duration)

        # Расчет результата
        if custom_calc:
            res: GameResult = custom_calc(dice_value, bet)
        else:
            res = game.calculate(dice_value, bet)

        # Фиксируем в БД
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

        # Формируем отчет
        if res.is_win:
            header = "🎉 <b>ПОБЕДА! ВЫИГРЫШ!</b>"
            financial_info = (
                f"📈 Множитель: <b>x{res.multiplier:.1f}</b>\n"
                f"💵 Ваша ставка: <code>{bet:,}</code> 🪙\n"
                f"💰 Выплата: <b>+{res.payout:,}</b> 🪙\n"
                f"✨ Чистая прибыль: <b>+{res.net_profit:,}</b> 🪙"
            )
        elif res.payout > 0:
            header = "⚡ <b>ЧАСТИЧНЫЙ ВОЗВРАТ</b>"
            financial_info = (
                f"📊 Множитель: <b>x{res.multiplier:.1f}</b>\n"
                f"💵 Ваша ставка: <code>{bet:,}</code> 🪙\n"
                f"💰 Возврат: <b>+{res.payout:,}</b> 🪙\n"
                f"📉 Чистый итог: <b>{res.net_profit:,}</b> 🪙"
            )
        else:
            header = "💀 <b>ПРОИГРЫШ</b>"
            financial_info = (
                f"📉 Множитель: <b>x0.0</b>\n"
                f"💵 Ставка: <code>{bet:,}</code> 🪙 (сгорела)"
            )

        if game_header_override:
            header = game_header_override

        reply_text = (
            f"{header}\n\n"
            f"<b>{res.title}</b>\n"
            f"<i>{res.comment}</i>\n"
            f"📌 <i>{res.details}</i>\n\n"
            f"{financial_info}\n\n"
            f"💳 <b>Ваш новый баланс:</b> <code>{final_balance:,}</code> 🪙"
        )

        await message.reply(
            reply_text, reply_markup=get_after_game_kb(game_code, bet)
        )

    except Exception as e:
        await db.refund_bet(user_id, bet)
        await message.reply(
            f"⚠️ Ошибка броска: {e}. Ставка возвращена на баланс.",
            reply_markup=get_main_menu_kb(),
        )
    finally:
        active_players.discard(user_id)


# -------------------------------------------------------------
# ХЕНДЛЕР: Установка ставки текстом ("ставка 100", "ставка 500 монет", "ставка вабанк")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("ставка", "деп", "поставить")))
async def text_set_bet(message: Message, state: FSMContext):
    # Если пользователь находится в FSM состоянии ввода, не перехватываем
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.get_or_create_user(
            user_id, message.from_user.username, message.from_user.first_name
        )
    balance = user["balance"]

    raw = message.text.strip()
    # Убираем первое слово ("ставка", "деп" и т.п.)
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        current_bet = await db.get_user_bet(user_id)
        await message.reply(
            f"🎯 <b>Текущая ставка:</b> <code>{current_bet:,}</code> 🪙\n"
            f"💰 Ваш баланс: <code>{balance:,}</code> 🪙\n\n"
            f"Чтобы изменить ставку, напишите например:\n"
            f"• <code>ставка 100</code>\n"
            f"• <code>ставка 500 монет</code>\n"
            f"• <code>ставка 1к</code> (1,000)\n"
            f"• <code>ставка вабанк</code> (все монеты)"
        )
        return

    bet_str = parts[1]
    parsed_bet = parse_bet_value(bet_str, balance)

    if parsed_bet is None:
        await message.reply(
            "❌ Не удалось распознать сумму ставки. Напишите например: <code>ставка 500</code> или <code>ставка 1к</code>."
        )
        return

    if parsed_bet < MIN_BET:
        await message.reply(f"❌ Минимальная ставка: <b>{MIN_BET}</b> 🪙.")
        return

    if parsed_bet > balance and balance > 0:
        await message.reply(
            f"❌ Недостаточно средств! Ваш баланс: <b>{balance:,}</b> 🪙."
        )
        return

    if parsed_bet > MAX_BET:
        await message.reply(f"❌ Максимальная ставка: <b>{MAX_BET:,}</b> 🪙.")
        return

    await db.set_user_bet(user_id, parsed_bet)

    await message.reply(
        f"✅ <b>Текущая ставка успешно установлена:</b> <code>{parsed_bet:,}</code> 🪙\n\n"
        f"💰 Баланс: <code>{balance:,}</code> 🪙\n\n"
        f"🚀 Теперь напишите название игры для броска:\n"
        f"• <b>баскетбол</b> (или <b>баскет</b>)\n"
        f"• <b>футбол</b> (или <b>футбик</b>)\n"
        f"• <b>боулинг</b> (или <b>кегли</b>)\n"
        f"• <b>дартс</b> (или <b>мишень</b>)\n"
        f"• <b>слоты</b> (или <b>казино</b>)\n"
        f"• <b>кости</b> (или <b>кости 3</b> / <b>кости 3 5</b>)"
    )


# -------------------------------------------------------------
# ХЕНДЛЕР: Игра в кости словами ("кости 3", "кости 3 5", "кости", "кубик")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("кости", "кубик", "dice", "🎲")))
async def text_play_dice(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.get_or_create_user(
            user_id, message.from_user.username, message.from_user.first_name
        )
    balance = user["balance"]
    saved_bet = await db.get_user_bet(user_id)

    mode, targets, bet = parse_dice_text(message.text, balance, saved_bet)

    if mode == "guess" and targets:
        # Угадывание чисел на кубике ("кости 3", "кости 3 5")
        count = len(targets)
        mult_map = {1: "x5.0", 2: "x3.0", 3: "x2.0", 4: "x1.4", 5: "x1.15"}
        expected_mult = mult_map.get(count, "x1.0")
        sorted_targets = sorted(list(targets))
        targets_str = ", ".join(str(t) for t in sorted_targets)

        custom_calc = lambda val, b: calculate_dice_guess(val, targets, b)
        await execute_text_throw(
            message=message,
            game_code="dice",
            bet=bet,
            custom_calc=custom_calc,
            game_header_override=f"🎲 <b>БРОСОК КУБИКА (Цели: {targets_str} | Множитель: {expected_mult})</b>",
        )
    else:
        # Классические кости
        await execute_text_throw(
            message=message,
            game_code="dice",
            bet=bet,
        )


# -------------------------------------------------------------
# ХЕНДЛЕР: Баскетбол словами ("баскетбол", "баскет", "баскетбол 500", "🏀")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("баскетбол", "баскет", "🏀")))
async def text_play_basketball(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 10000
    saved_bet = await db.get_user_bet(user_id)

    # Проверяем, указана ли ставка сразу в сообщении, например "баскетбол 500"
    tokens = message.text.lower().split()
    bet = saved_bet
    if len(tokens) > 1:
        parsed = parse_bet_value(" ".join(tokens[1:]), balance)
        if parsed is not None:
            bet = parsed

    await execute_text_throw(message, "basketball", bet)


# -------------------------------------------------------------
# ХЕНДЛЕР: Футбол словами ("футбол", "футбик", "футбол 1000", "⚽")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("футбол", "футбик", "ногомяч", "⚽")))
async def text_play_football(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 10000
    saved_bet = await db.get_user_bet(user_id)

    tokens = message.text.lower().split()
    bet = saved_bet
    if len(tokens) > 1:
        parsed = parse_bet_value(" ".join(tokens[1:]), balance)
        if parsed is not None:
            bet = parsed

    await execute_text_throw(message, "football", bet)


# -------------------------------------------------------------
# ХЕНДЛЕР: Боулинг словами ("боулинг", "кегли", "боул", "🎳")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("боулинг", "кегли", "боул", "🎳")))
async def text_play_bowling(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 10000
    saved_bet = await db.get_user_bet(user_id)

    tokens = message.text.lower().split()
    bet = saved_bet
    if len(tokens) > 1:
        parsed = parse_bet_value(" ".join(tokens[1:]), balance)
        if parsed is not None:
            bet = parsed

    await execute_text_throw(message, "bowling", bet)


# -------------------------------------------------------------
# ХЕНДЛЕР: Дартс словами ("дартс", "дарт", "мишень", "darts", "🎯")
# -------------------------------------------------------------
@router.message(F.text.lower().startswith(("дартс", "дарт", "мишень", "darts", "🎯")))
async def text_play_darts(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 10000
    saved_bet = await db.get_user_bet(user_id)

    tokens = message.text.lower().split()
    bet = saved_bet
    if len(tokens) > 1:
        parsed = parse_bet_value(" ".join(tokens[1:]), balance)
        if parsed is not None:
            bet = parsed

    await execute_text_throw(message, "darts", bet)


# -------------------------------------------------------------
# ХЕНДЛЕР: Слоты словами ("слоты", "казино", "казик", "спин", "рулетка", "автомат", "🎰")
# -------------------------------------------------------------
@router.message(
    F.text.lower().startswith(
        ("слоты", "казино", "казик", "спин", "рулетка", "автомат", "slots", "🎰")
    )
)
async def text_play_slots(message: Message, state: FSMContext):
    if await state.get_state():
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = user["balance"] if user else 10000
    saved_bet = await db.get_user_bet(user_id)

    tokens = message.text.lower().split()
    bet = saved_bet
    if len(tokens) > 1:
        parsed = parse_bet_value(" ".join(tokens[1:]), balance)
        if parsed is not None:
            bet = parsed

    await execute_text_throw(message, "slots", bet)


# -------------------------------------------------------------
# ХЕНДЛЕР: Текстовые команды информации (баланс, топ, бонус и т.д.)
# -------------------------------------------------------------
@router.message(F.text.lower().in_(("баланс", "б", "balance", "монеты", "счет", "счёт")))
async def text_quick_balance(message: Message):
    user = await db.get_user(message.from_user.id)
    balance = user["balance"] if user else 0
    current_bet = await db.get_user_bet(message.from_user.id)
    await message.reply(
        f"💰 <b>Ваш баланс:</b> <code>{balance:,}</code> 🪙\n"
        f"🎯 <b>Текущая ставка:</b> <code>{current_bet:,}</code> 🪙\n\n"
        f"Напишите название игры (например, <b>баскетбол</b> или <b>кости 3 5</b>) для броска!"
    )
