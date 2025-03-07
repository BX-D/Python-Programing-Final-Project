import os
import json
import requests
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from requests.exceptions import RequestException

# Import custom exceptions and logger
from nba_api.exceptions import (
    NBAApiException, ApiKeyError, PlayerNotFoundError,
    SeasonNotFoundError, ApiRateLimitError, InvalidParameterError, CacheError
)
from nba_api.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

class BallDontLieClient:
    """Client for interacting with the BallDontLie NBA API.
    
    This client provides methods to access player information, statistics,
    game schedules, and other NBA data through the BallDontLie API. It includes
    built-in caching to minimize API calls and improve performance.
    
    Attributes:
        base_url (str): The base URL for the BallDontLie API.
        headers (dict): HTTP headers including the API key for authentication.
        cache_dir (str): Directory where API responses are cached.
    """
    
    def __init__(self, api_key: str, cache_dir: str = "data"):
        """Initialize the BallDontLie API client.
        
        Args:
            api_key: Your BallDontLie API key from the All-Star or GOAT plan.
            cache_dir: Directory to store cached API responses as JSON files.
                Default is "data".
                
        Raises:
            CacheError: If the cache directory cannot be created.
        """
        self.base_url = "https://api.balldontlie.io/v1"
        self.headers = {"Authorization": api_key}
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        try:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Cache directory: {os.path.abspath(cache_dir)}")
        except OSError as e:
            logger.error(f"Failed to create cache directory: {str(e)}")
            raise CacheError(f"Failed to create cache directory: {str(e)}") from e
    
    def _get_cache_path(self, endpoint: str, params: Dict = None) -> str:
        """Generate a cache file path based on the endpoint and parameters.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Path to the cache file
        """
        # Create a unique cache filename based on the request
        if params:
            # Convert params to a sorted string representation for consistency
            param_str = '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))
            filename = f"{endpoint.replace('/', '_')}_{param_str}.json"
        else:
            filename = f"{endpoint.replace('/', '_')}.json"
        
        return os.path.join(self.cache_dir, filename)
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the API with caching.
        
        Args:
            endpoint: API endpoint (e.g., 'players', 'teams')
            params: Query parameters
            
        Returns:
            API response as a dictionary
            
        Raises:
            ApiKeyError: If the API key is invalid or missing.
            ApiRateLimitError: If the API rate limit has been reached.
            RequestException: If the API request fails for other reasons.
            CacheError: If there's an issue with the cache.
        """
        # Build the full URL
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Request: {url}, Params: {params}")
        
        # Get cache file path
        try:
            cache_path = self._get_cache_path(endpoint, params)
            
            # Check if response is already cached
            if os.path.exists(cache_path):
                logger.debug(f"Using cached response from {cache_path}")
                try:
                    with open(cache_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read cache file {cache_path}: {str(e)}")
                    # If cache is corrupted, continue with the API request
            
            # Make the API request
            logger.info(f"Making API request to {url}")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Check for API errors
            if response.status_code == 401:
                logger.error(f"API key error: {response.text}")
                raise ApiKeyError("Invalid or missing API key")
            elif response.status_code == 429:
                logger.error("API rate limit exceeded")
                raise ApiRateLimitError("Rate limit exceeded. Please try again later.")
            elif response.status_code != 200:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                raise RequestException(f"API request failed with status {response.status_code}: {response.text}")
            
            # Parse the response
            data = response.json()
            
            # Cache the response
            try:
                with open(cache_path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Cached response to {cache_path}")
            except (IOError, OSError) as e:
                logger.warning(f"Failed to cache response to {cache_path}: {str(e)}")
                # Continue even if caching fails
            
            return data
            
        except (json.JSONDecodeError, RequestException) as e:
            # Re-raise request exceptions
            logger.error(f"Request error: {str(e)}")
            raise
        except Exception as e:
            # Catch any other exceptions and provide context
            logger.exception(f"Unexpected error in API request: {str(e)}")
            raise NBAApiException(f"Unexpected error in API request: {str(e)}") from e

    def search_players(self, name: str) -> List[Dict]:
        """Search for players by name.
        
        This method intelligently searches for players by their name, supporting
        both full names and partial names.
        
        Args:
            name: Player name to search for (e.g., "LeBron James" or "LeBron")
                
        Returns:
            List of matching player data
            
        Raises:
            ApiKeyError: If the API key is invalid or missing.
            ApiRateLimitError: If the API rate limit has been reached.
            RequestException: If the API request fails for other reasons.
            CacheError: If there's an issue with the cache.
        """
        logger.info(f"Searching for player: {name}")
        
        try:
            # Split the name to check if it's a full name
            name_parts = name.strip().split()
            
            if len(name_parts) > 1:
                # If we have multiple parts, try both approaches
                
                # Approach 1: Use the general search parameter
                params = {"search": name}
                response1 = self._request("players", params)
                results1 = response1.get("data", [])
                
                # Approach 2: Use specific first_name and last_name parameters
                # Assuming first part is first name and last part is last name
                params = {
                    "first_name": name_parts[0],
                    "last_name": name_parts[-1]
                }
                response2 = self._request("players", params)
                results2 = response2.get("data", [])
                
                # Combine results, removing duplicates based on player ID
                all_results = results1 + results2
                unique_results = []
                seen_ids = set()
                
                for player in all_results:
                    player_id = player.get("id")
                    if player_id not in seen_ids:
                        seen_ids.add(player_id)
                        unique_results.append(player)
                
                logger.info(f"Found {len(unique_results)} unique players matching '{name}'")
                return unique_results
            else:
                # If only one name part, use the standard search
                params = {"search": name}
                response = self._request("players", params)
                results = response.get("data", [])
                
                logger.info(f"Found {len(results)} players matching '{name}'")
                return results
                
        except Exception as e:
            logger.error(f"Error searching for player '{name}': {str(e)}")
            raise

    def get_player(self, player_id: int) -> Dict:
        """Get detailed information about a specific player.
        
        Args:
            player_id: The player's ID in the BallDontLie API
                
        Returns:
            Player data dictionary
            
        Raises:
            PlayerNotFoundError: If the player is not found
            ApiKeyError: If the API key is invalid or missing
            ApiRateLimitError: If the API rate limit has been reached
            RequestException: If the API request fails for other reasons
        """
        logger.info(f"Getting player details for ID: {player_id}")
        
        try:
            # Validate player_id
            if not isinstance(player_id, int) or player_id <= 0:
                raise InvalidParameterError(f"Invalid player ID: {player_id}. Must be a positive integer.")
            
            response = self._request(f"players/{player_id}")
            player_data = response.get("data", {})
            
            if not player_data:
                logger.error(f"Player not found with ID: {player_id}")
                raise PlayerNotFoundError(f"Player not found with ID: {player_id}")
            
            logger.info(f"Found player: {player_data.get('first_name')} {player_data.get('last_name')}")
            return player_data
            
        except (PlayerNotFoundError, ApiKeyError, ApiRateLimitError, RequestException):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting player {player_id}: {str(e)}")
            raise NBAApiException(f"Unexpected error getting player {player_id}: {str(e)}") from e

    def get_player_stats(self, player_id: int, season: Optional[int] = None) -> List[Dict]:
        """Get statistics for a player.
        
        Args:
            player_id: The player's ID in the BallDontLie API
            season: Season year (e.g., 2023 for 2023-2024 season)
                
        Returns:
            List of player statistics
            
        Raises:
            PlayerNotFoundError: If the player is not found
            InvalidParameterError: If player_id or season is invalid
            ApiKeyError: If the API key is invalid or missing
            ApiRateLimitError: If the API rate limit has been reached
            RequestException: If the API request fails for other reasons
        """
        logger.info(f"Getting stats for player ID: {player_id}, Season: {season}")
        
        try:
            # Validate player_id
            if not isinstance(player_id, int) or player_id <= 0:
                raise InvalidParameterError(f"Invalid player ID: {player_id}. Must be a positive integer.")
            
            # Validate season if provided
            if season is not None:
                current_year = datetime.now().year
                if not isinstance(season, int) or season < 1946 or season > current_year:
                    raise InvalidParameterError(
                        f"Invalid season: {season}. Must be between 1946 and {current_year}."
                    )
            
            params = {"player_ids[]": player_id}
            if season:
                params["seasons[]"] = season
                
            response = self._request("stats", params)
            stats = response.get("data", [])
            
            logger.info(f"Found {len(stats)} stat entries for player {player_id}")
            return stats
            
        except (PlayerNotFoundError, InvalidParameterError, ApiKeyError, ApiRateLimitError, RequestException):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting stats for player {player_id}: {str(e)}")
            raise NBAApiException(f"Unexpected error getting stats for player {player_id}: {str(e)}") from e

    def get_player_seasons(self, player_id: int) -> List[int]:
        """Get all seasons a player has played."""
        try:
            # Get all stats for this player (without season filtering)
            params = {"player_ids[]": player_id}
            response = self._request("stats", params)
            
            # Extract unique seasons from the stats data
            seasons = set()
            for stat in response.get("data", []):
                if "game" in stat and "season" in stat["game"]:
                    seasons.add(stat["game"]["season"])
            
            seasons_list = sorted(list(seasons))
            return seasons_list
        except Exception as e:
            # Handle exceptions
            logger.error(f"Error getting seasons for player {player_id}: {str(e)}")
            raise

    def compare_player_seasons(self, player_id: int, seasons: List[int]) -> Dict:
        """Compare a player's statistics across multiple seasons.
        
        This method retrieves and analyzes a player's performance across the
        specified seasons. It calculates average statistics for each season and
        determines the percentage growth or decline in key metrics between
        consecutive seasons.
        
        Args:
            player_id: The BallDontLie player ID.
            seasons: A list of season years to compare. Each season is represented 
                by the year in which the season started (e.g., 2023 for the 
                2023-2024 season).
                
        Returns:
            A dictionary containing:
                - player: Basic information about the player
                - seasons: The list of seasons compared
                - season_averages: Statistics for each season
                - growth: Percentage changes between consecutive seasons
                - metrics: The statistical categories included in the comparison
                
        Raises:
            PlayerNotFoundError: If the player is not found
            InvalidParameterError: If player_id or seasons are invalid
            ApiKeyError: If the API key is invalid or missing
            ApiRateLimitError: If the API rate limit has been reached
            RequestException: If the API request fails for other reasons
        """
        logger.info(f"Comparing seasons {seasons} for player ID: {player_id}")
        
        try:
            # Validate player_id
            if not isinstance(player_id, int) or player_id <= 0:
                raise InvalidParameterError(f"Invalid player ID: {player_id}. Must be a positive integer.")
            
            # Validate seasons
            if not seasons or not isinstance(seasons, list):
                raise InvalidParameterError("Seasons must be a non-empty list of integers")
            
            current_year = datetime.now().year
            for season in seasons:
                if not isinstance(season, int) or season < 1946 or season > current_year:
                    raise InvalidParameterError(
                        f"Invalid season: {season}. Must be between 1946 and {current_year}."
                    )
            
            # Get player information
            player = self.get_player(player_id)
            
            # Calculate season averages for each season
            season_averages_raw = {}
            for season in seasons:
                stats = self.get_player_stats(player_id, season)
                
                # Skip if no stats found for this season
                if not stats:
                    logger.warning(f"No stats found for player {player_id} in season {season}")
                    season_averages_raw[season] = None
                    continue
                
                # Calculate averages
                total_games = len(stats)
                if total_games == 0:
                    season_averages_raw[season] = None
                    continue
                
                totals = {
                    "pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0,
                    "turnover": 0, "fg_pct": 0, "fg3_pct": 0, "ft_pct": 0,
                    "min": 0, "games_played": total_games
                }
                
                valid_games = 0
                for game in stats:
                    valid_game = True
                    for key in totals.keys():
                        if key == "games_played":
                            continue
                        
                        if key == "min":
                            # Handle minutes played (format like "34:56")
                            min_str = game.get(key, "0:0")
                            try:
                                if ":" in min_str:
                                    minutes, seconds = min_str.split(":")
                                    totals[key] += int(minutes) + (int(seconds) / 60)
                                else:
                                    # Handle cases where minutes might be a straight number
                                    totals[key] += float(min_str)
                            except (ValueError, TypeError):
                                valid_game = False
                                break
                        else:
                            # Handle regular numerical stats
                            try:
                                value = game.get(key, 0)
                                if value is not None:
                                    totals[key] += float(value)
                            except (ValueError, TypeError):
                                valid_game = False
                                break
                    
                    if valid_game:
                        valid_games += 1
                
                # Calculate averages
                if valid_games > 0:
                    averages = {k: v / valid_games for k, v in totals.items() if k != "games_played"}
                    averages["games_played"] = total_games
                    season_averages_raw[season] = averages
                else:
                    season_averages_raw[season] = None
            
            # Convert integer season keys to strings for JSON compatibility
            season_averages = {str(season): stats for season, stats in season_averages_raw.items()}
            
            # Calculate growth between consecutive seasons
            growth = {}
            key_metrics = ["pts", "reb", "ast", "stl", "blk", "fg_pct", "fg3_pct", "ft_pct"]
            
            for i in range(1, len(seasons)):
                prev_season = seasons[i-1]
                curr_season = seasons[i]
                
                prev_stats = season_averages_raw.get(prev_season)
                curr_stats = season_averages_raw.get(curr_season)
                
                # Skip if either season has no stats
                if not prev_stats or not curr_stats:
                    continue
                
                # Calculate percentage changes
                season_growth = {}
                for metric in key_metrics:
                    prev_value = prev_stats.get(metric, 0)
                    curr_value = curr_stats.get(metric, 0)
                    
                    # Avoid division by zero
                    if prev_value and prev_value != 0:
                        pct_change = ((curr_value - prev_value) / abs(prev_value)) * 100
                        season_growth[metric] = round(pct_change, 1)
                    else:
                        season_growth[metric] = None
                
                # Store growth data for this season pair
                growth[f"{prev_season}-{curr_season}"] = season_growth
            
            # Prepare the final result
            result = {
                "player": {
                    "id": player.get("id"),
                    "name": f"{player.get('first_name')} {player.get('last_name')}",
                    "team": player.get("team", {}).get("full_name")
                },
                "seasons": seasons,
                "season_averages": season_averages,
                "growth": growth,
                "metrics": key_metrics
            }
            
            logger.info(f"Successfully compared {len(seasons)} seasons for player {player_id}")
            return result
            
        except (PlayerNotFoundError, InvalidParameterError, ApiKeyError, ApiRateLimitError, RequestException):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.exception(f"Unexpected error comparing seasons for player {player_id}: {str(e)}")
            raise NBAApiException(f"Unexpected error comparing seasons for player {player_id}: {str(e)}") from e
        

    def format_game_for_calendar(self, game: Dict) -> Dict:
        """Format a game for calendar display.
        
        Args:
            game: Game data from API
            
        Returns:
            Dict with formatted game information for calendar
        """
        # Extract teams
        home_team = game.get('home_team', {})
        visitor_team = game.get('visitor_team', {})
        
        # Format game date and time
        # Note: The API provides the date without specific time information
        # We'll use an estimated game time (7:30 PM local time) for demonstration
        game_date = game.get('date', '')
        game_datetime = f"{game_date}T19:30:00"
        
        # Format game information
        home_team_name = home_team.get('full_name', 'Unknown')
        visitor_team_name = visitor_team.get('full_name', 'Unknown')
        
        # Create a formatted event
        return {
            'summary': f"{visitor_team_name} @ {home_team_name}",
            'location': f"{home_team.get('city', '')}, {home_team.get('name', 'Arena')}",
            'description': f"NBA game: {visitor_team_name} at {home_team_name}",
            'start_datetime': game_datetime,
            'end_datetime': f"{game_date}T22:00:00",  # Assuming ~2.5 hour games
            'game_id': game.get('id'),
            'home_team': home_team_name,
            'visitor_team': visitor_team_name
        }
        
    
    def get_team_games(self, team_id: int, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None, season: Optional[int] = None) -> List[Dict]:
        """Get games for a specific team with flexible filtering.
        
        Args:
            team_id: The team's ID
            start_date: Start date in YYYY-MM-DD format (inclusive)
            end_date: End date in YYYY-MM-DD format (inclusive)
            season: Season year (e.g., 2023 for 2023-2024 season)
            
        Returns:
            List of games matching the criteria
        """
        params = {"team_ids[]": team_id}
        
        if start_date:
            params["start_date"] = start_date
        
        if end_date:
            params["end_date"] = end_date
            
        if season:
            params["seasons[]"] = season
        
        response = self._request("games", params)
        return response.get("data", [])