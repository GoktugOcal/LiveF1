from typing import Dict, Optional
import requests

from livef1.utils.constants import START_COORDINATES_URL

class Circuit:
    """
    Represents a Formula 1 circuit with its characteristics and metadata.

    Attributes
    ----------
    key : str
        The unique identifier for the circuit.
    short_name : str
        Short name/abbreviation of the circuit.
    name : str, optional
        Full name of the circuit.
    length : float, optional
        Length of the circuit in kilometers.
    laps : int, optional
        Standard number of race laps.
    country : Dict, optional
        Dictionary containing country information.
    location : str, optional
        Geographic location of the circuit.
    coordinates : Dict[str, float], optional
        Latitude and longitude of the circuit.
    """

    def __init__(
        self,
        key: str,
        short_name: str
    ):
        self.key = key
        self.short_name = short_name
    
    def _load_start_coordinates(self):
        """
        Load the start coordinates of the circuit from an external API.
        """
        response = requests.get(START_COORDINATES_URL)
        
        if response.status_code == 200:
            data = response.json()
            try:
                self.start_coordinates = data[self.short_name]["start_coordinates"]
                self.start_direction = data[self.short_name]["start_direction"]
            except:
                pass
        else:
            raise Exception(f"Failed to load start coordinates: {response.status_code}")