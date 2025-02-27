from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from nba_api.client import BallDontLieClient
from nba_api.models.stats import StatisticsComparison, StatisticsRequest
from nba_api.exceptions import (
    NBAApiException, ApiKeyError, PlayerNotFoundError,
    SeasonNotFoundError, ApiRateLimitError, InvalidParameterError
)
from nba_api.logger import get_logger
import os

# Get logger for this module
logger = get_logger(__name__)

router = APIRouter(
    prefix="/stats",
    tags=["statistics"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        429: {"description": "Too many requests"},
        500: {"description": "Internal server error"}
    },
)

def get_client():
    """Dependency to get a BallDontLie API client instance."""
    api_key = os.environ.get("BALLDONTLIE_API_KEY")
    if not api_key:
        logger.error("API key not configured in environment variables")
        raise HTTPException(status_code=500, detail="API key not configured")
    return BallDontLieClient(api_key)

@router.get("/player/{player_id}/seasons", response_model=List[int])
def get_player_seasons(
    player_id: int = Path(..., description="Player ID"),
    client: BallDontLieClient = Depends(get_client)
):
    """Retrieve all seasons a player has participated in.
    
    This endpoint returns a chronological list of season years for which
    the specified player has statistics. Each season is represented by 
    the year in which it began (e.g., 2023 for the 2023-2024 season).
    
    Args:
        player_id: The player's unique identifier in the BallDontLie API.
        
    Returns:
        A list of integers representing season years.
        
    Raises:
        HTTPException: With appropriate status codes for different error scenarios.
    """
    logger.info(f"API request: Get seasons for player {player_id}")
    
    try:
        seasons = client.get_player_seasons(player_id)
        
        if not seasons:
            logger.warning(f"No seasons found for player {player_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No seasons found for player ID {player_id}"
            )
        
        return seasons
        
    except PlayerNotFoundError as e:
        logger.error(f"Player not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ApiKeyError as e:
        logger.error(f"API key error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except ApiRateLimitError as e:
        logger.error(f"API rate limit error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )

@router.get("/player/{player_id}/compare", response_model=StatisticsComparison)
def compare_seasons_get(
    player_id: int = Path(..., description="Player ID"),
    seasons: List[int] = Query(..., description="Seasons to compare"),
    client: BallDontLieClient = Depends(get_client)
):
    """Compare player statistics across multiple seasons using GET.
    
    This endpoint compares a player's performance across the specified seasons
    and calculates growth/decline between consecutive seasons.
    
    Args:
        player_id: The player's unique identifier.
        seasons: List of season years to compare.
        
    Returns:
        A StatisticsComparison object with detailed comparison data.
        
    Raises:
        HTTPException: With appropriate status codes for different error scenarios.
    """
    logger.info(f"API request: Compare seasons {seasons} for player {player_id}")
    
    try:
        if len(seasons) < 1:
            logger.error("No seasons specified")
            raise HTTPException(
                status_code=400,
                detail="At least one season must be specified"
            )
        
        result = client.compare_player_seasons(player_id, seasons)
        return result
        
    except PlayerNotFoundError as e:
        logger.error(f"Player not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except SeasonNotFoundError as e:
        logger.error(f"Season not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ApiKeyError as e:
        logger.error(f"API key error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except ApiRateLimitError as e:
        logger.error(f"API rate limit error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )

@router.post("/player/{player_id}/compare", response_model=StatisticsComparison)
def compare_seasons_post(
    player_id: int = Path(..., description="Player ID"),
    request: StatisticsRequest = ...,
    client: BallDontLieClient = Depends(get_client)
):
    """Compare player statistics across multiple seasons using POST.
    
    This endpoint is similar to the GET version but accepts the seasons in the request body.
    
    Args:
        player_id: The player's unique identifier.
        request: A StatisticsRequest object containing the seasons to compare.
        
    Returns:
        A StatisticsComparison object with detailed comparison data.
        
    Raises:
        HTTPException: With appropriate status codes for different error scenarios.
    """
    logger.info(f"API request: Compare seasons {request.seasons} for player {player_id}")
    
    try:
        if len(request.seasons) < 1:
            logger.error("No seasons specified")
            raise HTTPException(
                status_code=400,
                detail="At least one season must be specified"
            )
        
        result = client.compare_player_seasons(player_id, request.seasons)
        return result
        
    except PlayerNotFoundError as e:
        logger.error(f"Player not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except SeasonNotFoundError as e:
        logger.error(f"Season not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidParameterError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ApiKeyError as e:
        logger.error(f"API key error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except ApiRateLimitError as e:
        logger.error(f"API rate limit error: {str(e)}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )