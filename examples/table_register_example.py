"""
Example: Creating custom silver and gold tables with create_silver_table and create_gold_table.
Run after installing livef1: pip install livef1
"""
import livef1

session = livef1.get_session(
    2025,
    "British",
    "Qualifying"
)

@session.create_silver_table(
    table_name = "SectorDiff",
    source_tables = ["laps"],
    include_session = True
)
def sector_diff(session, laps):
    df = laps.groupby("DriverNo")[["Sector1_Time","Sector2_Time","Sector3_Time"]].min().reset_index()
    df["sector1_diff"] = (df["Sector1_Time"] - df["Sector1_Time"].min()).dt.total_seconds()
    df["sector2_diff"] = (df["Sector2_Time"] - df["Sector2_Time"].min()).dt.total_seconds()
    df["sector3_diff"] = (df["Sector3_Time"] - df["Sector3_Time"].min()).dt.total_seconds()
    df["DriverName"] = df["DriverNo"].map(lambda x: session.drivers[x].FullName)
    return df


@session.create_gold_table(
    table_name = "SectorLeaders",
    source_tables = ["SectorDiff"],
    include_session = True
)
def sector_leaders(session, SectorDiff):
    return SectorDiff.iloc[SectorDiff[["sector1_diff","sector2_diff","sector3_diff"]].idxmin().values]


session.generate(silver=True, gold=True)

print(session.SectorDiff.head().to_markdown())
print(session.SectorLeaders.head())
