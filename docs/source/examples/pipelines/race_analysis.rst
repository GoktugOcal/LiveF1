Race Analysis Pipeline
====================

This example demonstrates a complete end-to-end pipeline for analyzing Formula 1 race data, including lap times, tire strategies, and performance metrics.

Setup
-----

First, let's import the required libraries:

.. code-block:: python

    import livef1
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from datetime import timedelta

Loading Race Data
---------------

.. code-block:: python

    # Get the race session
    race = livef1.get_session(
        season=2024,
        meeting_identifier="Spa",
        session_identifier="Race"
    )

    # Generate silver tables
    race.generate(silver=True)

    # Load different data types
    laps = race.laps
    telemetry = race.carTelemetry
    weather = race.get_weather()
    timing = race.get_timing()

Lap Time Analysis
---------------

.. code-block:: python

    def analyze_lap_times(laps_df):
        # Calculate average lap times per driver
        avg_lap_times = laps_df.groupby('DriverNo')['lap_time'].mean()
        
        # Create lap time evolution plot
        plt.figure(figsize=(15, 8))
        for driver in laps_df['DriverNo'].unique():
            driver_laps = laps_df[(laps_df['DriverNo'] == driver) & (laps_df['lap_time'] > timedelta(seconds=10))]
            plt.plot(
                driver_laps['lap_number'], 
                driver_laps['lap_time'],
                label=f'Driver {driver}'
            )
        
        plt.title('Lap Time Evolution')
        plt.xlabel('Lap Number')
        plt.ylabel('Lap Time (seconds)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
        return avg_lap_times

    avg_lap_times = analyze_lap_times(laps)
    print("\nAverage Lap Times:")
    print(avg_lap_times)


Performance Analysis
-----------------

.. code-block:: python

    def analyze_performance(telemetry_df):
        # Calculate speed statistics per driver
        speed_stats = telemetry_df.groupby('DriverNo').agg({
            'speed': ['mean', 'max', 'std']
        })
        
        # Create speed distribution plot
        plt.figure(figsize=(15, 8))
        sns.boxplot(data=telemetry_df, x='DriverNo', y='speed')
        plt.title('Speed Distribution by Driver')
        plt.xlabel('Driver Number')
        plt.ylabel('Speed (km/h)')
        plt.grid(True)
        plt.show()
        
        return speed_stats

    performance_stats = analyze_performance(telemetry)
    print("\nPerformance Statistics:")
    print(performance_stats)

Complete Pipeline
---------------

Here's how to combine all analyses into a complete pipeline:

.. code-block:: python

    def race_analysis_pipeline(session):
        # Generate required data
        session.generate(silver=True)
        
        # Load data
        laps = session.laps
        telemetry = session.carTelemetry
        
        # Run analyses
        lap_analysis = analyze_lap_times(laps)
        performance_analysis = analyze_performance(telemetry)
        
        # Combine results
        results = {
            'lap_times': lap_analysis,
            'performance': performance_analysis
        }
        
        return results

    # Run the complete pipeline
    race_results = race_analysis_pipeline(race)

    # Export results
    for analysis_name, data in race_results.items():
        data.to_csv(f'{analysis_name}.csv')