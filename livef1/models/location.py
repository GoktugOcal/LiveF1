from typing import Any, Dict, Optional
from timezonefinder import TimezoneFinder

from livef1.models.country import Country

tzfinder = TimezoneFinder()

class Location:
    """
    Geographic context for a circuit venue (city/region and country).

    Attributes
    ----------
    locality : str, optional
        City or region name (for example, \"Monza\").
    country : str, optional
        Country name (for example, for timezone helpers such as :func:`relocate_tz`).
    lat : float, optional
        Latitude in decimal degrees.
    long : float, optional
        Longitude in decimal degrees.
    """

    def __init__(
        self,
        locality: Optional[str] = None,
        country: Optional[str] = None,
        lat: Optional[float] = None,
        long: Optional[float] = None,
        **kwargs: Any,
    ):
        self.locality = locality
        self.country = country
        self.lat = lat
        self.long = long

        if self.lat is not None and self.long is not None:
            self.timezone = tzfinder.timezone_at(lat=self.lat, lng=self.long)

        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key.lower(), value)

        if getattr(self, "latitude", None) is not None and self.lat is None:
            self.lat = self.latitude
        if getattr(self, "lng", None) is not None and self.long is None:
            self.long = self.lng

        if hasattr(self, "country"):
            if isinstance(self.country, str): self.country = {"name": self.country}
            self.country = Country(**self.country)
        
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Location"]:
        if not data:
            return None
        normalized = {str(k).lower(): v for k, v in data.items() if v is not None}
        return cls(**normalized)

    def __repr__(self) -> str:
        locality = getattr(self, "locality", None)
        country = getattr(self, "country", None)
        if locality and country:
            return f"Location({locality!r}, {country!r})"
        if locality:
            return f"Location({locality!r})"
        if country:
            return f"Location(country={country!r})"
        return "Location()"
