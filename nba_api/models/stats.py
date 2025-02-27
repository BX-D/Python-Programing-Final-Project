from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class SeasonStat(BaseModel):
    """Statistics for a single season."""
    pts: float = Field(..., description="Points per game")
    reb: float = Field(..., description="Rebounds per game")
    ast: float = Field(..., description="Assists per game")
    stl: float = Field(..., description="Steals per game")
    blk: float = Field(..., description="Blocks per game")
    turnover: float = Field(..., description="Turnovers per game")
    fg_pct: float = Field(..., description="Field goal percentage")
    fg3_pct: float = Field(..., description="3-point percentage")
    ft_pct: float = Field(..., description="Free throw percentage")
    min: float = Field(..., description="Minutes played per game")
    games_played: int = Field(..., description="Number of games played")

class PlayerSummary(BaseModel):
    """Summary information about a player."""
    id: int = Field(..., description="Player ID")
    name: str = Field(..., description="Player's full name")
    team: Optional[str] = Field(None, description="Player's current team")

class SeasonGrowth(BaseModel):
    """Growth/decline between seasons for various metrics."""
    pts: Optional[float] = Field(None, description="Points growth percentage")
    reb: Optional[float] = Field(None, description="Rebounds growth percentage")
    ast: Optional[float] = Field(None, description="Assists growth percentage")
    stl: Optional[float] = Field(None, description="Steals growth percentage")
    blk: Optional[float] = Field(None, description="Blocks growth percentage")
    fg_pct: Optional[float] = Field(None, description="Field goal percentage growth")
    fg3_pct: Optional[float] = Field(None, description="3-point percentage growth")
    ft_pct: Optional[float] = Field(None, description="Free throw percentage growth")

class StatisticsComparison(BaseModel):
    """Complete comparison of player statistics across seasons."""
    player: PlayerSummary = Field(..., description="Player information")
    seasons: List[int] = Field(..., description="Seasons included in the comparison")
    season_averages: Dict[str, Optional[Dict[str, Any]]] = Field(..., description="Statistics by season")
    growth: Dict[str, Optional[SeasonGrowth]] = Field(..., description="Growth between seasons")
    metrics: List[str] = Field(..., description="Metrics included in the comparison")

class StatisticsRequest(BaseModel):
    """Request model for statistics comparison."""
    seasons: List[int] = Field(..., description="Seasons to compare")