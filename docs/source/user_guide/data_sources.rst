.. _data_sources:

Data sources: Livetiming and Jolpica
====================================

LiveF1 combines two independent backends: **Formula 1 Livetiming** (official timing HTTP archives and live feeds) and the **Jolpica F1 API** (community REST data in the Ergast tradition). Each covers different shapes of Formula 1 data; the library merges them so seasons, meetings, and sessions stay usable when either source is incomplete.

.. seealso::

   Livetiming URL layout and topic indexes are documented under :ref:`f1-livetiming-data`.

Formula 1 Livetiming
--------------------

Livetiming exposes a hierarchy of **static JSON** under ``https://livetiming.formula1.com/static/`` (season index, meeting and session paths, per-session ``Index.json`` listing **Feeds** / topics). LiveF1 uses this tree to **discover** meetings and sessions, to know which **topics** exist for a session, and to **download** archived high-frequency data (timing, car telemetry, position, weather, and related streams) for analysis and the medallion pipeline.

Jolpica F1 API
--------------

`Jolpica F1`_ is an open-source, community-maintained project that provides a **JSON** HTTP API in the spirit of the former **Ergast** Formula 1 API. It is widely used as an Ergast-style source for championship-oriented data. The public service serves Ergast-compatible JSON (for example at ``https://api.jolpi.ca/ergast/f1/``); see the upstream repository for the canonical base URL, schema notes, and operational policies.

**What Jolpica provides:** seasons, race calendar, circuits, drivers, constructors, race results, qualifying, standings, lap and pit-stop style resources, and related **structured** tables. These are **REST resources** and aggregate rows—not the same as Livetiming’s **per-session topic streams** and compressed archives.

**Further reading (upstream):**

- `Jolpica F1`_ — project home
- `Rate limits`_ — request etiquette for ``api.jolpi.ca``
- `Differences vs Ergast`_ — migration notes from legacy Ergast behavior

.. _Jolpica F1: https://github.com/jolpica/jolpica-f1
.. _Rate limits: https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md
.. _Differences vs Ergast: https://github.com/jolpica/jolpica-f1/blob/main/docs/ergast_differences.md

Why LiveF1 uses both
--------------------

**Livetiming** is the right source when you need **session-level** archives and live topics: ``Session.get_data()``, lake generation, and medallion **silver/gold** tables assume Livetiming-backed material exists for that session. Models expose ``is_livetiming_available`` when the session can be tied to that backend.

**Jolpica** complements Livetiming by supplying a stable **calendar and registry**: race rounds, circuit and URL fields, driver and constructor lists, and championship standings. LiveF1 **merges** Livetiming meetings with Jolpica races so the season view stays coherent—**filling** gaps when one side is missing an event and **enriching** rows that appear in both (for example attaching round numbers and circuit details from Jolpica). Jolpica-only rounds may get **synthetic** session keys derived from the merge logic so the object model can still list practice, qualifying, sprint, and race slots. Lazy-loaded standings and similar features are gated by ``is_jolpica_available``.

**Resilience:** Building a :class:`~livef1.models.season.Season` requires at least one backend to succeed for that year; the merged calendar is effectively the **union** of Livetiming meetings and Jolpica races, with rules implemented in ``merge_meetings`` and related helpers in ``livef1.adapters.functions``.

BaseF1: Jolpica client
----------------------

HTTP access to Jolpica inside LiveF1 is implemented with **`basef1`** (**BaseF1**), a separate synchronous Python client for the Jolpica / Ergast-MRD-style API: typed responses, pagination helpers, and a chainable query builder. LiveF1 depends on ``basef1`` and uses `BaseF1Client` from ``livef1.adapters.jolpicaf1_adapter``.

If you only need to **query Jolpica directly** (outside LiveF1’s ``Season`` / ``Meeting`` / ``Session`` model), use BaseF1:

- **PyPI:** `basef1 on PyPI <https://pypi.org/project/basef1/>`__
- **Source:** `GoktugOcal/BaseF1 <https://github.com/GoktugOcal/BaseF1>`__

Practical notes
---------------

- ``list_seasons()`` is driven by Jolpica (season list from the API).
- ``get_session`` triggers ``load_session_data`` when **either** ``is_livetiming_available`` **or** ``is_jolpica_available`` is true; **raw topic downloads** and ``generate()`` still depend on Livetiming archives where those topics exist. Jolpica-first or synthetic sessions may expose **limited** topic coverage compared with a fully Livetiming-backed session.
- When running bulk scrapes, **cache and space requests** appropriately; follow upstream `Rate limits`_ for ``api.jolpi.ca``.

.. admonition:: Disclaimer

   LiveF1 is an unofficial toolkit and is not affiliated with or endorsed by Formula 1, Liberty Media, Jolpica F1 operators, or legacy Ergast. Third-party endpoints, schemas, and rate limits may change without notice. Verify compliance with each provider’s terms and use respectful request volumes.
