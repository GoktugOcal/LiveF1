:layout: landing
:description: LiveF1 is a powerful toolkit for accessing and analyzing Formula 1 data

LiveF1
=========================================================

.. rst-class:: lead

   LiveF1 is a powerful toolkit for accessing and analyzing Formula 1 data in real time or from historical archives, designed for developers, analysts, and fans building applications around F1 insights.

.. container:: buttons

    `Docs <getting_started/index.html>`_
    `GitHub <https://github.com/goktugocal/LiveF1>`_

.. grid:: 3
    :gutter: 2
    :padding: 0
    :class-row: surface

    .. grid-item-card:: :octicon:`desktop-download` How to install?
      :link: getting_started/installation.html

      Before starting analysis, follow our simple guide to install the library in Python.

    .. grid-item-card:: :octicon:`zap` What can I do with LiveF1?
      :link: user_guide/index.html

      Follow the user guide step by step to understand the origins of the F1's Livetiming data and start using LiveF1, with various ways that fits your needs.

    .. grid-item-card:: :octicon:`light-bulb` Beautiful Examples
      :link: examples/index.html

      Look at the examples to see the capabilities of LiveF1 and get insights. Also you can prepare and send your examples to us.



How to Contribute
-----------------
LiveF1 is an open-source project! Contributions are welcome to enhance its functionality. Check the :doc:`developer_notes/index` to get started with contributing, reporting issues, or suggesting features.



----

.. toctree::
   :maxdepth: 1
   :caption: Power of F1 data
   :hidden:

   getting_started/index
   getting_started/installation
   getting_started/quick_start
   getting_start/features



.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   user_guide/index
   user_guide/f1_data
   user_guide/data_topics
   user_guide/medallion_architecture
   user_guide/data_objects
   user_guide/accessing_data
   .. user_guide/informative_data
   .. user_guide/telemetry_data
   .. user_guide/working_with_realtime_client
   .. user_guide/visualization


   .. ./index
   .. getting_started/index
   .. features/index
   .. developer_notes/index
   .. additional_resources/index

.. toctree::
   :maxdepth: 1
   :caption: Working with data
   :hidden:

   working_with_data/historical_data
   working_with_data/realtime_data

.. toctree::
   :maxdepth: 1
   :caption: Reference
   :hidden:

   api_reference/index