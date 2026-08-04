import logging
from pathlib import Path

# Defaults
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_STREAM_LOG_FORMAT = "%(asctime)s - %(name)s - %(message)s"
DEFAULT_STREAM_DATEFMT = "%H:%M:%S"
DEFAULT_FILE_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S"

# Public aliases kept for backwards compatibility
LOG_LEVEL = DEFAULT_LOG_LEVEL
STREAM_LOG_FORMAT = DEFAULT_STREAM_LOG_FORMAT
FILE_LOG_FORMAT = DEFAULT_FILE_LOG_FORMAT

_UNSET = object()

logger = logging.getLogger("livef1")
logger.propagate = False

_console_handler = None
_file_handler = None

_logging_config = {
    "log_level": DEFAULT_LOG_LEVEL,
    "stream_format": DEFAULT_STREAM_LOG_FORMAT,
    "stream_datefmt": DEFAULT_STREAM_DATEFMT,
    "file_path": None,
    "file_format": DEFAULT_FILE_LOG_FORMAT,
    "file_datefmt": DEFAULT_FILE_DATEFMT,
}


def _resolve_level(level):
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        return numeric_level
    return level


def _remove_handler(handler):
    if handler is not None:
        logger.removeHandler(handler)
        handler.close()
    return None


def _apply_logging_config():
    """Apply the current logging configuration to the livef1 logger."""
    global _console_handler, _file_handler

    logger.setLevel(_logging_config["log_level"])

    _console_handler = _remove_handler(_console_handler)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(
        logging.Formatter(
            _logging_config["stream_format"],
            _logging_config["stream_datefmt"],
        )
    )
    logger.addHandler(_console_handler)

    _file_handler = _remove_handler(_file_handler)
    if _logging_config["file_path"]:
        path = Path(_logging_config["file_path"])
        if path.parent and str(path.parent) not in (".", ""):
            path.parent.mkdir(parents=True, exist_ok=True)
        _file_handler = logging.FileHandler(path)
        _file_handler.setFormatter(
            logging.Formatter(
                _logging_config["file_format"],
                _logging_config["file_datefmt"],
            )
        )
        logger.addHandler(_file_handler)


def configure_logging(
    *,
    log_level=None,
    stream_format=None,
    stream_datefmt=None,
    file_path=_UNSET,
    file_format=None,
    file_datefmt=None,
):
    """
    Apply logging options to the livef1 logger.

    Prefer :func:`livef1.configure` for package-level setup. This function is
    the logging backend used by that API.
    """
    if log_level is not None:
        _logging_config["log_level"] = _resolve_level(log_level)
    if stream_format is not None:
        _logging_config["stream_format"] = stream_format
    if stream_datefmt is not None:
        _logging_config["stream_datefmt"] = stream_datefmt
    if file_path is not _UNSET:
        _logging_config["file_path"] = None if file_path is None else str(file_path)
    if file_format is not None:
        _logging_config["file_format"] = file_format
    if file_datefmt is not None:
        _logging_config["file_datefmt"] = file_datefmt

    _apply_logging_config()


def set_log_level(level):
    """
    Set the logging level for the livef1 logger.

    Parameters
    ----------
    level : Union[str, int]
        The logging level to set. Can be either a string
        (``'DEBUG'``, ``'INFO'``, ``'WARNING'``, ``'ERROR'``, ``'CRITICAL'``)
        or the corresponding integer value.

    Examples
    --------
    >>> set_log_level('DEBUG')
    >>> set_log_level(logging.INFO)
    """
    level = _resolve_level(level)
    _logging_config["log_level"] = level
    logger.setLevel(level)


# Console-only defaults on import (no file handler — safe for read-only FS)
_apply_logging_config()
