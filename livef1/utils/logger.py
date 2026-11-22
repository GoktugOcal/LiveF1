"""
Logging for LiveF1.

The ``livef1`` logger picks an output style for where it runs:

* **Terminal (TTY):** coloured lines on stderr, tqdm progress bars.
* **Notebook (Jupyter, VS Code, Colab):** coloured lines; INFO and below go to
  stdout (no red stderr box), warnings and errors to stderr; widget progress bars.
* **AWS Lambda, Google Cloud Functions/Run, Azure Functions:** no colours or
  bars. Records propagate to the platform's root handler when it has one (in
  Lambda that adds the request id and honours ``AWS_LAMBDA_LOG_FORMAT``);
  otherwise one line per record on stdout. ``AWS_LAMBDA_LOG_LEVEL`` sets the
  default level.
* **Anything else (pipes, CI, files):** plain lines on stderr.

Override with ``livef1.configure(log_style=...)`` (``"auto"``, ``"pretty"``,
``"plain"``, ``"json"``) or the ``LIVEF1_LOG_STYLE`` environment variable.
``NO_COLOR`` turns colours off and ``FORCE_COLOR`` turns them on.
"""
import copy
import json
import logging
import os
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Defaults
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_STREAM_LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_STREAM_DATEFMT = "%H:%M:%S"
DEFAULT_PLAIN_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DEFAULT_PLAIN_DATEFMT = "%Y-%m-%d %H:%M:%S"
DEFAULT_FILE_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S"

LOG_STYLES = ("auto", "pretty", "plain", "json")
CLOUD_ENVIRONMENTS = ("lambda", "cloud")

# Public aliases kept for backwards compatibility
LOG_LEVEL = DEFAULT_LOG_LEVEL
STREAM_LOG_FORMAT = DEFAULT_STREAM_LOG_FORMAT
FILE_LOG_FORMAT = DEFAULT_FILE_LOG_FORMAT

_UNSET = object()

logger = logging.getLogger("livef1")
logger.propagate = False

_console_handler = None
_file_handler = None


def _default_config():
    return {
        "log_level": None,          # None: AWS_LAMBDA_LOG_LEVEL in Lambda, else INFO
        "log_style": None,          # None: LIVEF1_LOG_STYLE, else "auto"
        "log_propagate": None,      # None: propagate only in cloud runtimes with a root handler
        "progress": None,           # None: bars in terminals and notebooks only
        "stream_format": None,      # None: the style's default
        "stream_datefmt": None,
        "file_path": None,
        "file_format": DEFAULT_FILE_LOG_FORMAT,
        "file_datefmt": DEFAULT_FILE_DATEFMT,
    }


_logging_config = _default_config()

# What the last _apply_logging_config() resolved; read by the handler, progress() and tests.
_resolved = {"environment": None, "style": None, "propagate": False}


# --------------------------------------------------------------------------
# Environment detection
# --------------------------------------------------------------------------

def _in_notebook():
    ipython = sys.modules.get("IPython")
    if ipython is None:
        return False
    try:
        shell = ipython.get_ipython()
    except Exception:
        return False
    if shell is None:
        return False
    name = type(shell).__name__
    module = type(shell).__module__ or ""
    return name == "ZMQInteractiveShell" or module.startswith("google.colab")


def _isatty(stream):
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def detect_environment():
    """
    Where LiveF1 is running: ``"lambda"``, ``"cloud"``, ``"notebook"``,
    ``"terminal"`` or ``"plain"`` (piped output, CI, files).
    """
    env = os.environ
    if env.get("AWS_LAMBDA_FUNCTION_NAME") or env.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda"):
        return "lambda"
    if env.get("K_SERVICE") or env.get("FUNCTION_TARGET") or env.get("FUNCTIONS_WORKER_RUNTIME"):
        return "cloud"
    if _in_notebook():
        return "notebook"
    if _isatty(sys.stderr):
        return "terminal"
    return "plain"


def _env_flag(name):
    value = os.environ.get(name)
    return value is not None and value not in ("", "0")


