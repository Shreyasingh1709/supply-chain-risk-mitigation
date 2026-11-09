import json

import pytest

from data_pipeline.adapters.inventory_adapter import REQUIRED_COLUMNS
from data_pipeline.spark_pipeline import run_spark_pipeline


try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    DataFrame = None
    SparkSession = None


class FakeSpark:
    read = object()


def test_unsupported_dataset_type_is_rejected_before_loading(monkeypatch):
    def fail_if_loaded(*args, **kwargs):
        raise AssertionError("file should not be loaded")

    monkeypatch.setattr("data_pipeline.spark_pipeline.load_spark_file", fail_if_loaded)

    with pytest.raises(ValueError, match="Unsupported dataset type"):
        run_spark_pipeline(None, "inventory.csv", "csv", "delivery")


def test_unsupported_file_format_is_rejected_without_spark():
    if SparkSession is not None:
        pytest.skip("This test uses the no-PySpark argument path")

    with pytest.raises(ValueError, match="Unsupported Spark file format"):
        run_spark_pipeline(FakeSpark(), "inventory.txt", "xml", "inventory")


@pytest.fixture(scope="module")
def spark():
    if SparkSession is None:
        pytest.skip("PySpark is not installed")
    session = (
        SparkSession.builder.master("local[2]")
        .appName("spark-pipeline-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def make_inventory_rows():
    return [
        "2026-01-01,1,10,100,1000,10000,100000,1000000,5.0,0.1,0,1,0.0,20.0,50.0,3.0,0",
        "2026-01-02,2,20,200,2000,20000,200000,2000000,6.0,0.2,1,0,1.0,21.0,51.0,4.0,1",
    ]


def write_inventory_csv(path, rows=None, extra_header=None):
    header = ",".join(REQUIRED_COLUMNS)
    if extra_header:
        header += f",{extra_header}"
    content = [header]
    for row in rows or make_inventory_rows():
        if extra_header:
            row += ","
        content.append(row)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def test_successful_csv_inventory_pipeline(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    write_inventory_csv(path)

    result = run_spark_pipeline(spark, path, "csv", "inventory")

    assert isinstance(result, DataFrame)
    assert result.columns == REQUIRED_COLUMNS
    assert result.count() == 2


def test_successful_json_inventory_pipeline(spark, tmp_path):
    path = tmp_path / "inventory.json"
    records = [
        dict(zip(REQUIRED_COLUMNS, [1] * len(REQUIRED_COLUMNS))),
        dict(zip(REQUIRED_COLUMNS, [2] * len(REQUIRED_COLUMNS))),
    ]
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    result = run_spark_pipeline(spark, path, "json", "inventory")

    assert result.columns == REQUIRED_COLUMNS
    assert result.count() == 2


def test_missing_required_columns_raise_value_error(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    missing_column_index = REQUIRED_COLUMNS.index("product_id")
    header = [
        column for index, column in enumerate(REQUIRED_COLUMNS)
        if index != missing_column_index
    ]
    values = make_inventory_rows()[0].split(",")
    values.pop(missing_column_index)
    path.write_text(
        ",".join(header) + "\n" + ",".join(values) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required columns") as error:
        run_spark_pipeline(spark, path, "csv", "inventory")

    assert "product_id" in str(error.value)


def test_null_values_raise_validation_error(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    rows = [make_inventory_rows()[0].replace(",5.0,", ",,")]
    write_inventory_csv(path, rows)

    with pytest.raises(ValueError, match="Spark data validation failed") as error:
        run_spark_pipeline(spark, path, "csv", "inventory")

    assert "sale_amount" in str(error.value)


def test_duplicate_business_keys_raise_validation_error(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    first = make_inventory_rows()[0]
    duplicate_key = first.replace(",5.0,", ",7.0,")
    write_inventory_csv(path, [first, duplicate_key])

    with pytest.raises(ValueError, match="Spark data validation failed") as error:
        run_spark_pipeline(spark, path, "csv", "inventory")

    assert "duplicate_key_records" in str(error.value)


def test_irrelevant_columns_are_removed_before_validation(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    write_inventory_csv(path, extra_header="irrelevant_column")

    result = run_spark_pipeline(spark, path, "csv", "inventory")

    assert result.columns == REQUIRED_COLUMNS
    assert "irrelevant_column" not in result.columns


def test_original_input_file_data_is_not_modified(spark, tmp_path):
    path = tmp_path / "inventory.csv"
    write_inventory_csv(path, extra_header="irrelevant_column")
    original = path.read_text(encoding="utf-8")

    result = run_spark_pipeline(spark, path, "csv", "inventory")

    assert path.read_text(encoding="utf-8") == original
    assert result.columns == REQUIRED_COLUMNS
