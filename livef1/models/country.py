from typing import Any, Dict, Optional
import pycountry


class Country:
    """
    Country metadata for a meeting or circuit (F1 live-timing style payload).

    Attributes
    ----------
    key : str, optional
        API country key.
    code : str, optional
        Country code (often ISO alpha-2).
    name : str, optional
        Display name of the country.
    """

    def __init__(
        self,
        key: Optional[str] = None,
        code: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ):
        self.key = key
        self.code = code
        self.name = name

        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k.lower(), v)
        
        if not self.code:
            self.code = pycountry.countries.search_fuzzy(self.name)[0].alpha_3
    
    def get(self, key, default=None):
        return getattr(self, key, default)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Country"]:
        if not data:
            return None
        normalized = {str(k).lower(): v for k, v in data.items() if v is not None}
        return cls(**normalized)

    def __repr__(self) -> str:
        name = getattr(self, "name", None)
        code = getattr(self, "code", None)
        if name and code:
            return f"Country({name!r}, {code!r})"
        if name:
            return f"Country({name!r})"
        if code:
            return f"Country(code={code!r})"
        return "Country()"
