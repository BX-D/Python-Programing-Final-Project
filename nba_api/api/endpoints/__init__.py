from .players import router as players_router
from .calendar import router as calendar_router
from .stats import router as stats_router

__all__ = ["players_router", "calendar_router", "stats_router"]