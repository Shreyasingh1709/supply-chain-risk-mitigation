import subprocess
import sys

import pandas as pd
import pytest

from data_pipeline.contracts.inventory_contract import (
    MODEL_COLUMNS,
    REQUIRED_COLUMNS,
    UNIQUE_KEY_COLUMNS,
)
from data_pipeline.contracts.inventory_contract import (
    MODEL_INPUT_COLUMNS,
    PROVISIONAL_ALLOWED_VALUES,
    PROVISIONAL_NULLABILITY,
    PROVISIONAL_TYPE_CATEGORIES,
    TARGET_COLUMN,
    VALIDATION_RULES,
    missing_required_columns,
    validate_inventory_columns,
)


def test_contract_preserves_existing_column_definitions():
    assert REQUIRED_COLUMNS == ["date", *MODEL_COLUMNS]
    assert MODEL_INPUT_COLUMNS == MODEL_COLUMNS
    assert UNIQUE_KEY_COLUMNS == [
        "city_id",
        "store_id",
        "product_id",
        "date",
    ]
    assert TARGET_COLUMN == "next_day_stockout_label"
    assert TARGET_COLUMN not in REQUIRED_COLUMNS


def test_contract_metadata_marks_unverified_details_provisional():
    assert set(PROVISIONAL_TYPE_CATEGORIES) == set(REQUIRED_COLUMNS)
    assert set(PROVISIONAL_NULLABILITY) == set(REQUIRED_COLUMNS)
    assert set(PROVISIONAL_NULLABILITY.values()) == {"unverified"}
    assert set(PROVISIONAL_ALLOWED_VALUES) == {
        "holiday_flag",
        "activity_flag",
        "stockout_label",
    }
    assert "expected data types after source confirmation" in VALIDATION_RULES


def test_missing_required_columns_are_reported_in_contract_order():
    columns = ["date", "city_id", "product_id"]

    assert missing_required_columns(columns) == [
        column for column in REQUIRED_COLUMNS if column not in columns
    ]

    report = validate_inventory_columns(columns)
    assert report["is_valid"] is False
    assert report["missing_columns"] == missing_required_columns(columns)


def test_additional_columns_are_allowed():
    columns = [*REQUIRED_COLUMNS, "irrelevant_column"]

    report = validate_inventory_columns(columns)

    assert report["is_valid"] is True
    assert report["missing_columns"] == []


def test_complete_columns_pass_without_modifying_input():
    dataframe = pd.DataFrame(columns=REQUIRED_COLUMNS)
    original_columns = dataframe.columns.tolist()

    report = validate_inventory_columns(dataframe.columns)

    assert report["is_valid"] is True
    assert dataframe.columns.tolist() == original_columns


def test_contract_module_imports_without_pyspark():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import data_pipeline.contracts.inventory_contract; "
                "print('pandas' in sys.modules, 'pyspark' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False False"


@pytest.mark.parametrize(
    "column",
    ["city_id", "store_id", "product_id", "date"],
)
def test_business_key_columns_are_required(column):
    assert column in UNIQUE_KEY_COLUMNS
