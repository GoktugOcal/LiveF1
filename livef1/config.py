"""Package-level configuration for LiveF1.

Call :func:`configure` before running LiveF1 code to adjust logging and
F1 account authentication settings.
"""

from .utils.logger import configure_logging

_UNSET = object()

# Non-logging package settings, e.g. the defaults of :func:`livef1.login`.
_settings = {}


def configure(
    *,
    log_level=None,
    logging_stream_format=None,
    logging_stream_datefmt=None,
    logging_file_path=_UNSET,
    logging_file_format=None,
    logging_file_datefmt=None,
    auth_save_token=None,
    auth_token_path=None,
    auth_env_path=None,
):
    """
    Configure LiveF1 package settings.

    Call this before running LiveF1 code when you need non-default behaviour
    (for example logging in read-only environments such as AWS Lambda).

    Parameters
    ----------
    log_level : Union[str, int], optional
        Logging level as a string (``'DEBUG'``, ``'INFO'``, ...) or an
        ``logging`` module constant.
    logging_stream_format : str, optional
        Format string for the console (stream) handler.
    logging_stream_datefmt : str, optional
        Date/time format for the console handler.
    logging_file_path : str or pathlib.Path or None, optional
        Path to the log file. Parent directories are created if needed.
        Pass ``None`` to disable file logging. Omit to leave unchanged.
        File logging is disabled by default.
    logging_file_format : str, optional
        Format string for the file handler.
    logging_file_datefmt : str, optional
        Date/time format for the file handler.
    auth_save_token : bool, optional
        Default for :func:`livef1.login`: save the F1 account token to disk.
        Set to False to keep it in memory only.
    auth_token_path : str or pathlib.Path, optional
        Default for :func:`livef1.login`: where the token is saved
        (``~/.livef1/token.json`` if not set).
    auth_env_path : str or pathlib.Path, optional
        Default for :func:`livef1.login`: the ``.env`` file the F1 account
        credentials are read from and saved to (``.env`` if not set).

    Examples
    --------
    >>> import livef1
    >>> # Console only (default) — safe for Lambda / read-only filesystems
    >>> livef1.configure(log_level="DEBUG")
    >>> # Enable file logging at a writable path
    >>> livef1.configure(logging_file_path="/tmp/livef1.log")
    >>> # Custom formats
    >>> livef1.configure(
    ...     logging_stream_format="%(levelname)s | %(message)s",
    ...     logging_file_path="logs/livef1.log",
    ...     logging_file_format="%(asctime)s %(levelname)s %(message)s",
    ... )
    >>> # Keep the F1 account token in memory only
    >>> livef1.configure(auth_save_token=False)
    """
    for name, value in (
        ("auth_save_token", auth_save_token),
        ("auth_token_path", auth_token_path),
        ("auth_env_path", auth_env_path),
    ):
        if value is not None:
            _settings[name] = value

    logging_kwargs = {}
    if log_level is not None:
        logging_kwargs["log_level"] = log_level
    if logging_stream_format is not None:
        logging_kwargs["stream_format"] = logging_stream_format
    if logging_stream_datefmt is not None:
        logging_kwargs["stream_datefmt"] = logging_stream_datefmt
    if logging_file_path is not _UNSET:
        logging_kwargs["file_path"] = logging_file_path
    if logging_file_format is not None:
        logging_kwargs["file_format"] = logging_file_format
    if logging_file_datefmt is not None:
        logging_kwargs["file_datefmt"] = logging_file_datefmt

    if logging_kwargs:
        configure_logging(**logging_kwargs)