import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
import aiosqlite

from config import (
    DB_PATH,
    STARTING_BALANCE,
    DAILY_BONUS_MIN,
    DAILY_BONUS_MAX,
    BAILOUT_THRESHOLD,
    BAILOUT_AMOUNT,
    BAILOUT_COOLDOWN_HOURS,
)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init(self):
        """Создает таблицы базы данных при первом запуске."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance INTEGER DEFAULT 10000,
                    current_bet INTEGER DEFAULT 250,
                    created_at TEXT NOT NULL,
                    last_daily_bonus TEXT,
                    last_bailout TEXT,
                    total_games INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    total_won_amount INTEGER DEFAULT 0,
                    total_lost_amount INTEGER DEFAULT 0,
                    biggest_win INTEGER DEFAULT 0
                )
                """
            )

            # Миграция: добавляем current_bet в существующие БД, если его еще нет
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "current_bet" not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN current_bet INTEGER DEFAULT 250")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS games_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_code TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    bet INTEGER NOT NULL,
                    dice_value INTEGER NOT NULL,
                    multiplier REAL NOT NULL,
                    payout INTEGER NOT NULL,
                    net_profit INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                """
            )
            await db.commit()

    async def get_or_create_user(
        self, user_id: int, username: Optional[str], first_name: Optional[str]
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Возвращает данные пользователя и флаг is_new (True, если пользователь только что создан со стартовым балансом 10,000).
        """
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()

            if row is not None:
                # Обновим имя и юзернейм если изменились
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id),
                )
                await db.commit()
                # Получаем свежие данные
                cursor = await db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row), False
            else:
                # Создаем нового пользователя с 10,000 монет
                await db.execute(
                    """
                    INSERT INTO users (
                        user_id, username, first_name, balance, created_at,
                        total_games, total_wins, total_losses,
                        total_won_amount, total_lost_amount, biggest_win
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0)
                    """,
                    (user_id, username, first_name, STARTING_BALANCE, now_str),
                )
                await db.commit()
                cursor = await db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                )
                row = await cursor.fetchone()
                return dict(row), True

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по user_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def reserve_bet(self, user_id: int, bet: int) -> Tuple[bool, int, str]:
        """
        Резервирует (списывает) ставку перед броском кубика.
        Возвращает (success, new_balance, error_message).
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT balance FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return False, 0, "Пользователь не найден."

            current_balance = row["balance"]
            if current_balance < bet:
                return False, current_balance, f"Недостаточно монет! Ваш баланс: {current_balance:,} 🪙"

            new_balance = current_balance - bet
            await db.execute(
                "UPDATE users SET balance = ? WHERE user_id = ?",
                (new_balance, user_id),
            )
            await db.commit()
            return True, new_balance, ""

    async def record_game_outcome(
        self,
        user_id: int,
        game_code: str,
        emoji: str,
        bet: int,
        dice_value: int,
        multiplier: float,
        payout: int,
        net_profit: int,
    ) -> int:
        """
        Начисляет выигрыш (payout) после броска, обновляет статистику игрока и сохраняет игру в историю.
        Возвращает итоговый баланс.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT balance, biggest_win FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            current_balance = row["balance"] if row else 0
            old_biggest_win = row["biggest_win"] if row else 0

            new_balance = current_balance + payout
            new_biggest_win = max(old_biggest_win, payout)

            is_win = payout > bet
            win_inc = 1 if is_win else 0
            loss_inc = 0 if is_win else 1
            won_amount_inc = payout if is_win else 0
            lost_amount_inc = bet if not is_win else 0

            await db.execute(
                """
                UPDATE users SET
                    balance = ?,
                    total_games = total_games + 1,
                    total_wins = total_wins + ?,
                    total_losses = total_losses + ?,
                    total_won_amount = total_won_amount + ?,
                    total_lost_amount = total_lost_amount + ?,
                    biggest_win = ?
                WHERE user_id = ?
                """,
                (
                    new_balance,
                    win_inc,
                    loss_inc,
                    won_amount_inc,
                    lost_amount_inc,
                    new_biggest_win,
                    user_id,
                ),
            )

            await db.execute(
                """
                INSERT INTO games_history (
                    user_id, game_code, emoji, bet, dice_value, multiplier, payout, net_profit, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    game_code,
                    emoji,
                    bet,
                    dice_value,
                    multiplier,
                    payout,
                    net_profit,
                    now_str,
                ),
            )

            await db.commit()
            return new_balance

    async def refund_bet(self, user_id: int, bet: int) -> int:
        """Возвращает ставку на баланс в случае системной ошибки."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (bet, user_id),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT balance FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return row["balance"] if row else 0

    async def claim_daily_bonus(
        self, user_id: int, bonus_amount: int
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Выдает ежедневный бонус.
        Возвращает (success, new_balance, remaining_seconds).
        """
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT balance, last_daily_bonus FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return False, 0, None

            last_bonus_str = row["last_daily_bonus"]
            if last_bonus_str:
                last_bonus_time = datetime.fromisoformat(last_bonus_str)
                time_passed = now - last_bonus_time
                cooldown = timedelta(hours=24)
                if time_passed < cooldown:
                    remaining = int((cooldown - time_passed).total_seconds())
                    return False, row["balance"], remaining

            new_balance = row["balance"] + bonus_amount
            await db.execute(
                "UPDATE users SET balance = ?, last_daily_bonus = ? WHERE user_id = ?",
                (new_balance, now_str, user_id),
            )
            await db.commit()
            return True, new_balance, None

    async def claim_bailout(self, user_id: int) -> Tuple[bool, int, str]:
        """
        Помощь при банкротстве. Если баланс < 50, начисляет 1,000 монет.
        """
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT balance, last_bailout FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return False, 0, "Пользователь не найден."

            balance = row["balance"]
            if balance >= BAILOUT_THRESHOLD:
                return (
                    False,
                    balance,
                    f"Ваш баланс ({balance:,} 🪙) превышает порог банкротства ({BAILOUT_THRESHOLD} 🪙). Помощь доступна только когда почти не осталось монет!",
                )

            last_bailout_str = row["last_bailout"]
            if last_bailout_str:
                last_time = datetime.fromisoformat(last_bailout_str)
                time_passed = now - last_time
                cooldown = timedelta(hours=BAILOUT_COOLDOWN_HOURS)
                if time_passed < cooldown:
                    minutes_left = int(
                        (cooldown - time_passed).total_seconds() // 60
                    ) + 1
                    return (
                        False,
                        balance,
                        f"Помощь банкроту уже была получена недавно. Подождите еще {minutes_left} мин.",
                    )

            new_balance = balance + BAILOUT_AMOUNT
            await db.execute(
                "UPDATE users SET balance = ?, last_bailout = ? WHERE user_id = ?",
                (new_balance, now_str, user_id),
            )
            await db.commit()
            return True, new_balance, f"Вам начислено +{BAILOUT_AMOUNT:,} 🪙 второго дыхания!"

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Топ игроков по балансу."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT user_id, username, first_name, balance, total_games, total_wins
                FROM users
                ORDER BY balance DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_user_history(
        self, user_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Последние игры пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT game_code, emoji, bet, dice_value, multiplier, payout, net_profit, created_at
                FROM games_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def set_user_bet(self, user_id: int, bet: int) -> int:
        """Сохраняет выбранную ставку игрока в базе данных."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET current_bet = ? WHERE user_id = ?",
                (bet, user_id),
            )
            await db.commit()
            return bet

    async def get_user_bet(self, user_id: int) -> int:
        """Получает сохраненную ставку игрока (по умолчанию 250)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT current_bet, balance FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return 250
            bet = row["current_bet"] or 250
            return bet


db = Database()
