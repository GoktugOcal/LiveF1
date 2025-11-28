import livef1
from livef1.utils.constants import TABLE_REQUIREMENTS, TABLE_GENERATION_FUNCTIONS
from livef1.data_processing.silver_functions import *

# meeting = livef1.get_meeting(2024, "Lusail")
# print(meeting)

session = livef1.get_session(
    2024,
    meeting_identifier = "Spa",
    session_identifier = "Race"
    )

# session.create_silver_table("laps", TABLE_REQUIREMENTS["laps"], include_session=True)(globals()[TABLE_GENERATION_FUNCTIONS["laps"]])

print(session.meeting.circuit)

# session = livef1.get_session(2024, "Sao Paulo", "Qualifying")
# session.generate()
# print(session.name)