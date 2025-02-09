import livef1

livef1.set_log_level('INFO')

session = livef1.get_session(
   season=2024,
   meeting_identifier="Spa",
   session_identifier="Race"
   )

# session.generate()

# session.load_data("CarData.z", parallel=False)

data = session.get_data(["CarData.z", "Position.z", "SessionStatus"], parallel=True)

print(data)