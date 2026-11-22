"""Environment-aware logging: detection, styles, streams, propagation and progress bars."""
import json
import logging
import subprocess
import sys
import types
from pathlib import Path

import pytest

import livef1
from livef1.utils import logger as logger_module
from livef1.utils.logger import (
    JsonFormatter, PlainFormatter, PrettyFormatter, Progress, detect_environment,
    format_count, format_duration, logger,
)

ENV_VARS = [
    "AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "AWS_LAMBDA_LOG_LEVEL", "K_SERVICE",
    "FUNCTION_TARGET", "FUNCTIONS_WORKER_RUNTIME", "LIVEF1_LOG_STYLE", "NO_COLOR", "FORCE_COLOR",
]


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def env():
    """A clean environment (no cloud or colour variables); logging reset afterwards."""
    with pytest.MonkeyPatch.context() as mp:
        for name in ENV_VARS:
            mp.delenv(name, raising=False)
        mp.setattr(logger_module, "_in_notebook", lambda: False)
        mp.setattr(logger_module, "_isatty", lambda stream: False)
        yield mp
        logger_module.reset_logging()
    logger_module.reset_logging()


def _record(level=logging.INFO, msg="hello", args=None, exc_info=None, **extra):
    record = logging.LogRecord("livef1", level, __file__, 1, msg, args, exc_info)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


# --- environment detection -------------------------------------------------

def test_detects_plain_when_not_a_tty(env):
    assert detect_environment() == "plain"


def test_detects_terminal(env):
    env.setattr(logger_module, "_isatty", lambda stream: True)
    assert detect_environment() == "terminal"


@pytest.mark.parametrize("var,value", [
    ("AWS_LAMBDA_FUNCTION_NAME", "fn"), ("AWS_EXECUTION_ENV", "AWS_Lambda_python3.12"),
])
def test_detects_lambda(env, var, value):
    env.setenv(var, value)
    assert detect_environment() == "lambda"


@pytest.mark.parametrize("var", ["K_SERVICE", "FUNCTION_TARGET", "FUNCTIONS_WORKER_RUNTIME"])
def test_detects_other_cloud_runtimes(env, var):
    env.setenv(var, "x")
    assert detect_environment() == "cloud"


def test_detects_jupyter_kernel(env):
    env.undo()  # restore the real _in_notebook, keep a clean environment below
    for name in ENV_VARS:
        env.delenv(name, raising=False)
    ZMQInteractiveShell = type("ZMQInteractiveShell", (), {})
    fake_ipython = types.SimpleNamespace(get_ipython=lambda: ZMQInteractiveShell())
    env.setitem(sys.modules, "IPython", fake_ipython)
    assert detect_environment() == "notebook"


def test_terminal_ipython_is_not_a_notebook(env):
    env.undo()
    for name in ENV_VARS:
        env.delenv(name, raising=False)
    env.setattr(logger_module, "_isatty", lambda stream: False)
    TerminalInteractiveShell = type("TerminalInteractiveShell", (), {})
    env.setitem(sys.modules, "IPython", types.SimpleNamespace(get_ipython=lambda: TerminalInteractiveShell()))
    assert detect_environment() == "plain"


# --- style resolution ------------------------------------------------------

def test_auto_style_by_environment(env):
    logger_module.reset_logging()
    assert logger_module._resolved["style"] == "plain"
    env.setattr(logger_module, "_isatty", lambda stream: True)
    logger_module.reset_logging()
    assert logger_module._resolved["style"] == "pretty"
    assert isinstance(logger_module._console_handler.formatter, PrettyFormatter)


def test_no_color_and_force_color(env):
    env.setattr(logger_module, "_isatty", lambda stream: True)
    env.setenv("NO_COLOR", "1")
    logger_module.reset_logging()
    assert logger_module._resolved["style"] == "plain"
    env.delenv("NO_COLOR")
    env.setattr(logger_module, "_isatty", lambda stream: False)
    env.setenv("FORCE_COLOR", "1")
    logger_module.reset_logging()
    assert logger_module._resolved["style"] == "pretty"


def test_style_from_environment_variable_and_configure(env):
    env.setenv("LIVEF1_LOG_STYLE", "json")
    logger_module.reset_logging()
    assert isinstance(logger_module._console_handler.formatter, JsonFormatter)
    livef1.configure(log_style="plain")
    assert isinstance(logger_module._console_handler.formatter, PlainFormatter)


def test_invalid_style_raises(env):
    with pytest.raises(ValueError, match="Invalid log style"):
        livef1.configure(log_style="fancy")


def test_custom_stream_format_applies_to_every_style(env):
    livef1.configure(log_style="pretty", logging_stream_format="%(levelname)s | %(message)s")
    assert "%(levelname)s | %(message)s" in logger_module._console_handler.formatter._fmt
    livef1.configure(log_style="plain")
    assert "%(levelname)s | %(message)s" in logger_module._console_handler.formatter._fmt


# --- formatters ------------------------------------------------------------

def test_pretty_formatter_colours_level_and_quoted_names():
    text = PrettyFormatter("%(levelname)s %(message)s").format(_record(msg="Built table '%s'", args=("laps",)))
    assert "\x1b[36mINFO \x1b[0m" in text
    assert "\x1b[1mlaps\x1b[0m" in text


def test_pretty_formatter_dims_traceback():
    try:
        raise KeyError("x")
    except KeyError:
        record = _record(level=logging.ERROR, msg="failed", exc_info=sys.exc_info())
    text = PrettyFormatter("%(levelname)s %(message)s").format(record)
    first, rest = text.split("\n", 1)
    assert "ERROR" in first and rest.startswith("\x1b[2m") and "KeyError" in rest


def test_plain_formatter_single_line_keeps_traceback_in_one_event():
    try:
        raise ValueError("boom")
    except ValueError:
        record = _record(level=logging.ERROR, msg="line one\nline two", exc_info=sys.exc_info())
    text = PlainFormatter("%(levelname)s %(message)s", single_line=True).format(record)
    assert "\n" not in text
    assert "line one\rline two" in text and "ValueError: boom" in text
    assert text.startswith("ERROR   ")


def test_json_formatter_includes_extra_fields_and_exception():
    try:
        raise KeyError("Status")
    except KeyError:
        record = _record(level=logging.ERROR, msg="Could not build '%s'", args=("trackEvents",),
                         exc_info=sys.exc_info(), event="table_failed", table="trackEvents", duration_ms=12)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == payload["severity"] == "ERROR"
    assert payload["message"] == "Could not build 'trackEvents'"
    assert payload["event"] == "table_failed" and payload["table"] == "trackEvents" and payload["duration_ms"] == 12
    assert "KeyError" in payload["exception"]
    assert payload["logger"] == "livef1" and payload["time"].endswith("+00:00")


# --- streams and propagation -----------------------------------------------

def test_plain_output_goes_to_current_stderr(env, capsys):
    logger_module.reset_logging()
    logger.info("to stderr")
    captured = capsys.readouterr()
    assert "to stderr" in captured.err and captured.out == ""


def test_notebook_sends_info_to_stdout_and_warnings_to_stderr(env, capsys):
    env.setattr(logger_module, "_in_notebook", lambda: True)
    logger_module.reset_logging()
    assert logger_module._resolved["environment"] == "notebook"
    logger.info("info line")
    logger.warning("warning line")
    captured = capsys.readouterr()
    assert "info line" in captured.out and "info line" not in captured.err
    assert "warning line" in captured.err and "warning line" not in captured.out


def test_lambda_propagates_to_the_runtime_handler(env):
    env.setenv("AWS_LAMBDA_FUNCTION_NAME", "fn")
    env.setenv("AWS_LAMBDA_LOG_LEVEL", "DEBUG")
    runtime = ListHandler()
    root = logging.getLogger()
    env.setattr(root, "handlers", [runtime])
    env.setattr(root, "level", logging.WARNING)
    logger_module.reset_logging()
    assert logger.propagate is True
    assert logger_module._console_handler is None
    assert logger.level == logging.DEBUG
    logger.info("reaches the runtime handler", extra={"event": "x"})
    assert [r.getMessage() for r in runtime.records] == ["reaches the runtime handler"]
    assert runtime.records[0].event == "x"


def test_lambda_without_runtime_handler_prints_single_lines_to_stdout(env, capsys):
    env.setenv("AWS_LAMBDA_FUNCTION_NAME", "fn")
    # pytest's own capture handler sits on the root logger during the test
    env.setattr(logging.getLogger(), "handlers", [])
    logger_module.reset_logging()
    assert logger.propagate is False
    logger.info("first\nsecond")
    captured = capsys.readouterr()
    assert captured.out.count("\n") == 1 and "first\rsecond" in captured.out
    assert "\x1b[" not in captured.out


