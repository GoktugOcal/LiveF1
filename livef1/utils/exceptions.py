from .logger import logger

class livef1Exception(Exception):
    pass

class LiveF1Error(Exception):
    """Base class for all LiveF1 module exceptions."""
    def __init__(self, message):
        """
        Initializes the exception and logs the message.
        
        Parameters
        ----------
        message : str
            The error message for the exception.
        """
        super().__init__(message)
        logger.error(str(self.__class__.__name__) + " - " + message)
    pass

class RealF1Error(LiveF1Error):
    """Exception for RealF1Client related errors"""
    pass

class ArgumentError(LiveF1Error):
    """Exception for arguments of methods related errors"""
    pass

class MissingFunctionError(LiveF1Error):
    """Raised when ETL functions does not include a function"""
    pass





class AdapterError(LiveF1Error):
    """Base exception for adapter-related issues."""
    pass

class InvalidResponseError(AdapterError):
    """Exception for invalid API responses."""
    pass

class InvalidEndpointError(AdapterError):
    """Raised when an invalid endpoint is accessed."""
    pass

# class AuthenticationError(AdapterError):
#     """Raised when authentication fails."""
#     pass

# class TimeoutError(AdapterError):
#     """Raised when a request times out."""
#     pass

# class ConnectionError(AdapterError):
#     """Raised when there is a connection issue."""
#     pass

class DataDecodingError(AdapterError):
    """Raised when decoding the response fails."""
    pass




class DataProcessingError(LiveF1Error):
    """Raised when data processing / parsing related error occurs."""
    pass

class ParsingError(DataProcessingError):
    """Raised when parsing the data fails."""
    pass

class ETLError(DataProcessingError):
    """Exception for ETL-specific issues."""
    pass

# class DataValidationError(DataProcessingError):
#     """Exception for invalid data during processing."""
#     pass




class SubscriptionError(AdapterError):
    """Exception for subscription errors."""
    pass

class DataFormatError(AdapterError):
    """Exception for unexpected data formats."""
    pass