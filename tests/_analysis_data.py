"""Small synthetic race shaped like LiveF1's silver tables, for the analysis tests.

Three drivers, six laps. Track status: green, safety car deployed during lap 4,
green again during lap 6 (lap 5 is run entirely behind the safety car). Driver 44
pits at the end of lap 3 (PitIn on lap 3, PitOut on lap 4). Driver 16 spins on lap 2
(an outlier lap). Driver 1's lap 6 is the fastest lap but deleted.
"""
import pandas as pd

LAP_ONE_START = 600.0  # session seconds

LAP_TIMES = {
    "1": [95.0, 90.0, 90.5, 110.0, 112.0, 89.0],
    "16": [95.5, 120.0, 90.8, 110.2, 112.3, 90.9],
    "44": [96.0, 91.0, 99.0, 115.0, 112.1, 91.5],
}
START_OFFSETS = {"1": 0.0, "16": 0.4, "44": 0.9}

SC_START = 900.0   # during lap 4 of every driver
SC_END = 1100.0    # during lap 6 of every driver


def make_laps():
    rows = []
    for driver_no, times in LAP_TIMES.items():
        start = LAP_ONE_START + START_OFFSETS[driver_no]
        for i, lap_time in enumerate(times):
            lap_no = i + 1
            end = start + lap_time
            changes = sorted({s for t, s in [(SC_START, "4"), (SC_END, "1")] if start < t < end})
            rows.append({
                "SessionKey": 9999,
                "DriverNo": driver_no,
                "LapNo": lap_no,
                "LapTime": pd.Timedelta(seconds=lap_time),
                "Position": {"1": 1, "16": 2, "44": 3}[driver_no],
                "NoPits": 1 if (driver_no == "44" and lap_no >= 4) else 0,
                "PitIn": pd.Timedelta(seconds=end - 1) if (driver_no == "44" and lap_no == 3) else None,
                "PitOut": pd.Timedelta(seconds=start + 20) if (driver_no == "44" and lap_no == 4) else None,
                "Compound": ("HARD" if lap_no >= 4 else "MEDIUM") if driver_no == "44" else "MEDIUM",
                "TyreAge": (lap_no - 3 if lap_no >= 4 else lap_no + 3) if driver_no == "44" else lap_no,
                "Sector1_Time": pd.Timedelta(seconds=round(lap_time * 0.3, 3)),
                "Sector2_Time": pd.Timedelta(seconds=round(lap_time * 0.4, 3)),
                "Sector3_Time": pd.Timedelta(seconds=round(lap_time * 0.3, 3)),
                "LapStartTime": pd.Timedelta(seconds=start),
                # Like the silver laps table: status changes during the lap, "1" when none
                "TrackStatus": ",".join(changes) if changes else "1",
                "IsDeleted": driver_no == "1" and lap_no == 6,
            })
            start = end
    laps = pd.DataFrame(rows)
    # Driver 16 has a quick first sector on lap 3 (theoretical best differs from best lap)
    laps.loc[(laps.DriverNo == "16") & (laps.LapNo == 3), "Sector1_Time"] = pd.Timedelta(seconds=26.5)
    return laps


def make_track_status():
    """Bronze TrackStatus records (timestamps as livetiming strings)."""
    return pd.DataFrame({
        "timestamp": pd.to_timedelta([0.0, SC_START, SC_END], unit="s"),
        "Status": ["1", "4", "1"],
        "Message": ["AllClear", "SCDeployed", "AllClear"],
    })


def make_lap_one_telemetry():
    """Lap-1 telemetry: speed ramps linearly; distance integrates speed."""
    rows = []
    accel = {"1": 10.0, "16": 8.0, "44": 12.5}  # km/h per second after a reaction delay
    reaction = {"1": 0.2, "16": 0.3, "44": 0.25}
    grid_order = {"1": 1, "16": 2, "44": 3}
    for driver_no in ["1", "16", "44"]:
        distance = -8.0 * (grid_order[driver_no] - 1)
        prev_v = 0.0
        for k in range(0, 300):
            t = LAP_ONE_START + 0.25 * k
            v = max(0.0, (t - LAP_ONE_START - reaction[driver_no]) * accel[driver_no])
            v = min(v, 300.0)
            distance += (prev_v + v) / 2 / 3.6 * 0.25
            prev_v = v
            rows.append({
                "DriverNo": driver_no, "LapNo": 1.0, "timestamp": pd.Timedelta(seconds=t),
                "Speed": v, "Distance": distance, "Throttle": 100.0, "Brake": 0.0,
                "Position": float(grid_order[driver_no]), "tag": "car",
            })
    return pd.DataFrame(rows)


def make_lap_telemetry(driver_no, lap_no, t_start, samples):
    """One lap of telemetry from ``samples`` = list of (dt, speed, throttle, brake)."""
    rows, t, d = [], t_start, 0.0
    for dt, speed, throttle, brake in samples:
        rows.append({"DriverNo": driver_no, "LapNo": float(lap_no), "timestamp": pd.Timedelta(seconds=t),
                     "Speed": speed, "Throttle": throttle, "Brake": brake, "Distance": d})
        t += dt
        d += speed / 3.6 * dt
    return pd.DataFrame(rows)


class FakeDriver:
    def __init__(self, RacingNumber, Tla, FirstName, LastName, TeamName, TeamColour, FullName=None):
        self.RacingNumber = RacingNumber
        self.Tla = Tla
        self.FirstName = FirstName
        self.LastName = LastName
        self.FullName = FullName if FullName is not None else f"{FirstName} {LastName.upper()}"
        self.TeamName = TeamName
        self.TeamColour = TeamColour


def make_drivers():
    return {
        "1": FakeDriver("1", "VER", "Max", "Verstappen", "Red Bull Racing", "3671C6"),
        "16": FakeDriver("16", "LEC", "Charles", "Leclerc", "Ferrari", "E8002D"),
        "44": FakeDriver("44", "HAM", "Lewis", "Hamilton", "Mercedes", "#27F4D2"),
    }


def make_driver_info():
    from livef1.analysis import driver_info
    return driver_info(make_drivers())


def make_meeting_table():
    idx = pd.MultiIndex.from_tuples(
        [(2024, "Spa", "Practice 1"), (2024, "Spa", "Qualifying"), (2024, "Spa", "Race")],
        names=["season_year", "meeting_location", "session_type"],
    )
    return pd.DataFrame({
        "meeting_key": [1242] * 3,
        "meeting_name": ["Belgian Grand Prix"] * 3,
        "session_key": [9570, 9573, 9574],
        "session_name": ["Practice 1", "Qualifying", "Race"],
        "session_startDate": pd.to_datetime(["2024-07-26T13:30:00", "2024-07-27T16:00:00", "2024-07-28T15:00:00"]),
        "session_endDate": pd.to_datetime(["2024-07-26T14:30:00", "2024-07-27T17:00:00", "2024-07-28T17:00:00"]),
        "gmtoffset": ["02:00:00"] * 3,
    }, index=idx)
