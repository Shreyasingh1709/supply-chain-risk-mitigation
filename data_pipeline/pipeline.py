"""Common local data ingestion, validation, and routing pipeline."""

from pathlib import Path

import pandas as pd

from data_pipeline.adapters.inventory_adapter import (
    REQUIRED_COLUMNS,
    UNIQUE_KEY_COLUMNS,
)
from data_pipeline.ingestion.file_loader import load_file
from data_pipeline.router import route_dataset
from data_pipeline.validation.validator import validate_dataframe


def run_pipeline(file_path: str | Path, dataset_type: str) -> pd.DataFrame:
    """Load, validate, and route a dataset using its explicit type."""
    if dataset_type != "inventory":
        raise ValueError(f"Unsupported dataset type: {dataset_type!r}")

    dataframe = load_file(file_path)
    adapted_dataframe = route_dataset(dataframe, dataset_type)
    report = validate_dataframe(
        adapted_dataframe,
        required_columns=REQUIRED_COLUMNS,
        unique_key_columns=UNIQUE_KEY_COLUMNS,
    )

    if not report["is_valid"]:
        raise ValueError(f"Data validation failed: {report}")

    return adapted_dataframe
