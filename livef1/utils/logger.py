import logging
import os

# Logger setup
# LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO
LOG_LEVEL = logging.INFO
STREAM_LOG_FORMAT = "%(asctime)s - %(message)s"
FILE_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure logger
logger = logging.getLogger("livef1")
logger.setLevel(LOG_LEVEL)

# Handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(STREAM_LOG_FORMAT,"%H:%M:%S"))

file_handler = logging.FileHandler("livef1.log")
file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT,"%Y-%m-%d %H:%M:%S"))

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def set_log_level(level):
    """
    Set the logging level for the livef1 logger.
    
    Parameters
    ----------
    level : Union[str, int]
        The logging level to set. Can be either a string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        or the corresponding integer value.
    
    Examples
    --------
    >>> set_log_level('DEBUG')  # Set to debug level
    >>> set_log_level(logging.INFO)  # Set to info level
    """
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        level = numeric_level
        
    logger.setLevel(level)