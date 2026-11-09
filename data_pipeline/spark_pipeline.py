"""Spark inventory ingestion, adaptation, and validation pipeline."""

from pathlib import Path
from typing import Any

from data_pipeline.adapters.inventory_adapter import (
    REQUIRED_COLUMNS,
    UNIQUE_KEY_COLUMNS,
)
from data_pipeline.adapters.spark_inventory_adapter import (
    adapt_spark_inventory_dataframe,
)
from data_pipeline.ingestion.spark_loader import load_spark_file
from data_pipeline.validation.spark_validator import validate_spark_dataframe


def run_spark_pipeline(
    spark: Any,
    file_path: str | Path,
    file_format: str,
    dataset_type: str,
) -> Any:
    """Load, adapt, validate, and return an inventory Spark DataFrame."""
    if dataset_type != "inventory":
        raise ValueError(f"Unsupported dataset type: {dataset_type!r}")

    dataframe = load_spark_file(spark, file_path, file_format)
    adapted_dataframe = adapt_spark_inventory_dataframe(dataframe)
    report = validate_spark_dataframe(
        adapted_dataframe,
        required_columns=REQUIRED_COLUMNS,
        unique_key_columns=UNIQUE_KEY_COLUMNS,
    )

    if not report["is_valid"]:
        raise ValueError(f"Spark data validation failed: {report}")

    return adapted_dataframe
