"""
DataFrame backends of a session's data lake.

The backend decides the format of every table a session holds, from the bronze
tables built out of the parsed livetiming records to the silver and gold tables
built on top of them. Nothing is converted between backends. It is set with
``livef1.configure(dataframe_backend=...)``:

- ``"pandas"`` (default): all tables are ``pandas.DataFrame``.
- ``"polars"``: all tables are ``polars.DataFrame``; bronze tables are built by
  :mod:`livef1.data_processing.bronze_polars` and the default silver tables by
  :mod:`livef1.data_processing.silver_functions_polars`.
  Requires the optional dependency: ``pip install livef1[polars]``.

Polars is imported only when the polars backend is used.
"""
import importlib

from ..config import _settings

DATAFRAME_BACKENDS = ("pandas", "polars")
DEFAULT_DATAFRAME_BACKEND = "pandas"

_SILVER_FUNCTION_MODULES = {
    "pandas": "livef1.data_processing.silver_functions",
    "polars": "livef1.data_processing.silver_functions_polars",
}


def configured_backend():
    """The backend set with ``livef1.configure(dataframe_backend=...)``, else ``"pandas"``."""
    return _settings.get("dataframe_backend", DEFAULT_DATAFRAME_BACKEND)


def validate_backend(backend):
    """
    Return the normalized backend name.

    Raises
    ------
    ValueError
        If the backend is not one of :data:`DATAFRAME_BACKENDS`.
    ImportError
        If the polars backend is selected but polars is not installed.
    """
    backend = str(backend).lower()
    if backend not in DATAFRAME_BACKENDS:
        raise ValueError(
            f"Unknown dataframe backend '{backend}'. Available backends: {', '.join(DATAFRAME_BACKENDS)}."
        )
    if backend == "polars":
        try:
            import polars  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "The 'polars' dataframe backend requires polars. Install it with: pip install livef1[polars]"
            ) from e
    return backend


def get_silver_functions(backend):
    """Module holding the default silver table functions of a backend."""
    return importlib.import_module(_SILVER_FUNCTION_MODULES[validate_backend(backend)])


def check_backend_frame(df, backend, table_name):
    """
    Raise a ``TypeError`` if a table function returned a DataFrame of the other backend.

    Tables are never converted between pandas and polars: all tables of a session
    use the session's backend.
    """
    module = type(df).__module__.split(".")[0]
    if type(df).__name__ == "DataFrame" and module in DATAFRAME_BACKENDS and module != backend:
        raise TypeError(
            f"Table '{table_name}' returned a {module} DataFrame, but the session uses the '{backend}' "
            f"dataframe backend. Return a {backend} DataFrame."
        )
