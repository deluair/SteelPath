"""
Miscellaneous helper functions for the SteelPath simulation.
"""
import uuid
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def generate_unique_id(prefix: str = "id") -> str:
    """
    Generates a unique ID string with an optional prefix.

    Args:
        prefix (str): A prefix for the generated ID.

    Returns:
        str: A unique ID string.
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def deep_update(source: Dict, overrides: Dict) -> Dict:
    """
    Recursively updates a dictionary with values from another dictionary.
    Unlike dict.update(), this function merges nested dictionaries.

    Args:
        source (Dict): The dictionary to be updated.
        overrides (Dict): The dictionary providing new values.

    Returns:
        Dict: The updated source dictionary.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            source[key] = deep_update(source[key], value)
        else:
            source[key] = value
    return source

# Example usage:
if __name__ == '__main__':
    uid1 = generate_unique_id("plant")
    uid2 = generate_unique_id()
    print(f"Generated UID 1: {uid1}")
    print(f"Generated UID 2: {uid2}")

    dict1 = {'a': 1, 'b': {'c': 2, 'd': 3}}
    dict2 = {'b': {'c': 4, 'e': 5}, 'f': 6}
    updated_dict = deep_update(dict1.copy(), dict2)
    print(f"Original dict1: {dict1}")
    print(f"Overrides dict2: {dict2}")
    print(f"Updated dict: {updated_dict}")

    dict3 = {'x': [1,2], 'y': {'z': 10}}
    dict4 = {'y': {'z': 20, 'w': 30}}
    updated_dict2 = deep_update(dict3.copy(), dict4)
    print(f"Updated dict2: {updated_dict2}")
