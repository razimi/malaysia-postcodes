"""
Data loader for Malaysia postcodes.
Loads JSON data and creates efficient lookup indexes.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from api.models import State, City, StateListItem


class PostcodeData:
    """Manages postcode data loading and querying."""
    
    def __init__(self, data_file: str = "all.json"):
        """Initialize and load postcode data.
        
        Args:
            data_file: Path to the JSON data file
        """
        self.data_file = data_file
        self.states: List[State] = []
        self.postcode_index: Dict[str, Tuple[str, str]] = {}  # postcode -> (state, city)
        self.state_dict: Dict[str, State] = {}  # state name (lowercase) -> State
        self.city_dict: Dict[str, List[Tuple[str, City]]] = {}  # city name (lowercase) -> [(state, City)]
        
        self._load_data()
        self._build_indexes()
    
    def _load_data(self):
        """Load data from JSON file."""
        data_path = Path(self.data_file)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse states and cities
        for state_data in data.get('state', []):
            cities = [City(**city_data) for city_data in state_data.get('city', [])]
            state = State(name=state_data['name'], city=cities)
            self.states.append(state)
    
    def _build_indexes(self):
        """Build lookup indexes for fast queries."""
        for state in self.states:
            # State index (case-insensitive)
            state_key = state.name.lower()
            self.state_dict[state_key] = state
            
            # City and postcode indexes
            for city in state.city:
                # City index (case-insensitive, cities can exist in multiple states)
                city_key = city.name.lower()
                if city_key not in self.city_dict:
                    self.city_dict[city_key] = []
                self.city_dict[city_key].append((state.name, city))
                
                # Postcode reverse lookup
                for postcode in city.postcode:
                    self.postcode_index[postcode] = (state.name, city.name)
    
    def get_all_states(self) -> List[StateListItem]:
        """Get list of all states with summary info."""
        result = []
        for state in self.states:
            city_count = len(state.city)
            postcode_count = sum(len(city.postcode) for city in state.city)
            result.append(StateListItem(
                name=state.name,
                city_count=city_count,
                postcode_count=postcode_count
            ))
        return result
    
    def get_state(self, state_name: str) -> Optional[State]:
        """Get state by name (case-insensitive).
        
        Args:
            state_name: Name of the state
            
        Returns:
            State object or None if not found
        """
        return self.state_dict.get(state_name.lower())
    
    def get_cities_in_state(self, state_name: str) -> Optional[List[City]]:
        """Get all cities in a state.
        
        Args:
            state_name: Name of the state
            
        Returns:
            List of cities or None if state not found
        """
        state = self.get_state(state_name)
        return state.city if state else None
    
    def get_city_in_state(self, state_name: str, city_name: str) -> Optional[City]:
        """Get a specific city in a state.
        
        Args:
            state_name: Name of the state
            city_name: Name of the city
            
        Returns:
            City object or None if not found
        """
        state = self.get_state(state_name)
        if not state:
            return None
        
        city_key = city_name.lower()
        for city in state.city:
            if city.name.lower() == city_key:
                return city
        return None
    
    def lookup_postcode(self, postcode: str) -> Optional[Tuple[str, str]]:
        """Lookup location by postcode.
        
        Args:
            postcode: Postcode to lookup
            
        Returns:
            Tuple of (state_name, city_name) or None if not found
        """
        return self.postcode_index.get(postcode)
    
    def search(self, query: str) -> List[Dict]:
        """Search for states or cities by name.
        
        Args:
            query: Search query (case-insensitive substring match)
            
        Returns:
            List of search results
        """
        query_lower = query.lower()
        results = []
        
        # Search in states
        for state in self.states:
            if query_lower in state.name.lower():
                postcode_count = sum(len(city.postcode) for city in state.city)
                results.append({
                    'type': 'state',
                    'name': state.name,
                    'state': None,
                    'postcode_count': postcode_count
                })
        
        # Search in cities
        seen_cities = set()
        for state in self.states:
            for city in state.city:
                if query_lower in city.name.lower():
                    # Avoid duplicate cities with same name
                    city_key = (city.name.lower(), state.name.lower())
                    if city_key not in seen_cities:
                        seen_cities.add(city_key)
                        results.append({
                            'type': 'city',
                            'name': city.name,
                            'state': state.name,
                            'postcode_count': len(city.postcode)
                        })
        
        return results
    
    def get_total_postcodes(self) -> int:
        """Get total number of unique postcodes."""
        return len(self.postcode_index)
    
    def get_total_states(self) -> int:
        """Get total number of states."""
        return len(self.states)


# Global instance (loaded once at startup)
_postcode_data: Optional[PostcodeData] = None


def get_postcode_data() -> PostcodeData:
    """Get the global PostcodeData instance.
    
    Returns:
        PostcodeData instance
        
    Raises:
        RuntimeError: If data hasn't been loaded yet
    """
    global _postcode_data
    if _postcode_data is None:
        raise RuntimeError("Postcode data not loaded. Call load_postcode_data() first.")
    return _postcode_data


def load_postcode_data(data_file: str = "all.json"):
    """Load postcode data into global instance.
    
    Args:
        data_file: Path to the JSON data file
    """
    global _postcode_data
    _postcode_data = PostcodeData(data_file)
