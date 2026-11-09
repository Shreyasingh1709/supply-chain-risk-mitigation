from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.ingestion.spark_loader import load_spark_file


try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    DataFrame = None
    SparkSession = None


class FakeReader:
    def csv(self, path, **options):
        return ("csv", path, options)

    def json(self, path):
        return ("json", path)

    def parquet(self, path):
        return ("parquet", path)


class FakeSpark:
    read = FakeReader()


def _spark_for_argument_tests():
    if SparkSession is None:
        return FakeSpark(), False
    return (
        SparkSession.builder.master("local[1]")
        .appName("spark-loader-argument-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate(),
        True,
    )


def test_unsupported_format_raises():
    spark, stop_spark = _spark_for_argument_tests()
    try:
        with pytest.raises(ValueError, match="Unsupported Spark file format"):
            load_spark_file(spark, "data.txt", "xml")
    finally:
        if stop_spark:
            spark.stop()


def test_invalid_arguments_raise():
    spark, stop_spark = _spark_for_argument_tests()
    try:
        with pytest.raises(TypeError, match="existing SparkSession"):
            load_spark_file(None, "data.csv", "csv")
        with pytest.raises(ValueError, match="must not be empty"):
            load_spark_file(spark, "   ", "csv")
        with pytest.raises(TypeError, match="file_path"):
            load_spark_file(spark, 42, "csv")
        with pytest.raises(ValueError, match="must not be empty"):
            load_spark_file(spark, "", "csv")
        with pytest.raises(TypeError, match="file_format"):
            load_spark_file(spark, "data.csv", None)
    finally:
        if stop_spark:
            spark.stop()


def test_fake_reader_dispatches_supported_formats():
    if SparkSession is not None:
        pytest.skip("FakeSpark is only used when PySpark is unavailable")
    spark = FakeSpark()

    assert load_spark_file(spark, Path("data.csv"), "CSV") == (
        "csv",
        "data.csv",
        {"header": True, "inferSchema": True},
    )
    assert load_spark_file(spark, "data.json", "json") == ("json", "data.json")
    assert load_spark_file(spark, "data.parquet", ".parquet") == (
        "parquet",
        "data.parquet",
    )


def test_fake_spark_is_rejected_when_pyspark_is_installed():
    if SparkSession is None:
        pytest.skip("PySpark is not installed")
    with pytest.raises(TypeError, match="existing SparkSession"):
        load_spark_file(FakeSpark(), "data.csv", "csv")


@pytest.fixture(scope="module")
def spark():
    if SparkSession is None:
        pytest.skip("PySpark is not installed")
    session = (
        SparkSession.builder.master("local[2]")
        .appName("spark-loader-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_loads_csv(spark, tmp_path):
    path = tmp_path / "items.csv"
    path.write_text("item,quantity\nA,2\nB,3\n", encoding="utf-8")

    loaded = load_spark_file(spark, path, "csv")

    assert isinstance(loaded, DataFrame)
    assert loaded.count() == 2
    assert loaded.columns == ["item", "quantity"]


def test_loads_json(spark, tmp_path):
    path = tmp_path / "items.json"
    path.write_text('{"item":"A","quantity":2}\n', encoding="utf-8")

    loaded = load_spark_file(spark, path, "json")

    assert isinstance(loaded, DataFrame)
    assert loaded.count() == 1


def test_loads_parquet(spark, tmp_path):
    path = tmp_path / "items.parquet"
    pd.DataFrame({"item": ["A"], "quantity": [2]}).to_parquet(path, index=False)

    loaded = load_spark_file(spark, path, "parquet")

    assert isinstance(loaded, DataFrame)
    assert loaded.count() == 1
