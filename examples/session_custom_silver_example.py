"""
Example: Session with a custom silver table (ValidLaps).
Run after installing livef1: pip install livef1
"""
import livef1

session = livef1.get_session(2025, "Las Vegas GP", "Race")

@session.create_silver_table(
    table_name="ValidLaps",
    source_tables=["laps"],
    include_session=False
)
def valid_laps(laps):
    return laps  # Replace with your custom logic

session.generate()

print(session.ValidLaps)
