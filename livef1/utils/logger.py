import logging
import os

# Logger setup
# LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s : %(name)s : %(levelname)s :: %(message)s"

# Configure logger
logger = logging.getLogger("livef1")
logger.setLevel(LOG_LEVEL)

# Handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

file_handler = logging.FileHandler("livef1.log")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)