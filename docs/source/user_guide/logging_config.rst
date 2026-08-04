Logging Configuration
===================

LiveF1 provides built-in logging through its ``logger`` module, built on Python's
standard ``logging`` package.

Basic Setup
----------

Logging is configured automatically on import. By default it:

- Logs to the **console only** (no file handler)
- Uses ``INFO`` as the default log level
- Uses a compact console format

File logging is **optional** and off by default so LiveF1 works in read-only
environments such as containerized AWS Lambda functions.

``livef1.configure()``
--------------------

Use the package-level ``livef1.configure()`` (from ``livef1.config``) before
running LiveF1 code to change log level, formats, or enable file logging.
Additional non-logging options may be added to this API later:

.. code-block:: python

    import livef1

    # Console only, debug level (safe for Lambda / read-only filesystems)
    livef1.configure(log_level="DEBUG")

    # Enable file logging at a writable path
    livef1.configure(file_path="/tmp/livef1.log")

    # Custom stream and file formats
    livef1.configure(
        log_level="INFO",
        stream_format="%(asctime)s - %(name)s - %(message)s",
        stream_datefmt="%H:%M:%S",
        file_path="logs/livef1.log",
        file_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        file_datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Disable file logging again
    livef1.configure(file_path=None)

Parameters:

- ``log_level``: string (``'DEBUG'``, ``'INFO'``, ...) or a ``logging`` constant
- ``stream_format`` / ``stream_datefmt``: console handler format
- ``file_path``: path to the log file (enables file logging); ``None`` disables it
- ``file_format`` / ``file_datefmt``: file handler format

Parent directories for ``file_path`` are created automatically when needed.

Log Levels
^^^^^^^^^

You can also change only the level with ``set_log_level``:

.. code-block:: python

    import livef1
    import logging

    livef1.set_log_level('DEBUG')
    livef1.set_log_level(logging.DEBUG)

Available log levels:

- DEBUG: Detailed information for diagnosing problems
- INFO: Confirmation that things are working (default)
- WARNING: Indication that something unexpected happened
- ERROR: More serious problem
- CRITICAL: Program may not be able to continue

Default Output Formats
--------------------

Console output format:

    ``HH:MM:SS - logger_name - message``

File output format (when enabled):

    ``YYYY-MM-DD HH:MM:SS - logger_name - level - message``

Custom Handlers
-------------

You can still add your own handlers to the logger:

.. code-block:: python

    from livef1.utils.logger import logger
    import logging

    custom_handler = logging.StreamHandler()
    custom_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(custom_handler)

Example Usage
-----------

.. code-block:: python

    import livef1
    from livef1.adapters.realtime_client import RealF1Client
    from livef1.utils.logger import logger

    livef1.configure(log_level="DEBUG", file_path="/tmp/livef1.log")

    client = RealF1Client(topics=["CarData.z"])

    @client.callback("logging_example")
    async def handle_data(records):
        logger.debug(f"Received {len(records)} records")
        logger.info("Processing new data batch")

        try:
            process_records(records)
        except Exception as e:
            logger.error(f"Error processing records: {e}")
