"""Provisional raw inventory data contract.

The source schema has not yet been verified against the FreshRetailNet-50K
dataset. Type, nullability, date representation, and allowed-value metadata
therefore remain provisional and must not be used for implicit coercion.
"""

from collections.abc import Iterable

MODEL_COLUMNS = [
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id",
    "sale_amount",
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
    "stockout_label",
]
REQUIRED_COLUMNS = ["date", *MODEL_COLUMNS]
UNIQUE_KEY_COLUMNS = [
    "city_id",
    "store_id",
    "product_id",
    "date",
]


MODEL_INPUT_COLUMNS = list(MODEL_COLUMNS)
TARGET_COLUMN = "next_day_stockout_label"

PROVISIONAL_TYPE_CATEGORIES = {
    "date": "temporal",
    "city_id": "identifier/categorical",
    "store_id": "identifier/categorical",
    "management_group_id": "identifier/categorical",
    "first_category_id": "identifier/categorical",
    "second_category_id": "identifier/categorical",
    "third_category_id": "identifier/categorical",
    "product_id": "identifier/categorical",
    "sale_amount": "numeric",
    "discount": "numeric",
    "holiday_flag": "binary/indicator",
    "activity_flag": "binary/indicator",
    "precpt": "numeric",
    "avg_temperature": "numeric",
    "avg_humidity": "numeric",
    "avg_wind_level": "numeric",
    "stockout_label": "binary/indicator",
}

PROVISIONAL_NULLABILITY = {
    column: "unverified"
    for column in REQUIRED_COLUMNS
}

PROVISIONAL_ALLOWED_VALUES = {
    "holiday_flag": "binary values; exact representation unverified",
    "activity_flag": "binary values; exact representation unverified",
    "stockout_label": "binary values; exact representation unverified",
}

VALIDATION_RULES = (
    "required column presence",
    "expected data types after source confirmation",
    "nullability after source confirmation",
    "valid date representation after source confirmation",
    "binary values after source confirmation",
    "duplicate business-key detection",
)


def missing_required_columns(columns: Iterable[str]) -> list[str]:
    """Return contract columns absent from a DataFrame column collection."""
    available = set(columns)
    return [column for column in REQUIRED_COLUMNS if column not in available]


def validate_inventory_columns(columns: Iterable[str]) -> dict[str, object]:
    """Report raw inventory contract column presence without changing data."""
    missing_columns = missing_required_columns(columns)
    return {
        "is_valid": not missing_columns,
        "missing_columns": missing_columns,
        "required_columns": list(REQUIRED_COLUMNS),
        "model_input_columns": list(MODEL_INPUT_COLUMNS),
        "business_key_columns": list(UNIQUE_KEY_COLUMNS),
        "target_column": TARGET_COLUMN,
    }
