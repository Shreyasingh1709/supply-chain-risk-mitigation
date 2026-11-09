"""Validation utilities for ingested tabular data."""

from collections.abc import Iterable

import pandas as pd


def validate_dataframe(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str] | None = None,
    unique_key_columns: Iterable[str] | None = None,
) -> dict[str, object]:
    """Return validation findings without changing or filtering the data.

    The report contains counts rather than invalid rows so callers can decide
    how to handle data quality issues without records being silently deleted.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a Pandas DataFrame")

    required = list(required_columns or [])
    unique_keys = list(unique_key_columns or [])
    missing_columns = [column for column in required if column not in dataframe.columns]
    missing_unique_key_columns = [
        column for column in unique_keys if column not in dataframe.columns
    ]
    null_values = dataframe.isna().sum()
    null_counts = {
        str(column): int(count)
        for column, count in null_values.items()
        if count > 0
    }
    duplicate_count = int(dataframe.duplicated().sum())
    duplicate_key_count = (
        int(dataframe.duplicated(subset=unique_keys).sum())
        if unique_keys and not missing_unique_key_columns
        else 0
    )

    return {
        "is_valid": (
            not dataframe.empty
            and not missing_columns
            and not missing_unique_key_columns
            and not null_counts
            and duplicate_count == 0
            and duplicate_key_count == 0
        ),
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "missing_columns": missing_columns,
        "missing_unique_key_columns": missing_unique_key_columns,
        "null_values": null_counts,
        "duplicate_records": duplicate_count,
        "duplicate_key_records": duplicate_key_count,
    }
