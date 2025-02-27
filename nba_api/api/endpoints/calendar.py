from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from nba_api.client import BallDontLieClient
from nba_api.calendar_service import GoogleCalendarService
from nba_api.models.calendar import GameEvent, CalendarEventResponse, CalendarAuthStatusResponse
import os
from datetime import datetime

router = APIRouter(
    prefix="/calendar",
    tags=["calendar"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the calendar service
def get_calendar_service():
    """Get an instance of the Google Calendar service."""
    service = GoogleCalendarService()
    return service

# Dependency to get the BallDontLie client
def get_client():
    """Get an instance of the BallDontLie API client."""
    api_key = os.environ.get("BALLDONTLIE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return BallDontLieClient(api_key)

@router.get("/auth-status", response_model=CalendarAuthStatusResponse)
def get_auth_status(calendar_service: GoogleCalendarService = Depends(get_calendar_service)):
    """Check if the calendar service is authenticated."""
    is_authenticated = calendar_service.is_authenticated()
    
    return {
        "authenticated": is_authenticated,
        "message": "Authenticated and ready to use" if is_authenticated else "Not authenticated"
    }

@router.get("/upcoming-events", response_model=List[dict])
def get_upcoming_events(
    max_results: int = Query(10, description="Maximum number of events to return"),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """Get upcoming events from the user's Google Calendar."""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Calendar service not authenticated")
    
    events = calendar_service.list_upcoming_events(max_results)
    return events

@router.post("/add-game", response_model=CalendarEventResponse)
def add_game_to_calendar(
    game_event: GameEvent,
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """Add a game to Google Calendar."""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Calendar service not authenticated")
    
    # Convert Pydantic model to dictionary
    event_data = game_event.dict()
    
    # Add the event to calendar
    result = calendar_service.add_event(event_data)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create calendar event")
    
    return result

@router.post("/add-team-games", response_model=List[CalendarEventResponse])
def add_team_games_to_calendar(
    team_id: int = Query(..., description="Team ID"),
    max_games: int = Query(5, description="Maximum number of games to add"),
    client: BallDontLieClient = Depends(get_client),
    calendar_service: GoogleCalendarService = Depends(get_calendar_service)
):
    """Add upcoming games for a team to Google Calendar."""
    if not calendar_service.is_authenticated():
        raise HTTPException(status_code=401, detail="Calendar service not authenticated")
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get upcoming games for the team
    games = client.get_team_games(team_id, start_date=today)
    
    if not games:
        raise HTTPException(status_code=404, detail=f"No upcoming games found for team ID {team_id}")
    
    # Limit to max_games
    games = games[:max_games]
    
    # Add each game to calendar
    results = []
    for game in games:
        # Format game for calendar
        event_data = client.format_game_for_calendar(game)
        
        # Add to calendar
        result = calendar_service.add_event(event_data)
        
        if result:
            results.append(result)
    
    if not results:
        raise HTTPException(status_code=500, detail="Failed to add any games to calendar")
    
    return results