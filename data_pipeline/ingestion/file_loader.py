"""Local tabular file loading utilities."""

from pathlib import Path

import pandas as pd


def load_file(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV, JSON, or Parquet file without modifying its contents.

    Args:
        file_path: Path to the input file.

    Raises:
        FileNotFoundError: If the path does not exist or is not a file.
        ValueError: If the format is unsupported, the file is empty, or it
            cannot be parsed.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Input path is not a file: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".csv", ".json", ".parquet"}:
        raise ValueError(f"Unsupported file format: {suffix or '<none>'}")

    if path.stat().st_size == 0:
        raise ValueError(f"Input file is empty: {path}")

    loader = {
        ".csv": pd.read_csv,
        ".json": pd.read_json,
        ".parquet": pd.read_parquet,
    }[suffix]

    try:
        return loader(path)
    except (
        OSError,
        UnicodeError,
        TypeError,
        ValueError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ) as error:
        raise ValueError(f"Unable to read {suffix[1:].upper()} file: {path}") from error
