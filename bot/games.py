from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class GameResult:
    dice_value: int
    multiplier: float
    bet: int
    payout: int
    net_profit: int
    is_win: bool
    title: str
    comment: str
    details: str


@dataclass
class GameInfo:
    code: str
    name: str
    emoji: str
    animation_duration: float
    description: str
    rules_text: str

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        raise NotImplementedError


class BasketballGame(GameInfo):
    def __init__(self):
        super().__init__(
            code="basketball",
            name="Баскетбол",
            emoji="🏀",
            animation_duration=3.5,
            description="Забросьте мяч в кольцо! Чистый трехочковый умножает ставку в 3 раза!",
            rules_text=(
                "🏀 <b>Правила баскетбола:</b>\n\n"
                "• 🔥 <b>Чистый трехочковый (Swish)</b> — <b>x3.0</b>\n"
                "• 🏀 <b>Обычное попадание (с отскоком)</b> — <b>x1.5</b>\n"
                "• ❌ <b>Промах (щит / дужка / мимо)</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Бросайте мяч и проверьте свою меткость!</i>"
            ),
        )

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        # Telegram Basketball:
        # 5: Clean swish / 3-pointer
        # 4: Regular score (bounces in)
        # 1, 2, 3: Miss (airball, backboard bounce, rim bounce)
        if dice_value == 5:
            mult = 3.0
            is_win = True
            title = "🔥 ЧИСТЫЙ ТРЕХОЧКОВЫЙ!"
            comment = "Мяч влетел точно в корзину без единого касания дужки!"
            details = "Идеальный бросок (5/5)"
        elif dice_value == 4:
            mult = 1.5
            is_win = True
            title = "🏀 ТОЧНОЕ ПОПАДАНИЕ!"
            comment = "Мяч ударился о дужку и провалился в корзину!"
            details = "Засчитано 2 очка (4/5)"
        elif dice_value == 3:
            mult = 0.0
            is_win = False
            title = "❌ ОБИДНЫЙ ПРОМАХ!"
            comment = "Мяч попрыгал по дужке кольца и соскочил наружу..."
            details = "Отскок от дужки (3/5)"
        elif dice_value == 2:
            mult = 0.0
            is_win = False
            title = "❌ МИМО КОРЗИНЫ!"
            comment = "Мяч ударился о щит и отлетел в сторону..."
            details = "Удар в щит (2/5)"
        else:
            mult = 0.0
            is_win = False
            title = "❌ ПОЛНЫЙ ПРОМАХ!"
            comment = "Мяч даже близко не долетел до корзины (Airball)..."
            details = "Мимо кольца (1/5)"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=is_win,
            title=title,
            comment=comment,
            details=details,
        )


class FootballGame(GameInfo):
    def __init__(self):
        super().__init__(
            code="football",
            name="Футбол",
            emoji="⚽",
            animation_duration=3.5,
            description="Пробейте пенальти в девятку! Красивые голы дают высокий коэффициент!",
            rules_text=(
                "⚽ <b>Правила футбола (пенальти):</b>\n\n"
                "• 🚀 <b>Гол в «девятку» (верхний угол)</b> — <b>x3.0</b>\n"
                "• ⚽ <b>Гол в угол ворот</b> — <b>x2.0</b>\n"
                "• 🥅 <b>Обычный гол по центру</b> — <b>x1.5</b>\n"
                "• ❌ <b>Штанга / сейв вратаря / мимо</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Пробейте вратаря мощным ударом!</i>"
            ),
        )

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        # Telegram Football:
        # 5: Top corner goal (девятка)
        # 4: Clean goal (в угол)
        # 3: Regular goal
        # 2: Post / save
        # 1: Miss wide
        if dice_value == 5:
            mult = 3.0
            is_win = True
            title = "🚀 ПУШКА В ДЕВЯТКУ!"
            comment = "Фантастический удар в самый верхний угол без шансов для вратаря!"
            details = "Гол в девятку (5/5)"
        elif dice_value == 4:
            mult = 2.0
            is_win = True
            title = "⚽ КРАСИВЫЙ ГОЛ!"
            comment = "Точный удар в угол ворот, вратарь не дотянулся!"
            details = "Гол в угол (4/5)"
        elif dice_value == 3:
            mult = 1.5
            is_win = True
            title = "🥅 ГОООЛ!"
            comment = "Мяч пролетает по центру и пересекает линию ворот!"
            details = "Гол (3/5)"
        elif dice_value == 2:
            mult = 0.0
            is_win = False
            title = "❌ ЗВОН ШТАНГИ!"
            comment = "Удар пришелся в перекладину, вратарь накрывает мяч!"
            details = "Штанга / сейв (2/5)"
        else:
            mult = 0.0
            is_win = False
            title = "❌ МИМО ВОРОТ!"
            comment = "Мяч улетел далеко на трибуны..."
            details = "Промах (1/5)"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=is_win,
            title=title,
            comment=comment,
            details=details,
        )


