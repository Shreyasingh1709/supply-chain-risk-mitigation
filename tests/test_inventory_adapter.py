import pandas as pd
import pytest

from data_pipeline.adapters.inventory_adapter import (
    MODEL_COLUMNS,
    REQUIRED_COLUMNS,
    adapt_inventory_dataframe,
)


def make_inventory_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            column: [index + 1]
            for index, column in enumerate(REQUIRED_COLUMNS)
        }
    )


def test_valid_input_returns_required_columns_without_target_column():
    dataframe = make_inventory_dataframe()
    dataframe["next_day_stockout_label"] = 0

    adapted = adapt_inventory_dataframe(dataframe)

    assert list(adapted.columns) == REQUIRED_COLUMNS
    assert "next_day_stockout_label" not in adapted.columns
    pd.testing.assert_frame_equal(adapted, dataframe[REQUIRED_COLUMNS])


def test_missing_columns_raise_clear_error():
    dataframe = make_inventory_dataframe().drop(columns=["product_id", "date"])

    with pytest.raises(ValueError, match="Missing required columns"):
        adapt_inventory_dataframe(dataframe)

    with pytest.raises(ValueError) as error:
        adapt_inventory_dataframe(dataframe)
    assert "date" in str(error.value)
    assert "product_id" in str(error.value)


def test_output_columns_follow_exact_model_order():
    dataframe = make_inventory_dataframe()[list(reversed(REQUIRED_COLUMNS))]

    adapted = adapt_inventory_dataframe(dataframe)

    assert list(adapted.columns) == ["date", *MODEL_COLUMNS]


def test_original_dataframe_is_preserved():
    dataframe = make_inventory_dataframe()
    original = dataframe.copy(deep=True)

    adapted = adapt_inventory_dataframe(dataframe)
    adapted.loc[0, "sale_amount"] = 999

    pd.testing.assert_frame_equal(dataframe, original)
