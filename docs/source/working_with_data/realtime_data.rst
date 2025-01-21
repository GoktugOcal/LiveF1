Real-Time Data
===========

The `RealF1Client` class allows you to manage real-time Formula 1 data streaming. You can subscribe to various topics and handle incoming data with custom functions.

Creating a Client
-----------------

To create a `RealF1Client`, you need to specify the topics you want to subscribe to. Optionally, you can also specify a log file to store incoming messages.

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client

    client = RealF1Client(
        topics=["CarData.z", "SessionInfo"],
        log_file_name="./output.json"
    )

Writing Custom Functions
------------------------

You can write custom functions to handle incoming data by using the `callback` decorator. The function must accept the required parameters defined in `REALTIME_CALLBACK_DEFAULT_PARAMETERS`.

.. code-block:: python

    @client.callback("custom_method")
    async def custom_handler(records):
        # Process the incoming records
        print(records)

Writing Data to a File with Timestamp
-------------------------------------

You can write a custom function to log incoming data to a different file with a timestamp. The function will use the `callback` decorator and write the data to the specified file.

.. code-block:: python

    import datetime

    @client.callback("log_with_timestamp")
    async def log_with_timestamp(records):
        with open("data_with_timestamp.log", "a") as f:
            for record in records:
                timestamp = datetime.datetime.now().isoformat()
                f.write(f"{timestamp} - {record}\n")

Running the Client
------------------

To start the client and begin receiving data, call the `run` method.

.. code-block:: python

    client.run()

Example
-------

Here is a complete example of creating a client, writing a custom function, and running the client:

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client

    client = RealF1Client(
        topics=["CarData.z", "SessionInfo"],
        log_file_name="./output.json"
    )

    @client.callback("custom_method")
    async def custom_handler(records):
        # Process the incoming records
        print(records)

    client.run()

Example
-------

Here is a complete example of creating a client, writing a custom function to log data with a timestamp, and running the client:

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client
    import datetime

    client = RealF1Client(
        topics=["CarData.z", "SessionInfo"],
        log_file_name="./output.json"
    )

    @client.callback("log_with_timestamp")
    async def log_with_timestamp(records):
        with open("data_with_timestamp.log", "a") as f:
            for record in records:
                timestamp = datetime.datetime.now().isoformat()
                f.write(f"{timestamp} - {record}\n")

    client.run()