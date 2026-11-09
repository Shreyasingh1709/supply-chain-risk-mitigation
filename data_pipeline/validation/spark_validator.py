"""Validation utilities for Spark DataFrames."""

from collections.abc import Iterable
from typing import Any


def validate_spark_dataframe(
    dataframe: Any,
    required_columns: Iterable[str] | None = None,
    unique_key_columns: Iterable[str] | None = None,
) -> dict[str, object]:
    """Return validation findings for a Spark DataFrame."""
    try:
        from pyspark.sql import DataFrame
        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType, FloatType
    except ImportError as error:
        raise ImportError(
            "PySpark is required to validate a Spark DataFrame"
        ) from error

    if not isinstance(dataframe, DataFrame):
        raise TypeError("dataframe must be a PySpark DataFrame")

    required = list(required_columns or [])
    unique_keys = list(unique_key_columns or [])
    columns = dataframe.columns
    missing_columns = [column for column in required if column not in columns]
    missing_unique_key_columns = [
        column for column in unique_keys if column not in columns
    ]

    if columns:
        used_aliases = set(columns)
        row_count_alias = _unique_alias("__spark_validator_row_count", used_aliases)
        null_expressions = []
        null_aliases = {}
        for field in dataframe.schema.fields:
            missing = F.col(field.name).isNull()
            if isinstance(field.dataType, (FloatType, DoubleType)):
                missing = missing | F.isnan(F.col(field.name))
            null_alias = _unique_alias(
                "__spark_validator_null_count",
                used_aliases,
            )
            null_aliases[field.name] = null_alias
            null_expressions.append(
                F.sum(F.when(missing, 1).otherwise(0)).alias(null_alias)
            )
        aggregate_row = dataframe.agg(
            F.count(F.lit(1)).alias(row_count_alias),
            *null_expressions,
        ).first()
        row_count = int(aggregate_row[row_count_alias])
        null_counts = {
            column: int(aggregate_row[null_aliases[column]])
            for column in columns
            if aggregate_row[null_aliases[column]]
        }
    else:
        row_count = dataframe.count()
        null_counts = {}

    duplicate_count = _duplicate_count(dataframe, columns, row_count)
    duplicate_key_count = (
        _duplicate_count(dataframe, unique_keys, row_count)
        if unique_keys and not missing_unique_key_columns
        else 0
    )

    return {
        "is_valid": (
            row_count > 0
            and not missing_columns
            and not missing_unique_key_columns
            and not null_counts
            and duplicate_count == 0
            and duplicate_key_count == 0
        ),
        "row_count": row_count,
        "column_count": len(columns),
        "missing_columns": missing_columns,
        "missing_unique_key_columns": missing_unique_key_columns,
        "null_values": null_counts,
        "duplicate_records": duplicate_count,
        "duplicate_key_records": duplicate_key_count,
    }


def _duplicate_count(
    dataframe: Any, columns: list[str], row_count: int
) -> int:
    """Count duplicate rows beyond the first row in each group."""
    if not columns:
        return max(row_count - 1, 0)

    duplicate_groups = (
        dataframe.groupBy(*columns)
        .count()
        .where("count > 1")
        .selectExpr("coalesce(sum(count - 1), 0) AS duplicate_count")
        .first()
    )
    return int(duplicate_groups["duplicate_count"])


def _unique_alias(prefix: str, used_aliases: set[str]) -> str:
    """Return an internal alias that cannot collide with existing names."""
    alias = prefix
    suffix = 0
    while alias in used_aliases:
        suffix += 1
        alias = f"{prefix}_{suffix}"
    used_aliases.add(alias)
    return alias
