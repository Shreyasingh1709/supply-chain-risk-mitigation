"""Spark-based file ingestion utilities."""

import os
from pathlib import Path
from typing import Any


def load_spark_file(
    spark: Any,
    file_path: str | Path,
    file_format: str,
) -> Any:
    """Load a CSV, JSON, or Parquet file with an existing SparkSession.

    Spark performs path validation and raises its native read exceptions. This
    keeps the function compatible with both local paths and cloud filesystem
    paths such as Databricks File System locations.
    """
    try:
        from pyspark.sql import SparkSession
    except ImportError:
        SparkSession = None

    if SparkSession is not None:
        valid_spark = isinstance(spark, SparkSession)
    else:
        valid_spark = spark is not None and hasattr(spark, "read")
    if not valid_spark:
        raise TypeError("spark must be an existing SparkSession")
    if not isinstance(file_path, (str, os.PathLike)):
        raise TypeError("file_path must be a string or path-like value")

    path = os.fspath(file_path)
    if not path.strip():
        raise ValueError("file_path must not be empty")
    if not isinstance(file_format, str):
        raise TypeError("file_format must be a string")

    normalized_format = file_format.strip().lower().lstrip(".")
    if normalized_format not in {"csv", "json", "parquet"}:
        raise ValueError(f"Unsupported Spark file format: {file_format!r}")

    if normalized_format == "csv":
        return spark.read.csv(path, header=True, inferSchema=True)
    if normalized_format == "json":
        return spark.read.json(path)
    return spark.read.parquet(path)