class BowlingGame(GameInfo):
    def __init__(self):
        super().__init__(
            code="bowling",
            name="Боулинг",
            emoji="🎳",
            animation_duration=3.5,
            description="Запустите шар по дорожке и выбейте страйк со всеми 10 кеглями!",
            rules_text=(
                "🎳 <b>Правила боулинга:</b>\n\n"
                "• 💥 <b>СТРАЙК (все 10 кеглей!)</b> — <b>x3.5</b>\n"
                "• 🎳 <b>Почти страйк (9 кеглей)</b> — <b>x2.0</b>\n"
                "• 🎯 <b>Хороший бросок (5-6 кеглей)</b> — <b>x1.4</b>\n"
                "• ⚡ <b>Утешительный возврат (3 кегли)</b> — <b>x0.8</b>\n"
                "• ❌ <b>1 кегля или желоб (0 кеглей)</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Точный бросок прямо по центру дорожки!</i>"
            ),
        )

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        # Telegram Bowling:
        # 6: Strike (10 pins)
        # 5: 9 pins
        # 4: 5-6 pins
        # 3: 3 pins
        # 2: 1 pin
        # 1: Gutter ball (0 pins)
        if dice_value == 6:
            mult = 3.5
            is_win = True
            title = "💥 СТРАЙК! ВСЕ 10 КЕГЛЕЙ!"
            comment = "Все кегли разлетелись в щепки! Идеальный бросок!"
            details = "10 из 10 кеглей (6/6)"
        elif dice_value == 5:
            mult = 2.0
            is_win = True
            title = "🎳 ПОЧТИ СТРАЙК!"
            comment = "Устояла всего одна кегля! Отличный бросок!"
            details = "9 из 10 кеглей (5/6)"
        elif dice_value == 4:
            mult = 1.4
            is_win = True
            title = "🎳 ХОРОШИЙ БРОСОК!"
            comment = "Сбита большая часть кеглей!"
            details = "Сбито 5-6 кеглей (4/6)"
        elif dice_value == 3:
            mult = 0.8
            is_win = False  # Partial return
            title = "⚡ УТЕШИТЕЛЬНЫЙ РЕЗУЛЬТАТ"
            comment = "Сбито 3 кегли. Возврат 80% от ставки."
            details = "Сбито 3 кегли (3/6)"
        elif dice_value == 2:
            mult = 0.0
            is_win = False
            title = "❌ СЛАБЫЙ БРОСОК"
            comment = "Шар задел лишь одну крайнюю кеглю..."
            details = "Сбита 1 кегля (2/6)"
        else:
            mult = 0.0
            is_win = False
            title = "❌ В ЖЕЛОБ!"
            comment = "Шар скатился в канаву, ни одной сбитой кегли."
            details = "Желоб / 0 кеглей (1/6)"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=(payout > bet),
            title=title,
            comment=comment,
            details=details,
        )


class DartsGame(GameInfo):
    def __init__(self):
        super().__init__(
            code="darts",
            name="Дартс",
            emoji="🎯",
            animation_duration=2.5,
            description="Метните дротик прямо в центр мишени! Попадание в яблочко даёт x4.0!",
            rules_text=(
                "🎯 <b>Правила дартса:</b>\n\n"
                "• 🎯 <b>В ЯБЛОЧКО (Bullseye - центр!)</b> — <b>x4.0</b>\n"
                "• 🔴 <b>Красное кольцо возле центра</b> — <b>x2.5</b>\n"
                "• 🟢 <b>Внутренний сектор мишени</b> — <b>x1.8</b>\n"
                "• ⚪ <b>Внешний сектор мишени</b> — <b>x1.2</b>\n"
                "• ❌ <b>Край щита / промах мимо мишени</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Задержите дыхание и метните дротик!</i>"
            ),
        )

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        # Telegram Darts:
        # 6: Bullseye (center red dot)
        # 5: Red ring around bullseye
        # 4: Inner circle
        # 3: Outer circle
        # 2: Rim / white border
        # 1: Off board
        if dice_value == 6:
            mult = 4.0
            is_win = True
            title = "🎯 ТОЧНО В ЯБЛОЧКО!"
            comment = "Идеальное попадание в самый центр мишени (Bullseye)!"
            details = "Центр мишени (6/6)"
        elif dice_value == 5:
            mult = 2.5
            is_win = True
            title = "🔴 КРАСНОЕ КОЛЬЦО!"
            comment = "Великолепный бросок в сектор возле центра!"
            details = "Около центра (5/6)"
        elif dice_value == 4:
            mult = 1.8
            is_win = True
            title = "🟢 ВНУТРЕННИЙ СЕКТОР!"
            comment = "Отличное попадание в очки!"
            details = "Внутренний круг (4/6)"
        elif dice_value == 3:
            mult = 1.2
            is_win = True
            title = "⚪ ВНЕШНИЙ СЕКТОР!"
            comment = "Дротик попал во внешнее поле мишени."
            details = "Внешний круг (3/6)"
        elif dice_value == 2:
            mult = 0.0
            is_win = False
            title = "❌ ОБОД МИШЕНИ!"
            comment = "Дротик чиркнул по внешнему ободу без очков."
            details = "Обод мишени (2/6)"
        else:
            mult = 0.0
            is_win = False
            title = "❌ В МОЛОКО!"
            comment = "Дротик улетел в стену мимо мишени..."
            details = "Мимо мишени (1/6)"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=is_win,
            title=title,
            comment=comment,
            details=details,
        )


