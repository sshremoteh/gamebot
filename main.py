import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, DB_PATH
from bot.database import db
from bot.handlers import (
    start_router,
    game_router,
    text_games_router,
    profile_router,
    bonus_router,
    leaderboard_router,
    rules_router,
)

# Настройка красивого логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("GameBot")


async def setup_bot_commands(bot: Bot):
    """Устанавливает список команд в меню Telegram."""
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="profile", description="👤 Мой профиль и баланс"),
        BotCommand(command="bonus", description="🎁 Ежедневный бонус"),
        BotCommand(command="top", description="🏆 Таблица лидеров"),
        BotCommand(command="rules", description="ℹ️ Правила и множители"),
        BotCommand(command="bailout", description="🆘 Помощь банкроту"),
        BotCommand(command="help", description="📖 Справка"),
    ]
    await bot.set_my_commands(commands)


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "\n" + "=" * 60 + "\n"
            "❌ ОШИБКА: Токен Telegram-бота не установлен!\n\n"
            "Как запустить бота:\n"
            "1. Откройте Telegram и напишите боту @BotFather\n"
            "2. Создайте нового бота командой /newbot и скопируйте токен\n"
            "3. Вставьте полученный токен в файл .env:\n"
            "   BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ\n"
            "4. Запустите бота снова: python main.py\n"
            + "=" * 60
        )
        sys.exit(1)

    logger.info("Инициализация базы данных SQLite (%s)...", DB_PATH)
    await db.init()
    logger.info("База данных успешно инициализирована.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация всех роутеров
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(text_games_router)
    dp.include_router(profile_router)
    dp.include_router(bonus_router)
    dp.include_router(leaderboard_router)
    dp.include_router(rules_router)

    # Установка подсказок команд в Telegram
    await setup_bot_commands(bot)

    logger.info("Запуск Telegram GameBot в режиме Polling...")
    # Удаляем накопившиеся апдейты, чтобы бот не спамил старыми ответами
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Бот успешно остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Выключение бота...")
