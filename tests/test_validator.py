import pytest
import pandas as pd

from data_pipeline.validation.validator import validate_dataframe


def test_valid_dataframe_returns_valid_report():
    dataframe = pd.DataFrame({"item": ["A", "B"], "quantity": [2, 3]})

    report = validate_dataframe(dataframe, required_columns=["item", "quantity"])

    assert report == {
        "is_valid": True,
        "row_count": 2,
        "column_count": 2,
        "missing_columns": [],
        "missing_unique_key_columns": [],
        "null_values": {},
        "duplicate_records": 0,
        "duplicate_key_records": 0,
    }


def test_report_identifies_missing_columns_nulls_and_duplicates():
    dataframe = pd.DataFrame(
        {"item": ["A", "A", None], "quantity": [2, 2, 4]}
    )
    original = dataframe.copy(deep=True)

    report = validate_dataframe(dataframe, required_columns=["item", "quantity", "date"])

    assert report["is_valid"] is False
    assert report["missing_columns"] == ["date"]
    assert report["missing_unique_key_columns"] == []
    assert report["null_values"] == {"item": 1}
    assert report["duplicate_records"] == 1
    assert report["duplicate_key_records"] == 0
    pd.testing.assert_frame_equal(dataframe, original)


def test_empty_dataframe_is_invalid():
    report = validate_dataframe(pd.DataFrame(columns=["item"]))

    assert report["is_valid"] is False
    assert report["row_count"] == 0


def test_non_dataframe_input_raises_type_error():
    with pytest.raises(TypeError, match="Pandas DataFrame"):
        validate_dataframe([{"item": "A"}])


def test_duplicate_business_keys_are_reported_separately():
    dataframe = pd.DataFrame(
        {"item": ["A", "A", "B"], "quantity": [2, 3, 4]}
    )

    report = validate_dataframe(dataframe, unique_key_columns=["item"])

    assert report["is_valid"] is False
    assert report["duplicate_records"] == 0
    assert report["duplicate_key_records"] == 1


def test_missing_unique_key_columns_are_reported_without_crashing():
    dataframe = pd.DataFrame({"item": ["A"]})

    report = validate_dataframe(dataframe, unique_key_columns=["shipment_id"])

    assert report["is_valid"] is False
    assert report["missing_unique_key_columns"] == ["shipment_id"]
    assert report["duplicate_key_records"] == 0