class SlotsGame(GameInfo):
    SLOT_SYMBOLS = {
        0: ("🍫", "BAR"),
        1: ("🍇", "Виноград"),
        2: ("🍋", "Лимон"),
        3: ("7️⃣", "Семёрка"),
    }

    def __init__(self):
        super().__init__(
            code="slots",
            name="Слоты / Рулетка",
            emoji="🎰",
            animation_duration=2.3,
            description="Испытайте удачу в слотах! Три семёрки принесут Джекпот x10!",
            rules_text=(
                "🎰 <b>Правила слотов (Рулетка 777):</b>\n\n"
                "• 7️⃣ 7️⃣ 7️⃣ <b>Три семёрки (ДЖЕКПОТ!)</b> — <b>x10.0</b>\n"
                "• 🍋 🍋 🍋 <b>Три лимона</b> — <b>x5.0</b>\n"
                "• 🍇 🍇 🍇 <b>Три винограда</b> — <b>x4.0</b>\n"
                "• 🍫 🍫 🍫 <b>Три BAR</b> — <b>x3.0</b>\n"
                "• ✨ <b>Две семёрки (7️⃣ 7️⃣)</b> — <b>x2.0</b>\n"
                "• 🎉 <b>Любая другая пара одинаковых</b> — <b>x1.4</b>\n"
                "• ❌ <b>Все символы разные</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Крутите барабаны и сорвите куш!</i>"
            ),
        )

    def decode_reels(self, dice_value: int) -> Tuple[int, int, int]:
        idx = max(0, min(63, dice_value - 1))
        r1 = idx & 3
        r2 = (idx >> 2) & 3
        r3 = (idx >> 4) & 3
        return r1, r2, r3

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        r1, r2, r3 = self.decode_reels(dice_value)
        s1 = self.SLOT_SYMBOLS[r1][0]
        s2 = self.SLOT_SYMBOLS[r2][0]
        s3 = self.SLOT_SYMBOLS[r3][0]
        reels_str = f"[{s1} | {s2} | {s3}]"

        counts: Dict[int, int] = {}
        for r in (r1, r2, r3):
            counts[r] = counts.get(r, 0) + 1

        if 3 in counts and counts[3] == 3:
            mult = 10.0
            is_win = True
            title = "🎰 СУПЕР ДЖЕКПОТ 777!"
            comment = f"Фантастика! Выпали три семёрки {reels_str}! Вы сорвали куш!"
        elif 2 in counts and counts[2] == 3:
            mult = 5.0
            is_win = True
            title = "🍋 ТРИ ЛИМОНА!"
            comment = f"Сочный выигрыш! Выпало три лимона {reels_str}!"
        elif 1 in counts and counts[1] == 3:
            mult = 4.0
            is_win = True
            title = "🍇 ТРИ ВИНОГРАДА!"
            comment = f"Отличная комбинация! Три ягоды {reels_str}!"
        elif 0 in counts and counts[0] == 3:
            mult = 3.0
            is_win = True
            title = "🍫 ТРОЙНОЙ BAR!"
            comment = f"Классический трипл! Три плашки BAR {reels_str}!"
        elif 3 in counts and counts[3] == 2:
            mult = 2.0
            is_win = True
            title = "✨ ДВЕ СЕМЁРКИ!"
            comment = f"Две семёрки на барабанах {reels_str}! Отличный приз!"
        elif any(c == 2 for c in counts.values()):
            mult = 1.4
            is_win = True
            title = "🎉 ВЫИГРЫШНАЯ ПАРА!"
            comment = f"Совпала пара символов {reels_str}!"
        else:
            mult = 0.0
            is_win = False
            title = "❌ НЕТ СОВПАДЕНИЙ"
            comment = f"Все символы разные {reels_str}. В этот раз не повезло!"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=is_win,
            title=title,
            comment=comment,
            details=f"Комбинация: {reels_str}",
        )


