import pandas as pd
import pytest

from data_pipeline.adapters.inventory_adapter import REQUIRED_COLUMNS
from data_pipeline.pipeline import run_pipeline
from data_pipeline.router import route_dataset


def make_inventory_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {column: [index + 1, index + 2] for index, column in enumerate(REQUIRED_COLUMNS)}
    )


def test_valid_inventory_pipeline_execution(tmp_path):
    source = make_inventory_dataframe()
    path = tmp_path / "inventory.csv"
    source.to_csv(path, index=False)

    result = run_pipeline(path, "inventory")

    pd.testing.assert_frame_equal(result, source[REQUIRED_COLUMNS])


def test_missing_file_is_propagated(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path / "missing.csv", "inventory")


def test_unsupported_dataset_type_raises_clear_error():
    with pytest.raises(ValueError, match="Unsupported dataset type"):
        route_dataset(make_inventory_dataframe(), "delivery")


def test_unsupported_dataset_type_is_rejected_before_file_loading(monkeypatch):
    def fail_if_loaded(_file_path):
        raise AssertionError("file should not be loaded")

    monkeypatch.setattr("data_pipeline.pipeline.load_file", fail_if_loaded)

    with pytest.raises(ValueError, match="Unsupported dataset type"):
        run_pipeline("inventory.csv", "delivery")


def test_missing_required_columns_fail_validation(tmp_path):
    source = make_inventory_dataframe().drop(columns=["product_id"])
    path = tmp_path / "inventory.csv"
    source.to_csv(path, index=False)

    with pytest.raises(ValueError, match="Missing required columns") as error:
        run_pipeline(path, "inventory")

    assert "product_id" in str(error.value)


def test_null_required_values_report_validation_findings(tmp_path):
    source = make_inventory_dataframe()
    source.loc[1, "sale_amount"] = None
    path = tmp_path / "inventory.csv"
    source.to_csv(path, index=False)

    with pytest.raises(ValueError, match="Data validation failed") as error:
        run_pipeline(path, "inventory")

    assert "null_values" in str(error.value)
    assert "sale_amount" in str(error.value)


def test_duplicate_business_keys_report_validation_findings(tmp_path):
    source = make_inventory_dataframe()
    source.loc[1, ["city_id", "store_id", "product_id", "date"]] = (
        source.loc[0, ["city_id", "store_id", "product_id", "date"]]
    )
    path = tmp_path / "inventory.csv"
    source.to_csv(path, index=False)

    with pytest.raises(ValueError, match="Data validation failed") as error:
        run_pipeline(path, "inventory")

    assert "duplicate_key_records" in str(error.value)


def test_irrelevant_null_columns_are_removed_before_validation(tmp_path):
    source = make_inventory_dataframe()
    source["irrelevant_column"] = None
    path = tmp_path / "inventory.csv"
    source.to_csv(path, index=False)

    result = run_pipeline(path, "inventory")

    assert "irrelevant_column" not in result.columns


def test_existing_router_does_not_modify_input():
    source = make_inventory_dataframe()
    original = source.copy(deep=True)

    result = route_dataset(source, "inventory")
    result.loc[0, "sale_amount"] = 999

    pd.testing.assert_frame_equal(source, original)


def test_pipeline_does_not_modify_original_input_dataframe(monkeypatch):
    source = make_inventory_dataframe()
    original = source.copy(deep=True)

    monkeypatch.setattr("data_pipeline.pipeline.load_file", lambda _path: source)

    result = run_pipeline("inventory.csv", "inventory")
    result.loc[0, "sale_amount"] = 999

    pd.testing.assert_frame_equal(source, original)
