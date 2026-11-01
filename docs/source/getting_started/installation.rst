********************************
Installation
********************************

Install via pip
-------------------

The easiest way to install LiveF1 is through pip. Run the following command in your terminal:

.. code-block:: bash

   pip install livef1

Optional: Polars backend
------------------------

To build LiveF1 tables with `Polars <https://pola.rs>`_ instead of pandas, install the
``polars`` extra and select it with ``livef1.configure(dataframe_backend="polars")``
(see :ref:`dataframe_backend`):

.. code-block:: bash

   pip install "livef1[polars]"

Install from source
-------------------

If you want to install the latest development version or contribute to LiveF1, follow these steps:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/goktugocal/LiveF1.git

2. Navigate into the project directory:

   .. code-block:: bash

      cd LiveF1

3. Install dependencies and the package:

   .. code-block:: bash

      pip install -r requirements.txt
      pip install .

.. note::

   LiveF1 uses data feeds from external Formula 1 timing services. These data sources may be subject to change, service limitations, or terms of use outside the control of this library.