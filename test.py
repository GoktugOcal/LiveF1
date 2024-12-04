import livef1

session = livef1.get_meeting(season=2024, meeting_identifier="spa")

print(session.name)