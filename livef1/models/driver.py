class Driver:
    """
    Represents a Formula 1 driver with their associated information.

    Attributes
    ----------
    RacingNumber : str
        Driver's racing number (e.g., "1")
    BroadcastName : str
        Name used in broadcasts (e.g., "M VERSTAPPEN")
    FullName : str
        Driver's complete name (e.g., "Max VERSTAPPEN")
    Tla : str
        Three letter abbreviation (e.g., "VER")
    Line : int
        Driver's line number in timing screens
    TeamName : str
        Current team name (e.g., "Red Bull Racing")
    TeamColour : str
        Team's primary color hex code without # (e.g., "3671C6")
    FirstName : str
        Driver's first name (e.g., "Max")
    LastName : str
        Driver's last name (e.g., "Verstappen")
    Reference : str
        Driver's unique reference code (e.g., "MAXVER01")
    HeadshotUrl : str
        URL to driver's headshot image
    session : Session
        Reference to the parent session object
    """

    def __init__(
        self,
        RacingNumber: str = None,
        BroadcastName: str = None,
        FullName: str = None,
        Tla: str = None,
        Line: int = None,
        TeamName: str = None,
        TeamColour: str = None,
        FirstName: str = None,
        LastName: str = None,
        Reference: str = None,
        HeadshotUrl: str = None,
        session: "Session" = None,
        **kwargs
    ):
        self.RacingNumber = RacingNumber
        self.BroadcastName = BroadcastName
        self.FullName = FullName
        self.Tla = Tla
        self.Line = Line
        self.TeamName = TeamName
        self.TeamColour = TeamColour
        self.FirstName = FirstName
        self.LastName = LastName
        self.Reference = Reference
        self.HeadshotUrl = HeadshotUrl
        self.session = session

        # Set any additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)  # Removed .lower() to preserve exact key names

    def get_telemetry(self):
        """
        Get telemetry data for this driver from the session.

        Returns
        -------
        DataFrame
            Telemetry data filtered for this driver
        """
        if self.session and self.session.carTelemetry is not None:
            return self.session.carTelemetry[
                self.session.carTelemetry["DriverNo"] == self.RacingNumber
            ]
        return None

    def get_laps(self):
        """
        Get lap data for this driver from the session.

        Returns
        -------
        DataFrame
            Lap data filtered for this driver
        """
        if self.session and self.session.laps is not None:
            return self.session.laps[
                self.session.laps["DriverNo"] == self.RacingNumber
            ]
        return None

    def __repr__(self):
        return f"Driver({self.Tla} - {self.TeamName})"