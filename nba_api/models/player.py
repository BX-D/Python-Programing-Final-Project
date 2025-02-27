from typing import Optional, List, Dict
from pydantic import BaseModel

class Team(BaseModel):
    """Team information model."""
    id: int
    full_name: str
    abbreviation: str
    conference: Optional[str] = None
    division: Optional[str] = None
    city: Optional[str] = None
    name: Optional[str] = None

class PlayerBase(BaseModel):
    """Base player information model."""
    id: int
    first_name: str
    last_name: str
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    jersey_number: Optional[str] = None
    college: Optional[str] = None
    country: Optional[str] = None

class Player(PlayerBase):
    """Complete player model including team information."""
    team: Optional[Team] = None
    
    @property
    def full_name(self) -> str:
        """Get the player's full name."""
        return f"{self.first_name} {self.last_name}"

class PlayerStat(BaseModel):
    """Player statistics model."""
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: Optional[float] = None
    fg3_pct: Optional[float] = None
    ft_pct: Optional[float] = None
    turnover: Optional[float] = None
    min: Optional[str] = None
    games_played: Optional[int] = None
    season: Optional[int] = None

class PlayerWithStats(Player):
    """Player model including statistics."""
    stats: Optional[PlayerStat] = None
    
class SearchResponse(BaseModel):
    """Response model for player search."""
    count: int
    results: List[Player]