def _env_style():
    style = os.environ.get("LIVEF1_LOG_STYLE", "").strip().lower()
    return style if style in LOG_STYLES and style != "auto" else None


def _resolve_style(style, environment):
    style = style or _env_style() or "auto"
    if style != "auto":
        return style
    if environment in CLOUD_ENVIRONMENTS:
        return "plain"
    if _env_flag("NO_COLOR"):
        return "plain"
    if environment in ("terminal", "notebook") or _env_flag("FORCE_COLOR"):
        return "pretty"
    return "plain"


def _resolve_level(level):
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        return numeric_level
    return level


def _effective_level(environment):
    if _logging_config["log_level"] is not None:
        return _logging_config["log_level"]
    if environment == "lambda" and os.environ.get("AWS_LAMBDA_LOG_LEVEL"):
        try:
            return _resolve_level(os.environ["AWS_LAMBDA_LOG_LEVEL"])
        except ValueError:
            pass
    return DEFAULT_LOG_LEVEL


# --------------------------------------------------------------------------
# Formatters
# --------------------------------------------------------------------------

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"
_LEVEL_STYLES = {
    logging.DEBUG: ("DEBUG", "\x1b[2;35m"),        # dim magenta
    logging.INFO: ("INFO ", "\x1b[36m"),           # cyan
    logging.WARNING: ("WARN ", "\x1b[33m"),        # yellow
    logging.ERROR: ("ERROR", "\x1b[1;31m"),        # bold red
    logging.CRITICAL: ("CRIT ", "\x1b[1;37;41m"),  # white on red
}

# Attributes every LogRecord has; anything else came in through ``extra=``.
_RECORD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime", "taskName"}


def _level_style(levelno):
    for threshold in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO):
        if levelno >= threshold:
            return _LEVEL_STYLES[threshold]
    return _LEVEL_STYLES[logging.DEBUG]


def _highlight_quoted(text, on, off):
    """Wrap short ``'quoted'`` names (tables, topics) in ``on``/``off`` codes."""
    out, i = [], 0
    while True:
        start = text.find("'", i)
        end = text.find("'", start + 1) if start != -1 else -1
        if start == -1 or end == -1:
            out.append(text[i:])
            return "".join(out)
        inner = text[start + 1:end]
        if inner and "\n" not in inner and len(inner) <= 60:
            out.append(text[i:start] + on + inner + off)
        else:
            out.append(text[i:end + 1])
        i = end + 1


class PrettyFormatter(logging.Formatter):
    """Coloured output: dim time, coloured level badge, quoted names in bold."""

    def formatTime(self, record, datefmt=None):
        return _DIM + super().formatTime(record, datefmt) + _RESET

    def format(self, record):
        record = copy.copy(record)
        label, colour = _level_style(record.levelno)
        record.levelname = colour + label + _RESET
        message = record.getMessage()
        if record.levelno < logging.WARNING:
            message = _highlight_quoted(message, _BOLD, _RESET)
        record.msg, record.args = message, None
        text = super().format(record)
        if record.exc_info or record.stack_info:
            head, sep, tail = text.partition("\n")
            if sep:
                text = head + "\n" + _DIM + tail + _RESET
        return text


class PlainFormatter(logging.Formatter):
    """Plain text with a padded level name; ``single_line`` keeps a record in one line."""

    def __init__(self, fmt=None, datefmt=None, single_line=False):
        super().__init__(fmt, datefmt)
        self.single_line = single_line

    def format(self, record):
        record = copy.copy(record)
        record.levelname = f"{record.levelname:<7}"
        text = super().format(record)
        if self.single_line:
            # CloudWatch and most log routers start a new event at "\n"; "\r"
            # keeps a traceback in one event (the Lambda runtime does the same).
            text = text.replace("\n", "\r")
        return text


class JsonFormatter(logging.Formatter):
    """
    One JSON object per line: ``time`` (UTC ISO 8601), ``level``, ``severity``,
    ``logger``, ``message``, any ``extra=`` fields (``event``, ``table``,
    ``rows``, ``duration_ms`` ...) and ``exception`` when there is a traceback.
    CloudWatch Logs Insights and Google Cloud Logging read the fields directly.
    """

    def format(self, record):
        payload = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _RECORD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


