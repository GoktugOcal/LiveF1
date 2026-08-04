"""Tests for livef1 package configuration and logging."""

import logging

import pytest

from livef1.config import configure
from livef1.utils import logger as logger_module
from livef1.utils.logger import logger, set_log_level


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logger to console-only defaults after each test."""
    yield
    configure(
        log_level="INFO",
        logging_stream_format=logger_module.DEFAULT_STREAM_LOG_FORMAT,
        logging_stream_datefmt=logger_module.DEFAULT_STREAM_DATEFMT,
        logging_file_path=None,
        logging_file_format=logger_module.DEFAULT_FILE_LOG_FORMAT,
        logging_file_datefmt=logger_module.DEFAULT_FILE_DATEFMT,
    )


def _handlers_of_type(handler_type):
    return [h for h in logger.handlers if isinstance(h, handler_type)]


def test_default_has_console_only():
    assert len(_handlers_of_type(logging.StreamHandler)) >= 1
    assert _handlers_of_type(logging.FileHandler) == []


def test_configure_log_level_string():
    configure(log_level="DEBUG")
    assert logger.level == logging.DEBUG


def test_configure_log_level_int():
    configure(log_level=logging.WARNING)
    assert logger.level == logging.WARNING


def test_configure_invalid_log_level():
    with pytest.raises(ValueError, match="Invalid log level"):
        configure(log_level="NOT_A_LEVEL")


def test_set_log_level():
    set_log_level("ERROR")
    assert logger.level == logging.ERROR


def test_configure_enables_file_logging(tmp_path):
    log_file = tmp_path / "livef1.log"
    configure(logging_file_path=log_file)

    file_handlers = _handlers_of_type(logging.FileHandler)
    assert len(file_handlers) == 1

    logger.info("hello from test")
    for handler in file_handlers:
        handler.flush()

    assert log_file.exists()
    assert "hello from test" in log_file.read_text()


def test_configure_creates_parent_directories(tmp_path):
    log_file = tmp_path / "nested" / "dir" / "livef1.log"
    configure(logging_file_path=log_file)

    logger.info("nested path")
    for handler in _handlers_of_type(logging.FileHandler):
        handler.flush()

    assert log_file.exists()


def test_configure_disables_file_logging(tmp_path):
    configure(logging_file_path=tmp_path / "livef1.log")
    assert _handlers_of_type(logging.FileHandler)

    configure(logging_file_path=None)
    assert _handlers_of_type(logging.FileHandler) == []


def test_configure_stream_format():
    configure(logging_stream_format="%(levelname)s :: %(message)s")
    stream_handlers = [
        h for h in logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    assert stream_handlers
    assert "%(levelname)s :: %(message)s" in stream_handlers[0].formatter._fmt


def test_configure_lives_in_config_module():
    import livef1
    from livef1 import config as config_module

    assert livef1.configure is config_module.configure
    assert not hasattr(logger_module, "configure")
