import pandas as pd
import pytest

from data_pipeline.ingestion.file_loader import load_file


def test_loads_csv_without_changing_values(tmp_path):
    source = pd.DataFrame({"item": ["A", "B"], "quantity": [2, 3]})
    path = tmp_path / "items.csv"
    source.to_csv(path, index=False)

    loaded = load_file(path)

    pd.testing.assert_frame_equal(loaded, source)
    assert source.equals(pd.DataFrame({"item": ["A", "B"], "quantity": [2, 3]}))


def test_loads_json(tmp_path):
    source = pd.DataFrame({"item": ["A", "B"], "quantity": [2, 3]})
    json_path = tmp_path / "items.json"
    source.to_json(json_path, orient="records")

    loaded = load_file(str(json_path))

    pd.testing.assert_frame_equal(loaded, source)


def test_loads_parquet(tmp_path):
    source = pd.DataFrame({"item": ["A", "B"], "quantity": [2, 3]})
    parquet_path = tmp_path / "items.parquet"
    source.to_parquet(parquet_path, index=False)

    pd.testing.assert_frame_equal(load_file(parquet_path), source)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_file(tmp_path / "missing.csv")


def test_directory_instead_of_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="not a file"):
        load_file(tmp_path)


def test_unsupported_extension_raises(tmp_path):
    path = tmp_path / "items.txt"
    path.write_text("item\nA\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported"):
        load_file(path)


def test_zero_byte_file_raises(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Input file is empty"):
        load_file(path)


def test_header_only_csv_loads_as_empty_dataframe(tmp_path):
    path = tmp_path / "header_only.csv"
    path.write_text("item,quantity\n", encoding="utf-8")

    loaded = load_file(path)

    assert loaded.empty
    assert list(loaded.columns) == ["item", "quantity"]


def test_malformed_json_raises_chained_value_error(tmp_path):
    path = tmp_path / "malformed.json"
    path.write_text('{"item": "A"', encoding="utf-8")

    with pytest.raises(ValueError, match="Unable to read JSON file") as error:
        load_file(path)
    assert error.value.__cause__ is not None
