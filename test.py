import livef1

if __name__ == '__main__':
    session = livef1.get_session(
        season=2024,
        meeting_identifier="Spa",
        session_identifier="Race"
    )

    session.load_data("Position.z")