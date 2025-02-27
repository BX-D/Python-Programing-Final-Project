from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from nba_api.client import BallDontLieClient
from nba_api.models.player import Player, PlayerWithStats, SearchResponse, PlayerStat
import os

router = APIRouter(
    prefix="/players",
    tags=["players"],
    responses={404: {"description": "Not found"}},
)

def get_client():
    """Dependency to get a BallDontLie API client instance."""
    api_key = os.environ.get("BALLDONTLIE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return BallDontLieClient(api_key)

@router.get("/search/", response_model=SearchResponse)
def search_players(
    name: str = Query(..., description="Name to search for"),
    client: BallDontLieClient = Depends(get_client)
):
    """
    Search for players by name.
    
    This endpoint searches for NBA players whose names match the provided search term.
    Results are returned in order of relevance.
    """
    players = client.search_players(name)
    
    # Convert to Pydantic models
    player_models = [Player(**player) for player in players]
    
    return {
        "count": len(player_models),
        "results": player_models
    }

@router.get("/{player_id}", response_model=Player)
def get_player(
    player_id: int,
    client: BallDontLieClient = Depends(get_client)
):
    """
    Get detailed information about a specific player by ID.
    """
    player = client.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found")
    
    return Player(**player)

@router.get("/{player_id}/stats", response_model=PlayerWithStats)
def get_player_stats(
    player_id: int,
    season: Optional[int] = Query(None, description="Season year (e.g., 2023 for 2023-2024)"),
    client: BallDontLieClient = Depends(get_client)
):
    """
    Get player statistics for a specific season.
    
    If no season is specified, the most recent available statistics will be returned.
    """
    # Get player details
    player = client.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with ID {player_id} not found")
    
    # Get player stats
    stats = client.get_player_stats(player_id, season)
    
    # Check if stats were found
    if not stats:
        player_model = Player(**player)
        return PlayerWithStats(**player_model.dict(), stats=None)
    
    # Get the first stat entry (could be improved to aggregate or get the most relevant)
    stat_data = stats[0]
    
    # Create the PlayerStat model
    player_stat = PlayerStat(
        pts=stat_data.get('pts', 0),
        reb=stat_data.get('reb', 0),
        ast=stat_data.get('ast', 0),
        stl=stat_data.get('stl', 0),
        blk=stat_data.get('blk', 0),
        fg_pct=stat_data.get('fg_pct', 0),
        fg3_pct=stat_data.get('fg3_pct', 0),
        ft_pct=stat_data.get('ft_pct', 0),
        turnover=stat_data.get('turnover', 0),
        min=stat_data.get('min', '0'),
        season=season
    )
    
    # Create the complete player with stats
    player_model = Player(**player)
    return PlayerWithStats(**player_model.dict(), stats=player_stat)