Logging Configuration
===================

LiveF1 provides built-in logging capabilities through its ``logger`` module. The package uses Python's standard logging module with pre-configured formatters and handlers.

Basic Setup
----------

The logging system is automatically configured when you import the package. By default, it:

- Logs to both console and file (``livef1.log``)
- Sets INFO as the default log level
- Uses different formats for console and file output

Configuration Options
------------------

Log Levels
^^^^^^^^^

You can adjust the logging level using the ``set_log_level`` function:

.. code-block:: python

    from livef1.utils.logger import set_log_level
    import logging

    # Set using string
    set_log_level('DEBUG')

    # Or using logging constants
    set_log_level(logging.DEBUG)

Available log levels:
    - DEBUG: Detailed information for diagnosing problems
    - INFO: Confirmation that things are working (default)
    - WARNING: Indication that something unexpected happened
    - ERROR: More serious problem
    - CRITICAL: Program may not be able to continue

Output Formats
------------

Console output format:
    ``HH:MM:SS - message``

File output format:
    ``YYYY-MM-DD HH:MM:SS - logger_name - level - message``

Custom Handlers
-------------

You can add your own handlers to the logger:

.. code-block:: python

    from livef1.utils.logger import logger
    import logging

    # Create custom handler
    custom_handler = logging.StreamHandler()
    custom_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(custom_handler)

Example Usage
-----------

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client
    from livef1.utils.logger import logger, set_log_level
    import logging

    # Enable debug logging
    set_log_level('DEBUG')

    # Initialize client
    client = RealF1Client(topics=["CarData.z"])

    @client.callback("logging_example")
    async def handle_data(records):
        logger.debug(f"Received {len(records)} records")
        logger.info("Processing new data batch")
        
        try:
            # Process records
            process_records(records)
        except Exception as e:
            logger.error(f"Error processing records: {e}")
