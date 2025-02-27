# nba_api/exceptions.py

class NBAApiException(Exception):
    """Base exception for all NBA API related errors."""
    pass

class ApiKeyError(NBAApiException):
    """Raised when there's an issue with the API key."""
    pass

class PlayerNotFoundError(NBAApiException):
    """Raised when a requested player cannot be found."""
    pass

class SeasonNotFoundError(NBAApiException):
    """Raised when statistics for a requested season cannot be found."""
    pass

class ApiRateLimitError(NBAApiException):
    """Raised when the API rate limit has been exceeded."""
    pass

class InvalidParameterError(NBAApiException):
    """Raised when an invalid parameter is provided."""
    pass

class CacheError(NBAApiException):
    """Raised when there's an issue with the cache system."""
    pass