# --------------------------------------------------------------------------
# Console handler
# --------------------------------------------------------------------------

class ConsoleHandler(logging.StreamHandler):
    """
    Writes to the stream that is current at emit time, so notebook and test
    capture redirections are honoured.

    ``split_streams`` sends INFO and below to stdout and warnings and errors to
    stderr; otherwise ``stream_name`` picks the stream. While a text progress
    bar is shown (terminal, or a notebook without ipywidgets), lines go through
    ``tqdm.write``, which clears the bar, writes the line and redraws the bar,
    so a line never lands at the end of the bar.
    """

    def __init__(self, stream_name="stderr", split_streams=False):
        super().__init__(getattr(sys, stream_name))
        self.stream_name = stream_name
        self.split_streams = split_streams

    def _target(self, record):
        if self.split_streams:
            return sys.stdout if record.levelno < logging.WARNING else sys.stderr
        return getattr(sys, self.stream_name)

    def emit(self, record):
        try:
            stream = self._target(record)
            self.stream = stream
            msg = self.format(record)
            if any(bar.is_text for bar in _active_bars):
                from tqdm import tqdm as _tqdm
                _tqdm.write(msg, file=stream)
            else:
                stream.write(msg + self.terminator)
                self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def _make_console_formatter(style, environment):
    fmt = _logging_config["stream_format"]
    datefmt = _logging_config["stream_datefmt"]
    if style == "json":
        return JsonFormatter()
    if style == "pretty":
        return PrettyFormatter(fmt or DEFAULT_STREAM_LOG_FORMAT, datefmt or DEFAULT_STREAM_DATEFMT)
    return PlainFormatter(
        fmt or DEFAULT_PLAIN_LOG_FORMAT,
        datefmt or (DEFAULT_STREAM_DATEFMT if fmt else DEFAULT_PLAIN_DATEFMT),
        single_line=environment in CLOUD_ENVIRONMENTS,
    )


def _remove_handler(handler):
    if handler is not None:
        logger.removeHandler(handler)
        handler.close()
    return None


def _apply_logging_config():
    """Apply the current logging configuration to the livef1 logger."""
    global _console_handler, _file_handler

    environment = detect_environment()
    explicit_style = _logging_config["log_style"] not in (None, "auto") or _env_style() is not None
    style = _resolve_style(_logging_config["log_style"], environment)

    propagate = _logging_config["log_propagate"]
    if propagate is None:
        # Hand records to the platform's handler (Lambda's adds the request id
        # and does the JSON formatting) unless the user picked a style.
        propagate = (
            environment in CLOUD_ENVIRONMENTS
            and not explicit_style
            and bool(logging.getLogger().handlers)
        )

    _resolved.update(environment=environment, style=style, propagate=propagate)

    logger.setLevel(_effective_level(environment))
    logger.propagate = propagate

    _console_handler = _remove_handler(_console_handler)
    if not propagate:
        if environment == "notebook":
            handler = ConsoleHandler(split_streams=True)
        elif environment in CLOUD_ENVIRONMENTS:
            handler = ConsoleHandler(stream_name="stdout")
        else:
            handler = ConsoleHandler(stream_name="stderr")
        handler.setFormatter(_make_console_formatter(style, environment))
        _console_handler = handler
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
    log_style=None,
    log_propagate=_UNSET,
    progress=_UNSET,
):
    """
    Apply logging options to the livef1 logger.

    Prefer :func:`livef1.configure` for package-level setup. This function is
    the logging backend used by that API.
    """
    if log_level is not None:
        _logging_config["log_level"] = _resolve_level(log_level)
    if log_style is not None:
        style = str(log_style).strip().lower()
        if style not in LOG_STYLES:
            raise ValueError(f"Invalid log style: {log_style!r}. Use one of: {', '.join(LOG_STYLES)}.")
        _logging_config["log_style"] = style
    if log_propagate is not _UNSET:
        _logging_config["log_propagate"] = None if log_propagate is None else bool(log_propagate)
    if progress is not _UNSET:
        _logging_config["progress"] = None if progress is None else bool(progress)
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


