from .endpoints.players import router as players_router
from .endpoints.calendar import router as calendar_router
from .endpoints.stats import router as stats_router

__all__ = ["players_router", "calendar_router", "stats_router"]