import importlib

import pandas as pd
import pytest

from data_pipeline.adapters.inventory_adapter import REQUIRED_COLUMNS


spark_adapter = importlib.import_module(
    "data_pipeline.adapters.spark_inventory_adapter"
)
adapt_spark_inventory_dataframe = (
    spark_adapter.adapt_spark_inventory_dataframe
)

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    DataFrame = None
    SparkSession = None


def test_module_imports_without_pyspark():
    assert spark_adapter is not None
    assert callable(adapt_spark_inventory_dataframe)


def test_invalid_input_type_when_pyspark_unavailable():
    if SparkSession is not None:
        pytest.skip("PySpark is installed; use Spark DataFrame type test")

    with pytest.raises(ImportError, match="PySpark is required"):
        adapt_spark_inventory_dataframe(pd.DataFrame())


@pytest.fixture(scope="module")
def spark():
    if SparkSession is None:
        pytest.skip("PySpark is not installed")
    session = (
        SparkSession.builder.master("local[2]")
        .appName("spark-inventory-adapter-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def make_inventory_dataframe(spark):
    columns = [*REQUIRED_COLUMNS, "irrelevant_column", "next_day_stockout_label"]
    values = list(range(len(columns)))
    return spark.createDataFrame([values], columns)


def test_valid_spark_dataframe_returns_required_columns(spark):
    dataframe = make_inventory_dataframe(spark)

    adapted = adapt_spark_inventory_dataframe(dataframe)

    assert isinstance(adapted, DataFrame)
    assert adapted.columns == REQUIRED_COLUMNS


def test_output_columns_preserve_required_order(spark):
    dataframe = make_inventory_dataframe(spark).select(
        *reversed(make_inventory_dataframe(spark).columns)
    )

    adapted = adapt_spark_inventory_dataframe(dataframe)

    assert adapted.columns == REQUIRED_COLUMNS


def test_irrelevant_columns_are_removed(spark):
    adapted = adapt_spark_inventory_dataframe(make_inventory_dataframe(spark))

    assert "irrelevant_column" not in adapted.columns


def test_missing_required_columns_raise_value_error(spark):
    dataframe = make_inventory_dataframe(spark).drop("product_id")

    with pytest.raises(ValueError, match="Missing required columns") as error:
        adapt_spark_inventory_dataframe(dataframe)

    assert "product_id" in str(error.value)


def test_invalid_input_type_raises_type_error(spark):
    with pytest.raises(TypeError, match="PySpark DataFrame"):
        adapt_spark_inventory_dataframe(pd.DataFrame())


def test_original_dataframe_remains_unchanged(spark):
    dataframe = make_inventory_dataframe(spark)
    original_columns = dataframe.columns
    original_count = dataframe.count()

    adapted = adapt_spark_inventory_dataframe(dataframe)

    assert dataframe.columns == original_columns
    assert dataframe.count() == original_count
    assert "irrelevant_column" in dataframe.columns
    assert adapted.columns == REQUIRED_COLUMNS


def test_target_column_is_not_added_or_generated(spark):
    dataframe = make_inventory_dataframe(spark).drop(
        "next_day_stockout_label"
    )

    adapted = adapt_spark_inventory_dataframe(dataframe)

    assert "next_day_stockout_label" not in adapted.columns