def test_explicit_style_in_lambda_uses_own_handler(env, capsys):
    env.setenv("AWS_LAMBDA_FUNCTION_NAME", "fn")
    env.setattr(logging.getLogger(), "handlers", [ListHandler()])
    livef1.configure(log_style="json")
    assert logger.propagate is False
    logger.info("json line")
    assert json.loads(capsys.readouterr().out)["message"] == "json line"


def test_log_propagate_true_uses_the_applications_handlers(env, capsys):
    livef1.configure(log_propagate=True)
    assert logger.propagate is True and logger_module._console_handler is None
    livef1.configure(log_propagate=None)
    assert logger.propagate is False and logger_module._console_handler is not None


def test_file_handler_still_works_with_styles(env, tmp_path):
    log_file = tmp_path / "livef1.log"
    livef1.configure(log_style="json", logging_file_path=log_file)
    logger.info("to file")
    logger_module._file_handler.flush()
    assert "INFO - to file" in log_file.read_text()


# --- progress bars ---------------------------------------------------------

def test_progress_off_when_output_is_piped(env):
    logger_module.reset_logging()
    assert Progress(3, "Downloading").enabled is False


def test_progress_on_in_terminal_writes_bar_to_stderr(env, capsys):
    env.setattr(logger_module, "_isatty", lambda stream: True)
    logger_module.reset_logging()
    bar = Progress(2, "Downloading", unit="topic")
    try:
        assert bar.enabled
        bar.step("CarData.z")
        bar.advance()
        logger.info("between steps")
    finally:
        bar.close()
    assert logger_module._active_bars == []
    err = capsys.readouterr().err
    assert "Downloading" in err and "CarData.z" in err and "between steps" in err


@pytest.mark.parametrize("setup", ["progress_false", "json", "warning_level", "lambda"])
def test_progress_disabled(env, setup):
    env.setattr(logger_module, "_isatty", lambda stream: True)
    if setup == "lambda":
        env.setenv("AWS_LAMBDA_FUNCTION_NAME", "fn")
        livef1.configure(progress=True)
    elif setup == "progress_false":
        livef1.configure(progress=False)
    elif setup == "json":
        livef1.configure(log_style="json")
    else:
        livef1.configure(log_level="WARNING")
    assert Progress(3, "x").enabled is False


def test_progress_true_shows_bar_when_piped(env):
    livef1.configure(progress=True)
    bar = Progress(1, "x")
    try:
        assert bar.enabled
    finally:
        bar.close()


def test_format_helpers():
    assert format_duration(0.42) == "0.4s"
    assert format_duration(83) == "1m 23s"
    assert format_count(1104) == "1,104"
    assert format_count(2_912_000) == "2.9M"


# --- warnings filter -------------------------------------------------------

def test_import_only_silences_livef1_warnings():
    code = (
        "import warnings, livef1\n"
        "with warnings.catch_warnings(record=True) as caught:\n"
        "    warnings.warn('user code', UserWarning)\n"
        "    warnings.warn_explicit('library code', FutureWarning, 'x.py', 1, module='livef1.models.session')\n"
        "print(sorted(str(w.message) for w in caught))\n"
    )
    root = Path(__file__).resolve().parent.parent
    out = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=True).stdout
    assert out.strip() == "['user code']"


def test_notebook_text_bar_is_cleared_before_a_log_line(env, capsys):
    # A notebook without ipywidgets draws a text bar on stdout; a log line must
    # not be appended to the bar's line.
    env.setattr(logger_module, "_in_notebook", lambda: True)
    env.setattr(logger_module, "_notebook_widgets_available", lambda: False)
    logger_module.reset_logging()
    bar = Progress(3, "Building tables")
    try:
        assert bar.enabled and bar.is_text
        bar.step("laps")
        logger.info("between steps")
    finally:
        bar.close()
    out = capsys.readouterr().out
    idx = out.index("between steps")
    line_start = max(out.rfind("\r", 0, idx), out.rfind("\n", 0, idx))
    # tqdm.write cleared the bar, so the log line starts on a fresh line
    assert "Building tables" not in out[line_start:idx] and "laps" not in out[line_start:idx]
    assert "Building tables" in out and "laps" in out
