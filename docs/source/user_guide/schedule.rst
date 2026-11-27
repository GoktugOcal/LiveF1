.. _schedule:

Next and previous sessions
==========================

Four functions find a session or meeting by time, without loading a season:

.. code-block:: python

    import livef1

    livef1.next_session()               # the session running, else the next to start
    livef1.next_session("Race")         # "Qualifying", "Sprint", "Sprint Qualifying", "Practice", ...
    livef1.previous_session()           # the last session that ended
    livef1.next_meeting()               # the meeting under way, else the next one
    livef1.previous_meeting()           # the last meeting that ended

"Next" means not ended yet and "previous" means ended, so together they cover
every moment: during a session, ``next_session()`` returns it and
``next_session().is_live()`` is true. Each function takes ``now=`` (a datetime,
pandas Timestamp or ISO string; naive values are UTC) and ``refresh=True`` to
skip the cache.

Sessions and meetings
---------------------

:class:`~livef1.schedule.ScheduledSession` has ``meeting``, ``name``, ``type``,
``round``, and ``start`` and ``end`` as aware UTC datetimes.
:class:`~livef1.schedule.ScheduledMeeting` has ``name``, ``round``,
``location``, ``country``, ``circuit``, its ``sessions`` in start order,
``race`` and ``session(name)``. Pre-season testing is a meeting without a race.

.. code-block:: python

    meeting = livef1.next_meeting()
    meeting.name, meeting.round, meeting.race.start
    [s.name for s in meeting.sessions]

    meeting.load()                       # the full livef1.Meeting
    livef1.previous_session().load()     # the full livef1.Session, ready for generate()

The calendar comes from Jolpica, which lists every session in advance and
needs no F1 account. Live timing lists a meeting only once its weekend has
begun; from then on, with an F1 account (see :ref:`authentication`), sessions
also have ``key``, ``meeting_key``, ``path`` and their exact ``end``, and
``listed`` is true. Before that, ``end`` is estimated from the session type
(``end_estimated``).

Session status
--------------

:meth:`~livef1.schedule.ScheduledSession.status` returns live timing's state of
the session as a :class:`~livef1.schedule.SessionStatus`, or ``None`` while
live timing has nothing for it:

.. code-block:: python

    status = livef1.previous_session().status()
    status.session_status        # 'Inactive', 'Started', 'Aborted', 'Finished', 'Finalised' or 'Ends'
    status.archive_status        # 'Generating' or 'Complete'
    status.is_live, status.is_finished, status.is_data_available

``is_data_available`` is true once the session is over and live timing has
finished writing its data, which is when ``load()`` and ``generate()`` get the
whole session. For the session live timing currently shows, the status comes
from the public ``static/SessionInfo.json`` and needs no F1 account; any other
session needs one.
