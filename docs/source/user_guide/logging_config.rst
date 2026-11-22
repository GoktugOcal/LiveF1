Logging Configuration
=====================

LiveF1 logs through the ``livef1`` logger of Python's standard ``logging``
package. It is set up on import and adapts its output to where it runs.

What you see by default
-----------------------

``session.generate()`` logs a few summary lines and shows progress bars while
topics download and tables build:

.. code-block:: text

    12:33:06 INFO  Generating tables for 2024 Saudi Arabian Grand Prix · Race
    Downloading ███████▋        2/3 · 00:21, Position.z
    12:33:41 INFO  Downloaded 3 topics in 34.8s: CarData.z, Position.z, SessionStatus
    12:33:42 INFO  Silver: 6 tables in 0.8s
    12:33:42 ERROR Could not build gold table 'LapOneStart': KeyError: 'Distance' (log_level="DEBUG" shows the traceback)
    12:33:42 WARN  Gold: 7 tables in 0.3s, 1 failed (LapOneStart)
    12:33:42 INFO  Done in 36.1s. Tables: session.driverInfo, session.laps, ... (+8 more)

Each table's row count and build time, and the traceback of a failed table, are
logged at ``DEBUG`` level.

Output by environment
---------------------

The default style, ``log_style="auto"``, picks the output for the environment:

.. list-table::
   :header-rows: 1

   * - Environment
     - Output
   * - Terminal
     - Coloured lines on stderr, progress bars.
   * - Notebook (Jupyter, VS Code, Colab)
     - Coloured lines. ``INFO`` and ``DEBUG`` go to stdout, so they are not shown
       in the red stderr box; warnings and errors go to stderr. Progress bars are
       widgets when ``ipywidgets`` is installed, text otherwise.
   * - AWS Lambda, Google Cloud Functions / Cloud Run, Azure Functions
     - No colours or progress bars. Records go to the platform's own log handler
       when it has one, so in Lambda each line carries the request id and follows
       ``AWS_LAMBDA_LOG_FORMAT`` (text or JSON). ``AWS_LAMBDA_LOG_LEVEL`` sets
       LiveF1's default level. Without a platform handler LiveF1 prints one line
       per record to stdout; a multi-line message or traceback stays one
       CloudWatch event.
   * - Anything else (piped output, CI, files)
     - Plain lines on stderr with the date, level and logger name.

The ``NO_COLOR`` environment variable turns colours off and ``FORCE_COLOR``
turns them on. ``LIVEF1_LOG_STYLE`` sets the style without code changes.

``livef1.configure()``
----------------------

Call ``livef1.configure()`` before running LiveF1 code to change the logging
setup. The same function also holds the F1 account options (see
:ref:`authentication`) and ``dataframe_backend`` (see :ref:`dataframe_backend`):

.. code-block:: python

    import livef1

    # Debug level: per-table timings and tracebacks
    livef1.configure(log_level="DEBUG")

    # Pick a style: "auto" (default), "pretty", "plain" or "json"
    livef1.configure(log_style="plain")

    # No progress bars
    livef1.configure(progress=False)

    # Let your application's logging setup print LiveF1's records
    # (LiveF1 adds no console handler, so nothing is printed twice)
    livef1.configure(log_propagate=True)

    # Also write a log file (parent folders are created)
    livef1.configure(logging_file_path="/tmp/livef1.log")
    livef1.configure(logging_file_path=None)   # off again

    # Custom console format, used by every style
    livef1.configure(
        logging_stream_format="%(asctime)s %(levelname)s %(message)s",
        logging_stream_datefmt="%H:%M:%S",
    )

Parameters:

- ``log_level``: string (``'DEBUG'``, ``'INFO'``, ...) or a ``logging`` constant.
  Default ``INFO`` (``AWS_LAMBDA_LOG_LEVEL`` in Lambda when set).
- ``log_style``: ``"auto"``, ``"pretty"``, ``"plain"`` or ``"json"``.
- ``log_propagate``: ``True`` hands records to the root logger's handlers and
  prints nothing of LiveF1's own; ``False`` always uses LiveF1's console
  handler; ``None`` (default) propagates only in cloud runtimes that have a
  root handler.
- ``progress``: ``None`` (default) shows bars in terminals and notebooks;
  ``False`` turns them off; ``True`` also shows them when output is piped
  (never in cloud runtimes).
- ``logging_stream_format`` / ``logging_stream_datefmt``: console format.
- ``logging_file_path``: log file path (enables file logging); ``None`` disables it.
- ``logging_file_format`` / ``logging_file_datefmt``: file format.

File logging is off by default, so LiveF1 works on read-only file systems such
as AWS Lambda.

JSON logs for CloudWatch and Cloud Logging
------------------------------------------

``log_style="json"`` prints one JSON object per line with ``time`` (UTC),
``level``, ``severity``, ``logger`` and ``message``, plus structured fields:

.. code-block:: json

    {"time": "2026-11-22T15:13:05.338+00:00", "level": "INFO", "severity": "INFO",
     "logger": "livef1", "message": "Gold: 8 tables in 0.0s", "event": "tables_generated",
     "layer": "gold", "tables": ["ValidLaps", "..."], "failed": [], "duration_ms": 38}

The ``event`` values are ``generate_started``, ``topic_loaded``,
``topics_loaded``, ``table_generated`` (``DEBUG``), ``table_failed``,
``tables_generated`` and ``generate_finished``. CloudWatch Logs Insights can
filter on them, for example ``filter event = "table_failed" | stats count() by table``.

The same fields are attached to every record (``record.event``,
``record.duration_ms`` ...), so a JSON formatter of your own can use them too.

Log Levels
----------

You can also change only the level with ``set_log_level``:

.. code-block:: python

    import livef1
    import logging

    livef1.set_log_level('DEBUG')
    livef1.set_log_level(logging.DEBUG)

- DEBUG: per-table row counts and timings, tracebacks, request details
- INFO: the summary lines above (default)
- WARNING: something unexpected happened, LiveF1 carries on
- ERROR: a table or request failed
- CRITICAL: LiveF1 may not be able to continue

Warnings
--------

Python warnings raised from LiveF1's own code (for example pandas
``FutureWarning`` messages) are silenced. Warnings from your own code and other
libraries are not affected.

Custom Handlers
---------------

You can add your own handlers to the logger:

.. code-block:: python

    from livef1.utils.logger import logger
    import logging

    custom_handler = logging.StreamHandler()
    custom_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(custom_handler)

To send LiveF1's records only through your own logging setup, use
``livef1.configure(log_propagate=True)`` instead.
