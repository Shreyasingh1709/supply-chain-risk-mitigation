"""Route validated datasets to their dataset-specific adapters."""

import pandas as pd

from data_pipeline.adapters.inventory_adapter import adapt_inventory_dataframe


def route_dataset(dataframe: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
    """Route a DataFrame using the explicitly supplied dataset type."""
    if dataset_type == "inventory":
        return adapt_inventory_dataframe(dataframe)

    raise ValueError(f"Unsupported dataset type: {dataset_type!r}")
