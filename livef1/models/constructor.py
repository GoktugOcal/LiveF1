class Constructor:
    """
    Represents a Formula 1 constructor / team.

    Attributes
    ----------
    id : str
        Jolpica / Ergast ``constructorId`` (e.g. ``red_bull``).
    Name : str
        Display name (e.g. ``Red Bull``).
    Nationality : str
        Constructor nationality label.
    wiki : str
        Wikipedia or reference URL when provided by Jolpica.
    """

    def __init__(
        self,
        id: str = None,
        Name: str = None,
        Nationality: str = None,
        wiki: str = None,
        **kwargs
    ):
        self.id = id
        self.Name = Name
        self.Nationality = Nationality
        self.wiki = wiki
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        name = self.Name or self.id or "?"
        return f"{name} ({self.id})"


def _jolpica_constructor_dict(constructor: dict) -> dict:
    """Maps a Jolpica-style constructor dict onto :class:`Constructor` kwargs."""
    return {
        "id": constructor.get("constructorId", None),
        "Name": constructor.get("name", None),
        "Nationality": constructor.get("nationality", None),
        "wiki": constructor.get("url", None),
    }