class DiceGame(GameInfo):
    def __init__(self):
        super().__init__(
            code="dice",
            name="Кости",
            emoji="🎲",
            animation_duration=2.5,
            description="Классический бросок игрального кубика. Шестёрка утраивает ставку!",
            rules_text=(
                "🎲 <b>Правила классических костей:</b>\n\n"
                "• ⚅ <b>Выпало 6 (Шестёрка!)</b> — <b>x3.0</b>\n"
                "• ⚄ <b>Выпало 5 (Пятёрка!)</b> — <b>x2.0</b>\n"
                "• ⚃ <b>Выпало 4 (Четвёрка!)</b> — <b>x1.5</b>\n"
                "• ⚂ <b>Выпало 3 (Тройка)</b> — <b>x1.0</b> (возврат ставки)\n"
                "• ❌ <b>Выпало 1 или 2</b> — <b>x0.0</b> (ставка сгорает)\n\n"
                "<i>Бросайте кубик и пусть фортуна будет на вашей стороне!</i>"
            ),
        )

    def calculate(self, dice_value: int, bet: int) -> GameResult:
        dice_art = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        art = dice_art.get(dice_value, str(dice_value))

        if dice_value == 6:
            mult = 3.0
            is_win = True
            title = f"🎲 ШЕСТЁРКА {art}!"
            comment = "Высший результат на кубике! Ставка умножена в 3 раза!"
            details = f"Выпало {dice_value}"
        elif dice_value == 5:
            mult = 2.0
            is_win = True
            title = f"🎲 ПЯТЁРКА {art}!"
            comment = "Отличный бросок! Удвоение ставки!"
            details = f"Выпало {dice_value}"
        elif dice_value == 4:
            mult = 1.5
            is_win = True
            title = f"🎲 ЧЕТВЁРКА {art}!"
            comment = "Хороший результат! Прибыль 50%!"
            details = f"Выпало {dice_value}"
        elif dice_value == 3:
            mult = 1.0
            is_win = True
            title = f"🎲 ТРОЙКА {art}"
            comment = "Возврат ставки. Ваш баланс сохранен!"
            details = f"Выпало {dice_value}"
        elif dice_value == 2:
            mult = 0.0
            is_win = False
            title = f"❌ ДВОЙКА {art}"
            comment = "Слишком мало... Ставка сгорает."
            details = f"Выпало {dice_value}"
        else:
            mult = 0.0
            is_win = False
            title = f"❌ ЕДИНИЦА {art}"
            comment = "Минимальное значение на кубике... Ставка сгорает."
            details = f"Выпало {dice_value}"

        payout = int(bet * mult)
        net_profit = payout - bet
        return GameResult(
            dice_value=dice_value,
            multiplier=mult,
            bet=bet,
            payout=payout,
            net_profit=net_profit,
            is_win=(payout >= bet),
            title=title,
            comment=comment,
            details=details,
        )


def calculate_dice_guess(dice_value: int, targets: set, bet: int) -> GameResult:
    """
    Расчет выигрыша при угадывании чисел на кубике:
    - 1 число (например, "кости 3") -> x5.0
    - 2 числа (например, "кости 3 5") -> x3.0
    - 3 числа (например, "кости 1 2 3", "кости чет") -> x2.0
    - 4 числа -> x1.4
    - 5 чисел -> x1.15
    """
    dice_art = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    art = dice_art.get(dice_value, str(dice_value))
    sorted_targets = sorted(list(targets))
    targets_str = ", ".join(str(t) for t in sorted_targets)

    count = len(targets)
    mult_table = {
        1: 5.0,
        2: 3.0,
        3: 2.0,
        4: 1.4,
        5: 1.15,
    }
    target_mult = mult_table.get(count, 1.0)

    if dice_value in targets:
        mult = target_mult
        is_win = True
        title = f"🎯 ТОЧНО В ЦЕЛЬ! Выпало {dice_value} {art}!"
        comment = f"Вы ставили на [{targets_str}]. Ваше число сыграло!"
    else:
        mult = 0.0
        is_win = False
        title = f"❌ НЕ УГАДАЛИ! Выпало {dice_value} {art}"
        comment = f"Вы ставили на [{targets_str}], но выпало другое число."

    payout = int(bet * mult)
    net_profit = payout - bet
    details = f"Цели: [{targets_str}] | Выпало: {dice_value}"

    return GameResult(
        dice_value=dice_value,
        multiplier=mult,
        bet=bet,
        payout=payout,
        net_profit=net_profit,
        is_win=is_win,
        title=title,
        comment=comment,
        details=details,
    )


# Реестр всех игр
GAMES: Dict[str, GameInfo] = {
    "basketball": BasketballGame(),
    "football": FootballGame(),
    "bowling": BowlingGame(),
    "darts": DartsGame(),
    "slots": SlotsGame(),
    "dice": DiceGame(),
}


def get_game(code: str) -> Optional[GameInfo]:
    return GAMES.get(code)
