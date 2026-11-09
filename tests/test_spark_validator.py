import importlib

import pandas as pd
import pytest


spark_validator = importlib.import_module(
    "data_pipeline.validation.spark_validator"
)
validate_spark_dataframe = spark_validator.validate_spark_dataframe

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    DataFrame = None
    SparkSession = None


def test_module_imports_without_pyspark():
    assert spark_validator is not None
    assert callable(validate_spark_dataframe)


def test_internal_aggregation_aliases_are_unique():
    original_names = {
        "__spark_validator_row_count",
        "__spark_validator_null_count",
        "__spark_validator_null_count_1",
    }
    used_aliases = set(original_names)

    row_alias = spark_validator._unique_alias(
        "__spark_validator_row_count",
        used_aliases,
    )
    first_null_alias = spark_validator._unique_alias(
        "__spark_validator_null_count",
        used_aliases,
    )
    second_null_alias = spark_validator._unique_alias(
        "__spark_validator_null_count",
        used_aliases,
    )

    assert len({row_alias, first_null_alias, second_null_alias}) == 3
    assert not {row_alias, first_null_alias, second_null_alias} & original_names


def test_invalid_input_type_raises_type_error():
    if SparkSession is None:
        with pytest.raises(ImportError, match="PySpark is required"):
            validate_spark_dataframe(pd.DataFrame({"item": ["A"]}))
    else:
        with pytest.raises(TypeError, match="PySpark DataFrame"):
            validate_spark_dataframe(pd.DataFrame({"item": ["A"]}))


@pytest.fixture(scope="module")
def spark():
    if SparkSession is None:
        pytest.skip("PySpark is not installed")
    session = (
        SparkSession.builder.master("local[2]")
        .appName("spark-validator-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def make_dataframe(spark):
    return spark.createDataFrame(
        [
            ("2026-01-01", "A", "S1", "P1", 1),
            ("2026-01-02", "B", "S2", "P2", 2),
        ],
        ["date", "city_id", "store_id", "product_id", "quantity"],
    )


def test_valid_spark_dataframe(spark):
    report = validate_spark_dataframe(
        make_dataframe(spark),
        required_columns=["date", "city_id"],
        unique_key_columns=["city_id", "store_id", "product_id", "date"],
    )

    assert report == {
        "is_valid": True,
        "row_count": 2,
        "column_count": 5,
        "missing_columns": [],
        "missing_unique_key_columns": [],
        "null_values": {},
        "duplicate_records": 0,
        "duplicate_key_records": 0,
    }


def test_empty_spark_dataframe_is_invalid(spark):
    dataframe = spark.createDataFrame([], "item string")

    report = validate_spark_dataframe(dataframe)

    assert report["is_valid"] is False
    assert report["row_count"] == 0


def test_zero_column_dataframe_duplicate_count_is_safe(spark):
    dataframe = spark.range(3).select()

    report = validate_spark_dataframe(dataframe)

    assert report["row_count"] == 3
    assert report["column_count"] == 0
    assert report["duplicate_records"] == 2


def test_missing_required_columns(spark):
    report = validate_spark_dataframe(
        make_dataframe(spark), required_columns=["missing"]
    )

    assert report["is_valid"] is False
    assert report["missing_columns"] == ["missing"]


def test_missing_unique_key_columns(spark):
    report = validate_spark_dataframe(
        make_dataframe(spark), unique_key_columns=["shipment_id"]
    )

    assert report["is_valid"] is False
    assert report["missing_unique_key_columns"] == ["shipment_id"]
    assert report["duplicate_key_records"] == 0


def test_null_values(spark):
    dataframe = spark.createDataFrame(
        [("A", None), ("B", 2)], ["item", "quantity"]
    )

    report = validate_spark_dataframe(dataframe)

    assert report["is_valid"] is False
    assert report["null_values"] == {"quantity": 1}


def test_null_count_aliases_do_not_collide_with_columns(spark):
    dataframe = spark.createDataFrame(
        [(None, "ok")],
        ["__spark_validator_row_count", "__spark_validator_null_count"],
    )

    report = validate_spark_dataframe(dataframe)

    assert report["null_values"] == {
        "__spark_validator_row_count": 1,
    }


def test_duplicate_complete_records(spark):
    dataframe = spark.createDataFrame(
        [("A", 1), ("A", 1), ("A", 1), ("B", 2)], ["item", "quantity"]
    )

    report = validate_spark_dataframe(dataframe)

    assert report["is_valid"] is False
    assert report["duplicate_records"] == 2


def test_duplicate_business_keys(spark):
    dataframe = spark.createDataFrame(
        [("A", 1), ("A", 2), ("A", 3), ("A", 4), ("B", 5)], ["item", "quantity"]
    )

    report = validate_spark_dataframe(dataframe, unique_key_columns=["item"])

    assert report["is_valid"] is False
    assert report["duplicate_key_records"] == 3


def test_nan_float_value_is_reported_as_missing(spark):
    dataframe = spark.createDataFrame([(1.0,), (float("nan"),)], ["amount"])

    report = validate_spark_dataframe(dataframe)

    assert report["null_values"] == {"amount": 1}


def test_null_and_nan_float_values_are_counted_once(spark):
    dataframe = spark.createDataFrame(
        [(None,), (float("nan"),), (2.0,)], ["amount"]
    )

    report = validate_spark_dataframe(dataframe)

    assert report["null_values"] == {"amount": 2}


def test_literal_nan_string_is_not_missing(spark):
    dataframe = spark.createDataFrame([("NaN",)], ["value"])

    report = validate_spark_dataframe(dataframe)

    assert report["null_values"] == {}


def test_multiple_validation_failures(spark):
    dataframe = spark.createDataFrame(
        [("A", None), ("A", None)], ["item", "quantity"]
    )

    report = validate_spark_dataframe(
        dataframe,
        required_columns=["item", "missing"],
        unique_key_columns=["item", "missing_key"],
    )

    assert report["is_valid"] is False
    assert report["missing_columns"] == ["missing"]
    assert report["missing_unique_key_columns"] == ["missing_key"]
    assert report["null_values"] == {"quantity": 2}
    assert report["duplicate_records"] == 1
    assert report["duplicate_key_records"] == 0


def test_original_spark_dataframe_remains_unchanged(spark):
    dataframe = make_dataframe(spark)
    original_columns = dataframe.columns
    original_count = dataframe.count()

    validate_spark_dataframe(dataframe, required_columns=["date"])

    assert dataframe.columns == original_columns
    assert dataframe.count() == original_count
