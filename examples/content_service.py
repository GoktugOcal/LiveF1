"""
A content service driven by the F1 calendar, built on next/previous session and meeting.

Every poll answers two questions and acts once per answer (``state.json`` remembers
what was already published, so restarts don't publish twice):

1. Is there a race in the coming week, and which day is it? -> daily content
2. Is the last session's data ready in live timing?          -> analysis content

Session data needs an F1 account with F1TV: put ``F1_USERNAME`` and ``F1_PASSWORD``
in the environment or a ``.env`` file. Without them the calendar still works, and
so does the status of the session live timing shows right now.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import livef1

TZ = ZoneInfo("Europe/Istanbul")
STATE = Path("state.json")
DAILY = {6: "week preview", 5: "track guide", 2: "practice day", 1: "qualifying day", 0: "race day"}


def once(key, publish):
    """Run ``publish`` unless ``key`` was published before; a failure is retried next poll."""
    done = json.loads(STATE.read_text()) if STATE.exists() else {}
    if key in done:
        return
    publish()
    done[key] = datetime.now(TZ).isoformat()
    STATE.write_text(json.dumps(done, indent=1))


def poll():
    # 1. race this week?
    meeting = livef1.next_meeting()
    if meeting and meeting.race:
        today = datetime.now(TZ).date()
        days_to_race = (meeting.race.start.astimezone(TZ).date() - today).days
        if days_to_race in DAILY:
            once(f"daily:{meeting.season}:{meeting.round}:{today}",
                 lambda: print(f"[{today:%A}] {meeting.name}: {DAILY[days_to_race]}"))

    # 2. data of the last session ready?
    session = livef1.previous_session()
    status = session.status() if session else None
    if status and status.is_data_available:
        def analyse():
            print(f"Data ready: {session.meeting} {session.name}")
            # full livef1 Session: session.load().generate(silver=True)
        once(f"data:{session.season}:{session.meeting}:{session.name}", analyse)


if __name__ == "__main__":
    while True:
        try:
            poll()
        except Exception as exc:
            print(f"Poll failed: {exc}")
        nxt = livef1.next_session()
        busy = nxt is not None and (nxt.is_live() or (nxt.start - datetime.now(TZ)).total_seconds() < 7200)
        time.sleep(60 if busy else 900)
