from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class GameEvent(BaseModel):
    """Model for game events to be added to calendar."""
    summary: str = Field(..., description="Event title")
    location: Optional[str] = Field(None, description="Event location")
    description: Optional[str] = Field(None, description="Event description")
    start_datetime: str = Field(..., description="Start time in ISO format")
    end_datetime: str = Field(..., description="End time in ISO format")
    game_id: int = Field(..., description="Game ID from BallDontLie API")
    home_team: str = Field(..., description="Home team name")
    visitor_team: str = Field(..., description="Visiting team name")

class CalendarEventResponse(BaseModel):
    """Response model for created calendar events."""
    id: Optional[str] = Field(None, description="Google Calendar event ID")
    htmlLink: Optional[str] = Field(None, description="Link to the event in Google Calendar")
    status: str = Field(..., description="Status of the operation")
    
class CalendarAuthStatusResponse(BaseModel):
    """Response model for calendar authentication status."""
    authenticated: bool = Field(..., description="Whether the calendar service is authenticated")
    message: str = Field(..., description="Status message")