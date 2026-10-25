from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.games import GAMES, get_game


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 ИГРАТЬ (Выбор игры)", callback_data="menu:games"),
            ],
            [
                InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu:profile"),
                InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="menu:bonus"),
            ],
            [
                InlineKeyboardButton(text="🏆 Топ игроков", callback_data="menu:leaderboard"),
                InlineKeyboardButton(text="ℹ️ Правила и множители", callback_data="menu:rules"),
            ],
            [
                InlineKeyboardButton(text="🆘 Второе дыхание (Банкрот)", callback_data="menu:bailout"),
            ],
        ]
    )


def get_games_selection_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора одной из 6 интерактивных игр."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏀 Баскетбол (x3 / x1.5)", callback_data="select_game:basketball"
                ),
                InlineKeyboardButton(
                    text="⚽ Футбол (x3 / x2 / x1.5)", callback_data="select_game:football"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎳 Боулинг (Страйк x3.5)", callback_data="select_game:bowling"
                ),
                InlineKeyboardButton(
                    text="🎯 Дартс (Яблочко x4)", callback_data="select_game:darts"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎰 Слоты 777 (Джекпот x10)", callback_data="select_game:slots"
                ),
                InlineKeyboardButton(
                    text="🎲 Кости (x3 / x2 / x1.5)", callback_data="select_game:dice"
                ),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


def get_game_interface_kb(
    game_code: str, current_bet: int, user_balance: int
) -> InlineKeyboardMarkup:
    """Интерфейс игры: кнопка броска, быстрые ставки, ввод ставки и навигация."""
    game = get_game(game_code)
    emoji = game.emoji if game else "🎲"
    name = game.name if game else "Игра"

    action_text = {
        "basketball": f"{emoji} БРОСИТЬ МЯЧ ({current_bet:,} 🪙)",
        "football": f"{emoji} ПРОБИТЬ ПЕНАЛЬТИ ({current_bet:,} 🪙)",
        "bowling": f"{emoji} КАТИТЬ ШАР ({current_bet:,} 🪙)",
        "darts": f"{emoji} МЕТНУТЬ ДРОТИК ({current_bet:,} 🪙)",
        "slots": f"{emoji} КРУТИТЬ БАРАБАНЫ ({current_bet:,} 🪙)",
        "dice": f"{emoji} БРОСИТЬ КУБИК ({current_bet:,} 🪙)",
    }.get(game_code, f"{emoji} ИГРАТЬ ({current_bet:,} 🪙)")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔥 {action_text}",
                    callback_data=f"play:{game_code}:{current_bet}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="100 🪙", callback_data=f"set_bet:{game_code}:100"
                ),
                InlineKeyboardButton(
                    text="250 🪙", callback_data=f"set_bet:{game_code}:250"
                ),
                InlineKeyboardButton(
                    text="500 🪙", callback_data=f"set_bet:{game_code}:500"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="1,000 🪙", callback_data=f"set_bet:{game_code}:1000"
                ),
                InlineKeyboardButton(
                    text="2,500 🪙", callback_data=f"set_bet:{game_code}:2500"
                ),
                InlineKeyboardButton(
                    text=f"Ва-банк ({user_balance:,} 🪙)",
                    callback_data=f"set_bet:{game_code}:{user_balance}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Своя ставка", callback_data=f"custom_bet:{game_code}"
                ),
                InlineKeyboardButton(
                    text="📜 Правила этой игры",
                    callback_data=f"game_rules:{game_code}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Другая игра", callback_data="menu:games"
                ),
                InlineKeyboardButton(
                    text="🏠 В меню", callback_data="menu:main"
                ),
            ],
        ]
    )


def get_after_game_kb(game_code: str, current_bet: int) -> InlineKeyboardMarkup:
    """Кнопки после окончания броска: повторить, изменить ставку, сменить игру."""
    game = get_game(game_code)
    emoji = game.emoji if game else "🎲"

    repeat_text = {
        "basketball": f"🔄 Еще бросок ({current_bet:,} 🪙)",
        "football": f"🔄 Еще удар ({current_bet:,} 🪙)",
        "bowling": f"🔄 Еще бросок ({current_bet:,} 🪙)",
        "darts": f"🔄 Еще дротик ({current_bet:,} 🪙)",
        "slots": f"🔄 Крутить еще ({current_bet:,} 🪙)",
        "dice": f"🔄 Бросить еще ({current_bet:,} 🪙)",
    }.get(game_code, f"🔄 Играть снова ({current_bet:,} 🪙)")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=repeat_text,
                    callback_data=f"play:{game_code}:{current_bet}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Изменить ставку",
                    callback_data=f"select_game:{game_code}",
                ),
                InlineKeyboardButton(
                    text="🎮 Другая игра", callback_data="menu:games"
                ),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )


def get_cancel_bet_kb(game_code: str) -> InlineKeyboardMarkup:
    """Кнопка отмены ввода кастомной ставки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=f"select_game:{game_code}"
                )
            ]
        ]
    )


def get_back_to_menu_kb() -> InlineKeyboardMarkup:
    """Универсальная кнопка возврата в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ]
        ]
    )


def get_rules_menu_kb() -> InlineKeyboardMarkup:
    """Кнопки выбора правил для конкретных игр."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏀 Баскетбол", callback_data="game_rules:basketball"
                ),
                InlineKeyboardButton(
                    text="⚽ Футбол", callback_data="game_rules:football"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎳 Боулинг", callback_data="game_rules:bowling"
                ),
                InlineKeyboardButton(
                    text="🎯 Дартс", callback_data="game_rules:darts"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎰 Слоты 777", callback_data="game_rules:slots"
                ),
                InlineKeyboardButton(
                    text="🎲 Кости", callback_data="game_rules:dice"
                ),
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main"),
            ],
        ]
    )
