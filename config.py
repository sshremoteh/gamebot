import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# База данных
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "gamebot.db"))

# Игровой баланс и ставки
STARTING_BALANCE: int = int(os.getenv("STARTING_BALANCE", "10000"))
MIN_BET: int = int(os.getenv("MIN_BET", "10"))
MAX_BET: int = int(os.getenv("MAX_BET", "1000000"))
DEFAULT_BET: int = 250

# Бонусы
DAILY_BONUS_MIN: int = 1000
DAILY_BONUS_MAX: int = 2500
BAILOUT_THRESHOLD: int = 50   # Если баланс ниже этого значения, доступна помощь банкроту
BAILOUT_AMOUNT: int = 1000    # Сумма помощи банкроту
BAILOUT_COOLDOWN_HOURS: int = 1
