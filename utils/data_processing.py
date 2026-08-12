"""CSV validation and normalization for transaction data."""
from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import pandas as pd

REQUIRED_COLUMNS = {"ticker", "date", "transaction_type", "quantity", "price"}


class TransactionValidationError(ValueError):
    """Raised when uploaded transaction history is invalid."""


def validate_transactions(source: str | BytesIO | BinaryIO | pd.DataFrame) -> pd.DataFrame:
    """Load, normalize, and validate transactions including chronological oversells."""
    try:
        frame = source.copy() if isinstance(source, pd.DataFrame) else pd.read_csv(source)
    except Exception as exc:
        raise TransactionValidationError("Unable to read the CSV. Please upload a valid CSV file.") from exc
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise TransactionValidationError(f"Missing required column(s): {', '.join(sorted(missing))}.")
    frame = frame.loc[:, ["ticker", "date", "transaction_type", "quantity", "price"]].copy()
    frame["ticker"] = frame["ticker"].astype("string").str.strip().str.upper()
    if frame["ticker"].isna().any() or (frame["ticker"] == "").any():
        raise TransactionValidationError("Ticker cannot be empty.")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce", format="mixed")
    if frame["date"].isna().any():
        bad = frame.index[frame["date"].isna()][0] + 1
        raise TransactionValidationError(f"Invalid date in row {bad}.")
    frame["transaction_type"] = frame["transaction_type"].astype("string").str.strip().str.title()
    invalid_types = ~frame["transaction_type"].isin(["Buy", "Sell"])
    if invalid_types.any():
        raise TransactionValidationError("Transaction type must be either Buy or Sell.")
    for column in ("quantity", "price"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any() or (frame[column] <= 0).any():
            raise TransactionValidationError(f"{column.title()} must be numeric and greater than zero.")
    # Stable ordering preserves CSV order for transactions entered on the same day.
    frame["_source_order"] = range(len(frame))
    frame = frame.sort_values(["date", "_source_order"], kind="stable").drop(columns="_source_order").reset_index(drop=True)
    available: dict[str, float] = {}
    for row in frame.itertuples(index=False):
        held = available.get(row.ticker, 0.0)
        if row.transaction_type == "Sell" and row.quantity > held + 1e-10:
            raise TransactionValidationError(
                f"Invalid transaction on {row.date.date()}: attempted to sell {row.quantity:g} "
                f"{row.ticker} shares, but only {held:g} were available."
            )
        available[row.ticker] = held + row.quantity if row.transaction_type == "Buy" else held - row.quantity
    return frame


def sample_csv_bytes() -> bytes:
    """Return a small valid example suitable for download."""
    return b"ticker,date,transaction_type,quantity,price\nAAPL,2024-01-10,Buy,10,185.20\nMSFT,2024-02-15,Buy,5,402.10\nAAPL,2024-06-01,Sell,3,195.50\n"
