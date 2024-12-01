import livef1

# df = livef1.get_session(
#     2024,
#     "Monza",
#     "Race"
# )

# df = livef1.get_meeting(
#     2024,
#     "Monza"
# )

session = livef1.get_session(2023, "emilian", "Race")
print(session.meeting.name, session.name)