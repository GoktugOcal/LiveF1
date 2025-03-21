Real-Time Data
=============

LiveF1 provides real-time data access through the `RealF1Client` class, allowing you to stream live Formula 1 data during race weekends.

Creating a Real-Time Client
--------------------------

The RealF1Client automatically connects to the currently active F1 session and streams its data in real-time, with no need to specify session details:

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client

    client = RealF1Client(
        topics=["CarData.z", "SessionInfo"],
        log_file_name="./output.json"  # Optional: log incoming data
    )

.. seealso::
   For a complete list of available topics, see :ref:`data_topics`

Handling Real-Time Data
----------------------

1. Basic Handler
^^^^^^^^^^^^^^^

Create a basic handler for incoming data:

.. code-block:: python

    @client.callback("basic_handler")
    async def handle_data(records):
        print(records)  # Process incoming records

2. Logging Handler
^^^^^^^^^^^^^^^

Log data with timestamps:

.. code-block:: python

    import datetime

    @client.callback("log_handler")
    async def log_with_timestamp(records):
        with open("data_with_timestamp.log", "a") as f:
            for record in records:
                timestamp = datetime.datetime.now().isoformat()
                f.write(f"{timestamp} - {record}\n")

Running the Client
----------------

Start receiving real-time data:

.. code-block:: python

    client.run()  # Starts the client and begins receiving data


How Callbacks Work
----------------

1. **Registration**: The callback decorator registers your handler with the client:

.. code-block:: python

   @client.callback("handler_name")


2. **Activation**: When you call `client.run()`, the client:

   - Establishes a connection to the F1 live timing service

   - Subscribes to your specified topics

   - Activates all registered callbacks

3. **Data Flow**:

   - New data arrives for subscribed topics

   - Each callback receives the data as `records`

   - Callbacks process the data asynchronously

   - Multiple callbacks can handle the same data

Best Practices
-------------

1. **Connection Management**

   - Handle connection interruptions gracefully

   - Implement reconnection logic

   - Monitor connection health

2. **Data Processing**

   - Process data asynchronously to avoid blocking

   - Implement proper error handling

   - Consider data buffering for high-frequency updates

3. **Resource Management**

   - Close connections properly when done

   - Monitor memory usage
   
   - Implement proper logging

Example: Complete Real-Time Client
--------------------------------

Here's a complete example combining multiple features:

.. code-block:: python

    from livef1.adapters.realtime_client import RealF1Client
    import datetime
    import json

    # Initialize client
    client = RealF1Client(
        topics=["CarData.z", "SessionInfo", "TrackStatus"],
        log_file_name="session_data.json"
    )

    # Define multiple handlers
    @client.callback("process_telemetry")
    async def handle_telemetry(records):
        # Process car telemetry data
        telemetry_data = records.get("CarData.z")
        if telemetry_data:
            for record in telemetry_data:
                process_telemetry_data(record) # this is a placeholder for your code

    @client.callback("track_status")
    async def handle_track_status(records):
        # Monitor track conditions
        track_data = records.get("TrackStatus")
        if track_data:
            for record in track_data:
                update_track_status(record) # this is a placeholder for your code

    # Start the client
    client.run()

.. seealso::
   For information about logging configuration, see :doc:`logging_config`

Example:Database Handler
--------------------------------
Store incoming data in a database.

.. code-block:: python

    import sqlite3
    from datetime import datetime
    import json

    class F1Database:
        def __init__(self, db_name="f1_data.db"):
            self.conn = sqlite3.connect(db_name)
            self.create_tables()
        
        def create_tables(self):
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    topic TEXT,
                    driver_number INTEGER,
                    data JSON
                )
            ''')
            self.conn.commit()
        
        def insert_data(self, timestamp, topic, driver_number, data):
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO telemetry_data (timestamp, topic, driver_number, data)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, topic, driver_number, json.dumps(data)))
            self.conn.commit()

    # Initialize database
    db = F1Database()

    @client.callback("database_handler")
    async def handle_database_storage(records):
        for record in records:
            timestamp = datetime.now().isoformat()
            
            # Extract topic and driver number if available
            topic = next(iter(record.keys()))  # Get the first key as topic
            driver_number = record.get(topic, {}).get('DriverNumber', 0)
            
            # Store in database
            db.insert_data(
                timestamp=timestamp,
                topic=topic,
                driver_number=driver_number,
                data=record
            )
