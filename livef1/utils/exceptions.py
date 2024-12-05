class livef1Exception(Exception):
    pass


class LiveF1Error(Exception):
    """Base class for all LiveF1 module exceptions."""
    pass

class ArgumentError(LiveF1Error):
    """Exception for arguments of methods related errors"""
    pass