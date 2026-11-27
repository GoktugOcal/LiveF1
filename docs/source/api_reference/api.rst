LiveF1 API - :mod:`livef1`
=================================

Configuration
-------------
.. automodule:: livef1.config
   :members: configure
   :undoc-members:

   .. rubric:: Functions
   .. autosummary::
      configure

Session Access
--------------
.. automodule:: livef1.api
   :undoc-members:
   :inherited-members:

   .. rubric:: Functions
   .. autosummary::
      get_season
      get_meeting
      get_session

Next and Previous Sessions
--------------------------
See :ref:`schedule` for a guide.

.. automodule:: livef1.schedule
   :members: next_session, previous_session, next_meeting, previous_meeting, ScheduledSession, ScheduledMeeting, SessionStatus

   .. rubric:: Functions
   .. autosummary::
      next_session
      previous_session
      next_meeting
      previous_meeting

.. .. automodule:: livef1.api
..    :members: download_data

.. .. automodule:: livef1.api
..    :members: get_season

.. .. automodule:: livef1.api
..    :members: get_meeting

.. .. automodule:: livef1.api
..    :members: get_session

.. note::

   The LiveF1 package provides access to Formula 1 timing data, but it is not an official Formula 1 API client. External endpoints, available topics, and data formats may change without notice.