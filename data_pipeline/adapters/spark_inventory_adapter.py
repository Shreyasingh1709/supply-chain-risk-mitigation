"""Adapt Spark inventory data to the inventory model input contract."""

from typing import Any

from data_pipeline.contracts.inventory_contract import REQUIRED_COLUMNS


def adapt_spark_inventory_dataframe(dataframe: Any) -> Any:
    """Return a Spark projection containing the required columns in order."""
    try:
        from pyspark.sql import DataFrame
    except ImportError as error:
        raise ImportError(
            "PySpark is required to adapt a Spark inventory DataFrame"
        ) from error

    if not isinstance(dataframe, DataFrame):
        raise TypeError("dataframe must be a PySpark DataFrame")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return dataframe.select(*REQUIRED_COLUMNS)
