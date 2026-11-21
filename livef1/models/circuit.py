from typing import Dict, Optional
import requests
import pandas as pd

from livef1.utils.constants import START_COORDINATES_URL
from livef1.utils.exceptions import livef1Exception
from livef1.utils.helper import string_match_ratio
from livef1.models.location import Location


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
        key: str = None,
        short_name: str = None,
        **kwargs
    ):
        self.key = key
        self.short_name = short_name or kwargs.get("circuitId", None)
        # Iterate over the kwargs and set them as attributes of the instance
        for key, value in kwargs.items():
            if value:
                setattr(self, key.lower(), value)
        if hasattr(self, "shortname"):
            self.short_name = self.shortname
        if hasattr(self, "location"):
            self.location = Location(**self.location)

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

    @property
    def is_circuit_data_loaded(self):
        """True once the circuit layout (corners, track regions) has been fetched."""
        return self.__dict__.get("_raw_circuit_data") is not None

    def load_circuit_data(self, force=False):
        """
        Fetch the circuit layout (corners and track regions) from the circuit API.

        Does nothing if it is already loaded, unless ``force`` is True. :attr:`corners`
        and :attr:`track_regions` call this on first access.
        """
        if force or not self.is_circuit_data_loaded:
            self._load_circuit_data()
        return self

    @property
    def raw_circuit_data(self):
        """The circuit API response (loaded on first access)."""
        self.load_circuit_data()
        return self._raw_circuit_data

    @property
    def corners(self):
        """
        Corners of the circuit, loaded on first access.

        Returns
        -------
        pandas.DataFrame
            ``Number``, ``Letter``, ``Name`` (``"T1"``), ``Distance`` (metres from the
            start line), ``X``, ``Y`` (map coordinates) and ``Angle`` (degrees, for
            label placement), ordered by distance.
        """
        from livef1.analysis.track import corners_table
        return corners_table(self.raw_circuit_data.get("corners"))

    @property
    def track_regions(self):
        """
        Corner and straight regions of the circuit (``type``, ``name``, ``corner_start``,
        ``corner_end`` in metres ...), loaded on first access.
        """
        if self.__dict__.get("_track_regions") is None:
            self.load_circuit_data()
        return self._track_regions

    @track_regions.setter
    def track_regions(self, value):
        self._track_regions = value

    def _load_circuit_data(self):
        HEADERS = {'User-Agent': 'LiveF1/user'}
        response = requests.get("https://api.multiviewer.app/api/v1/circuits", headers=HEADERS)
        circuits = response.json()

        circuit_ref = next(
            (
                v for v in circuits.values()
                if
                    (v.get('name').lower() == self.short_name.lower())
                    | (string_match_ratio(v.get('name').lower(), self.short_name.lower()) > 0.8)
                ),
            None
        )
        if circuit_ref == None:
            raise livef1Exception(f"Circut {self.short_name} couldn't be found in circuit api.")

        circuit_key = circuit_ref["circuitKey"]
        circuit_ref_years = circuit_ref["years"]

        response = requests.get(f"https://api.multiviewer.app/api/v1/circuits/{circuit_key}/{circuit_ref_years[0]}/", headers=HEADERS)
        raw_circuit_data = response.json()

        for corner in raw_circuit_data["corners"]:
            corner.update(corner["trackPosition"])
        df_corners = pd.DataFrame(raw_circuit_data["corners"]).rename(
                columns = {
                    "length": "Distance",
                    "x": "X",
                    "y": "Y"
                }
            )
        df_corners.Distance = df_corners.Distance / 10
        df_corners["corner_start"] = df_corners.Distance - 50
        df_corners["corner_end"] = df_corners.Distance + 50

        df_corners["corner_end"] = (df_corners["corner_end"] > df_corners["corner_start"].shift(-1).fillna(1000000)) * df_corners["corner_start"].shift(-1).fillna(0) + (df_corners["corner_end"] < df_corners["corner_start"].shift(-1).fillna(1000000)) * df_corners["corner_end"]

        df_corners["name"] = "T" + df_corners["number"].astype(int).astype(str)
        df_corners["type"] = "Corner"
        df_corners = df_corners[["type","name","number","X","Y","corner_start","corner_end","angle","Distance"]]


        df_straights = pd.DataFrame(
            {
                "corner_start" : df_corners.corner_end.shift(1).fillna(df_corners.corner_end.max()),
                "corner_end" : df_corners.corner_start,
                "number" : df_corners.number.shift(1).fillna(0).astype(int),
            }
        )
        df_straights["type"] = "Straight"
        df_straights["name"] = "S" + df_straights["number"].astype(str)

        # Set both only once the layout is fully parsed, so a failed load can be retried
        self.track_regions = pd.concat([df_corners, df_straights])
        self._raw_circuit_data = raw_circuit_data
    
    def get(self, key, default=None):
        return getattr(self, key, default)