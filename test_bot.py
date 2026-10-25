import asyncio
import os
import unittest
from bot.games import (
    BasketballGame,
    FootballGame,
    BowlingGame,
    DartsGame,
    SlotsGame,
    DiceGame,
    calculate_dice_guess,
    GAMES,
)
from bot.handlers.text_games import parse_bet_value, parse_dice_text
from bot.database import Database


class TestGameBotLogic(unittest.TestCase):
    def test_basketball_multipliers(self):
        bball = BasketballGame()
        bet = 1000

        # Чистый трехочковый (5) -> x3
        res5 = bball.calculate(5, bet)
        self.assertEqual(res5.multiplier, 3.0)
        self.assertEqual(res5.payout, 3000)
        self.assertEqual(res5.net_profit, 2000)
        self.assertTrue(res5.is_win)

        # Обычное попадание (4) -> x1.5
        res4 = bball.calculate(4, bet)
        self.assertEqual(res4.multiplier, 1.5)
        self.assertEqual(res4.payout, 1500)
        self.assertEqual(res4.net_profit, 500)
        self.assertTrue(res4.is_win)

        # Промахи (1, 2, 3) -> сгорает (x0)
        for val in (1, 2, 3):
            res = bball.calculate(val, bet)
            self.assertEqual(res.multiplier, 0.0)
            self.assertEqual(res.payout, 0)
            self.assertEqual(res.net_profit, -1000)
            self.assertFalse(res.is_win)

    def test_football_multipliers(self):
        fb = FootballGame()
        bet = 1000

        # В девятку (5) -> x3.0
        res5 = fb.calculate(5, bet)
        self.assertEqual(res5.multiplier, 3.0)
        self.assertEqual(res5.payout, 3000)

        # В угол (4) -> x2.0
        res4 = fb.calculate(4, bet)
        self.assertEqual(res4.multiplier, 2.0)
        self.assertEqual(res4.payout, 2000)

        # Гол (3) -> x1.5
        res3 = fb.calculate(3, bet)
        self.assertEqual(res3.multiplier, 1.5)
        self.assertEqual(res3.payout, 1500)

        # Промах / штанга (1, 2) -> x0
        for val in (1, 2):
            res = fb.calculate(val, bet)
            self.assertEqual(res.multiplier, 0.0)
            self.assertEqual(res.payout, 0)

    def test_bowling_multipliers(self):
        bowling = BowlingGame()
        bet = 1000

        # Страйк (6) -> x3.5
        res6 = bowling.calculate(6, bet)
        self.assertEqual(res6.multiplier, 3.5)
        self.assertEqual(res6.payout, 3500)

        # 9 кеглей (5) -> x2.0
        res5 = bowling.calculate(5, bet)
        self.assertEqual(res5.multiplier, 2.0)
        self.assertEqual(res5.payout, 2000)

        # 5-6 кеглей (4) -> x1.4
        res4 = bowling.calculate(4, bet)
        self.assertEqual(res4.multiplier, 1.4)
        self.assertEqual(res4.payout, 1400)

        # 3 кегли (3) -> x0.8
        res3 = bowling.calculate(3, bet)
        self.assertEqual(res3.multiplier, 0.8)
        self.assertEqual(res3.payout, 800)

        # 0-1 кегли (1, 2) -> x0.0
        for val in (1, 2):
            res = bowling.calculate(val, bet)
            self.assertEqual(res.multiplier, 0.0)
            self.assertEqual(res.payout, 0)

    def test_darts_multipliers(self):
        darts = DartsGame()
        bet = 1000

        # Яблочко (6) -> x4.0
        res6 = darts.calculate(6, bet)
        self.assertEqual(res6.multiplier, 4.0)
        self.assertEqual(res6.payout, 4000)

        # Красное кольцо (5) -> x2.5
        res5 = darts.calculate(5, bet)
        self.assertEqual(res5.multiplier, 2.5)
        self.assertEqual(res5.payout, 2500)

        # Внутренний сектор (4) -> x1.8
        res4 = darts.calculate(4, bet)
        self.assertEqual(res4.multiplier, 1.8)
        self.assertEqual(res4.payout, 1800)

        # Внешний сектор (3) -> x1.2
        res3 = darts.calculate(3, bet)
        self.assertEqual(res3.multiplier, 1.2)
        self.assertEqual(res3.payout, 1200)

        # Мимо (1, 2) -> x0.0
        for val in (1, 2):
            res = darts.calculate(val, bet)
            self.assertEqual(res.multiplier, 0.0)
            self.assertEqual(res.payout, 0)

    def test_slots_multipliers(self):
        slots = SlotsGame()
        bet = 1000

        # 777 (val 64) -> x10
        res64 = slots.calculate(64, bet)
        self.assertEqual(res64.multiplier, 10.0)
        self.assertEqual(res64.payout, 10000)

        # Лимоны (val 43) -> x5
        res43 = slots.calculate(43, bet)
        self.assertEqual(res43.multiplier, 5.0)
        self.assertEqual(res43.payout, 5000)

        # Виноград (val 22) -> x4
        res22 = slots.calculate(22, bet)
        self.assertEqual(res22.multiplier, 4.0)
        self.assertEqual(res22.payout, 4000)

        # BAR (val 1) -> x3
        res1 = slots.calculate(1, bet)
        self.assertEqual(res1.multiplier, 3.0)
        self.assertEqual(res1.payout, 3000)

    def test_dice_multipliers(self):
        dice = DiceGame()
        bet = 1000

        # 6 -> x3.0
        self.assertEqual(dice.calculate(6, bet).multiplier, 3.0)
        # 5 -> x2.0
        self.assertEqual(dice.calculate(5, bet).multiplier, 2.0)
        # 4 -> x1.5
        self.assertEqual(dice.calculate(4, bet).multiplier, 1.5)
        # 3 -> x1.0
        self.assertEqual(dice.calculate(3, bet).multiplier, 1.0)
        # 1, 2 -> x0.0
        self.assertEqual(dice.calculate(2, bet).multiplier, 0.0)
        self.assertEqual(dice.calculate(1, bet).multiplier, 0.0)

    def test_dice_guessing(self):
        bet = 1000

        # Угадывание 1 числа ("кости 3"): если выпадает 3 -> x5
        res1_win = calculate_dice_guess(dice_value=3, targets={3}, bet=bet)
        self.assertEqual(res1_win.multiplier, 5.0)
        self.assertEqual(res1_win.payout, 5000)
        self.assertTrue(res1_win.is_win)

        res1_loss = calculate_dice_guess(dice_value=2, targets={3}, bet=bet)
        self.assertEqual(res1_loss.multiplier, 0.0)
        self.assertEqual(res1_loss.payout, 0)
        self.assertFalse(res1_loss.is_win)

        # Угадывание 2 чисел ("кости 3 5"): если выпадает 3 или 5 -> x3
        res2_win = calculate_dice_guess(dice_value=5, targets={3, 5}, bet=bet)
        self.assertEqual(res2_win.multiplier, 3.0)
        self.assertEqual(res2_win.payout, 3000)
        self.assertTrue(res2_win.is_win)

        res2_loss = calculate_dice_guess(dice_value=1, targets={3, 5}, bet=bet)
        self.assertEqual(res2_loss.multiplier, 0.0)
        self.assertEqual(res2_loss.payout, 0)
        self.assertFalse(res2_loss.is_win)

        # Угадывание 3 чисел (чет/нечет): x2.0
        res3_win = calculate_dice_guess(dice_value=6, targets={2, 4, 6}, bet=bet)
        self.assertEqual(res3_win.multiplier, 2.0)
        self.assertEqual(res3_win.payout, 2000)
        self.assertTrue(res3_win.is_win)

    def test_text_bet_parsing(self):
        bal = 10000
        self.assertEqual(parse_bet_value("100", bal), 100)
        self.assertEqual(parse_bet_value("100 монет", bal), 100)
        self.assertEqual(parse_bet_value("500 монет", bal), 500)
        self.assertEqual(parse_bet_value("1к", bal), 1000)
        self.assertEqual(parse_bet_value("2.5k", bal), 2500)
        self.assertEqual(parse_bet_value("вабанк", bal), 10000)

    def test_dice_text_parsing(self):
        bal = 10000
        default_bet = 250

        # "кости" -> классика
        mode, targets, bet = parse_dice_text("кости", bal, default_bet)
        self.assertEqual(mode, "classic")
        self.assertIsNone(targets)
        self.assertEqual(bet, 250)

        # "кости 3" -> угадывание {3}
        mode, targets, bet = parse_dice_text("кости 3", bal, default_bet)
        self.assertEqual(mode, "guess")
        self.assertEqual(targets, {3})
        self.assertEqual(bet, 250)

        # "кости 3 5" -> угадывание {3, 5}
        mode, targets, bet = parse_dice_text("кости 3 5", bal, default_bet)
        self.assertEqual(mode, "guess")
        self.assertEqual(targets, {3, 5})
        self.assertEqual(bet, 250)

        # "кости 3 5 500" -> угадывание {3, 5} со ставкой 500
        mode, targets, bet = parse_dice_text("кости 3 5 500", bal, default_bet)
        self.assertEqual(mode, "guess")
        self.assertEqual(targets, {3, 5})
        self.assertEqual(bet, 500)

        # "кости чет 1000" -> угадывание {2, 4, 6} со ставкой 1000
        mode, targets, bet = parse_dice_text("кости чет 1000", bal, default_bet)
        self.assertEqual(mode, "guess")
        self.assertEqual(targets, {2, 4, 6})
        self.assertEqual(bet, 1000)

        # "кости 500" -> классика со ставкой 500
        mode, targets, bet = parse_dice_text("кости 500", bal, default_bet)
        self.assertEqual(mode, "classic")
        self.assertIsNone(targets)
        self.assertEqual(bet, 500)


class TestDatabaseAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_db_path = "test_gamebot.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = Database(db_path=self.test_db_path)
        await self.db.init()

    async def asyncTearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    async def test_user_creation_and_balance(self):
        user, is_new = await self.db.get_or_create_user(999, "alex", "Alex")
        self.assertTrue(is_new)
        self.assertEqual(user["balance"], 10000)

        # Getting existing user
        user2, is_new2 = await self.db.get_or_create_user(999, "alex", "Alex Updated")
        self.assertFalse(is_new2)
        self.assertEqual(user2["balance"], 10000)
        self.assertEqual(user2["first_name"], "Alex Updated")

    async def test_betting_flow(self):
        await self.db.get_or_create_user(100, "player", "Player")

        # Reserve bet of 2,000
        ok, bal, err = await self.db.reserve_bet(100, 2000)
        self.assertTrue(ok)
        self.assertEqual(bal, 8000)

        # Record win of 6,000 (x3.0)
        final_bal = await self.db.record_game_outcome(
            user_id=100,
            game_code="basketball",
            emoji="🏀",
            bet=2000,
            dice_value=5,
            multiplier=3.0,
            payout=6000,
            net_profit=4000,
        )
        self.assertEqual(final_bal, 14000)

        # Check history
        history = await self.db.get_user_history(100, 5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["multiplier"], 3.0)
        self.assertEqual(history[0]["payout"], 6000)

    async def test_insufficient_balance(self):
        await self.db.get_or_create_user(200, "poor_player", "Poor")
        # Try to bet 20,000 when starting balance is 10,000
        ok, bal, err = await self.db.reserve_bet(200, 20000)
        self.assertFalse(ok)
        self.assertIn("Недостаточно монет", err)

    async def test_set_and_get_user_bet(self):
        await self.db.get_or_create_user(300, "bettor", "Bettor")
        bet = await self.db.get_user_bet(300)
        self.assertEqual(bet, 250)

        await self.db.set_user_bet(300, 1000)
        updated_bet = await self.db.get_user_bet(300)
        self.assertEqual(updated_bet, 1000)


if __name__ == "__main__":
    unittest.main()