def reset_logging():
    """Restore the default logging configuration."""
    _logging_config.clear()
    _logging_config.update(_default_config())
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


# --------------------------------------------------------------------------
# Progress bars and timings
# --------------------------------------------------------------------------

_active_bars = []


def progress_enabled():
    """Whether :func:`progress` shows a bar with the current configuration."""
    setting = _logging_config["progress"]
    if setting is False:
        return False
    if not logger.isEnabledFor(logging.INFO) or _resolved["style"] == "json":
        return False
    environment = detect_environment()
    if setting is True:
        return environment not in CLOUD_ENVIRONMENTS
    return environment in ("terminal", "notebook")


def _notebook_widgets_available():
    try:
        import ipywidgets  # noqa: F401
    except Exception:
        return False
    return True


def _supports_unicode(stream):
    encoding = getattr(stream, "encoding", None) or ""
    return "utf" in encoding.lower()


class Progress:
    """
    A progress bar, or a no-op when bars are off. ``enabled`` says which, so
    callers can log one line per step when there is no bar.
    """

    def __init__(self, total, desc, unit="it", show=True):
        self.enabled = bool(show) and progress_enabled()
        self.is_text = False
        self._bar = None
        self._stop = threading.Event()
        self._thread = None
        if not self.enabled:
            return
        environment = detect_environment()
        try:
            if environment == "notebook" and _notebook_widgets_available():
                from tqdm.notebook import tqdm as bar_cls
                self._bar = bar_cls(total=total, desc=desc, unit=unit, leave=False)
            else:
                from tqdm import tqdm as bar_cls
                stream = sys.stdout if environment == "notebook" else sys.stderr
                self._bar = bar_cls(
                    total=total, desc=desc, unit=unit, leave=False, file=stream,
                    dynamic_ncols=True, ascii=None if _supports_unicode(stream) else True,
                    bar_format="{desc} {bar:20} {n_fmt}/{total_fmt} · {elapsed}{postfix}",
                )
                self.is_text = True
        except Exception:
            self.enabled = False
            self._bar = None
            return
        _active_bars.append(self)
        # Keep the elapsed time ticking while one long step (a large topic
        # download) runs, so the bar never looks frozen.
        self._thread = threading.Thread(target=self._tick, name="livef1-progress", daemon=True)
        self._thread.start()

    def _tick(self):
        while not self._stop.wait(0.5):
            bar = self._bar
            if bar is None:
                return
            try:
                bar.refresh()
            except Exception:
                return

    def step(self, item):
        """Show ``item`` as the step in progress."""
        if self._bar is not None:
            self._bar.set_postfix_str(str(item), refresh=True)

    def advance(self, n=1):
        if self._bar is not None:
            self._bar.update(n)

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
        if self in _active_bars:
            _active_bars.remove(self)
        if self._bar is not None:
            bar, self._bar = self._bar, None
            bar.close()


@contextmanager
def progress(total, desc, unit="it", show=True):
    """
    Context manager yielding a :class:`Progress`. ``show=False`` gives a no-op bar.

    >>> with progress(len(topics), "Downloading", unit="topic") as bar:
    ...     for topic in topics:
    ...         bar.step(topic)
    ...         download(topic)
    ...         bar.advance()
    """
    bar = Progress(total, desc, unit, show=show)
    try:
        yield bar
    finally:
        bar.close()


def format_duration(seconds):
    """``0.42`` -> ``"0.4s"``, ``83`` -> ``"1m 23s"``."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes}m {secs:02d}s"


def format_count(n):
    """``1104`` -> ``"1,104"``, ``2_912_000`` -> ``"2.9M"``."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n:,}"


class Timer:
    """``with Timer() as t: ...``, then ``t.seconds`` and ``t.ms``."""

    def __enter__(self):
        self._start = time.perf_counter()
        self.seconds = 0.0
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self._start
        return False

    @property
    def ms(self):
        return int(round(self.seconds * 1000))


# Console defaults on import (no file handler — safe for read-only FS)
_apply_logging_config()
