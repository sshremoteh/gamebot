from .start import router as start_router
from .game import router as game_router
from .text_games import router as text_games_router
from .profile import router as profile_router
from .bonus import router as bonus_router
from .leaderboard import router as leaderboard_router
from .rules import router as rules_router

__all__ = [
    "start_router",
    "game_router",
    "text_games_router",
    "profile_router",
    "bonus_router",
    "leaderboard_router",
    "rules_router",
]
