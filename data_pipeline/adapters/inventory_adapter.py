"""Adapt inventory data to the date and inventory model input contract."""

import pandas as pd

from data_pipeline.contracts.inventory_contract import (
    MODEL_COLUMNS,
    REQUIRED_COLUMNS,
    UNIQUE_KEY_COLUMNS,
)


def adapt_inventory_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy containing date and inventory model columns in contract order."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a Pandas DataFrame")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return dataframe.loc[:, REQUIRED_COLUMNS].copy()
