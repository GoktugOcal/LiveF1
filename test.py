import livef1

session = livef1.get_session(
    2025,
    "Spa",
    "Race"
)

session.generate()
# session.load_session_results()

print(session.sessionResults)