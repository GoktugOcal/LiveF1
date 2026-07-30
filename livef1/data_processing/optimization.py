from ..utils.constants import _DOWNCAST_MAP, _CATEGORICAL_COLUMNS

def downcast(df, extra_mapping : dict = None):
    """
    Downcast columns to reduce memory usage.
    """
    for col, dtype in _DOWNCAST_MAP.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    if extra_mapping:
        for col, dtype in extra_mapping.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
    return df

def categorize(df, extra_columns : list = None):
    """
    Categorize columns to reduce memory usage.
    """
    for col in _CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("category")
    if extra_columns:
        for col in extra_columns:
            if col in df.columns:
                df[col] = df[col].astype("category")
    return df