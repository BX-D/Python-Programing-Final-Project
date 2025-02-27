import json
from typing import Dict, List, Any

def save_to_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file.
    
    Args:
        data: The data to save
        filepath: Path to the output file
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Data saved to {filepath}")

def load_from_json(filepath: str) -> Any:
    """Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        The loaded data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    with open(filepath, 'r') as f:
        return json.load(f)

def print_player_info(player: Dict) -> None:
    """Print formatted player information.
    
    Args:
        player: Player data dictionary
    """
    print(f"\n--- Player Information ---")
    print(f"Name: {player.get('first_name', '')} {player.get('last_name', '')}")
    print(f"Position: {player.get('position', 'Unknown')}")
    print(f"Height: {player.get('height', 'Unknown')}")
    print(f"Team: {player.get('team', {}).get('full_name', 'Unknown')}")
    print(f"---------------------\n")

def print_player_stats(stats: Dict) -> None:
    """Print formatted player statistics.
    
    Args:
        stats: Player statistics dictionary
    """
    print(f"\n--- Player Statistics ---")
    print(f"Points: {stats.get('pts', 0)}")
    print(f"Rebounds: {stats.get('reb', 0)}")
    print(f"Assists: {stats.get('ast', 0)}")
    print(f"Steals: {stats.get('stl', 0)}")
    print(f"Blocks: {stats.get('blk', 0)}")
    print(f"---------------------\n")