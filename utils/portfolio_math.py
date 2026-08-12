"""Deterministic FIFO accounting and portfolio analytics."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

import numpy as np
import pandas as pd


def fifo_match(transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Match sales to oldest lots and return remaining holdings and sale analysis."""
    lots: dict[str, deque[list[float]]] = defaultdict(deque)
    sales: list[dict] = []
    for row in transactions.sort_values("date", kind="stable").itertuples(index=False):
        if row.transaction_type == "Buy":
            lots[row.ticker].append([float(row.quantity), float(row.price), row.date])
            continue
        left, basis = float(row.quantity), 0.0
        while left > 1e-10:
            qty, cost, acquired = lots[row.ticker][0]
            used = min(left, qty)
            basis += used * cost
            qty -= used
            left -= used
            if qty <= 1e-10:
                lots[row.ticker].popleft()
            else:
                lots[row.ticker][0][0] = qty
        proceeds = float(row.quantity) * float(row.price)
        sales.append({"ticker": row.ticker, "date": row.date, "quantity": float(row.quantity), "sale_price": float(row.price), "proceeds": proceeds, "realized_cost_basis": basis, "realized_pl": proceeds - basis})
    holdings = []
    for ticker, ticker_lots in lots.items():
        qty = sum(lot[0] for lot in ticker_lots)
        cost = sum(lot[0] * lot[1] for lot in ticker_lots)
        if qty > 1e-10:
            holdings.append({"ticker": ticker, "quantity": qty, "cost_basis": cost, "avg_cost_basis": cost / qty})
    return pd.DataFrame(holdings, columns=["ticker", "quantity", "cost_basis", "avg_cost_basis"]), pd.DataFrame(sales, columns=["ticker", "date", "quantity", "sale_price", "proceeds", "realized_cost_basis", "realized_pl"])


def build_holdings_table(holdings: pd.DataFrame, quotes: pd.DataFrame) -> pd.DataFrame:
    """Join FIFO holdings with quotes and calculate current position measures."""
    if holdings.empty:
        return pd.DataFrame()
    table = holdings.merge(quotes, on="ticker", how="left")
    table["market_value"] = table["quantity"] * table["current_price"]
    table["unrealized_pl"] = table["market_value"] - table["cost_basis"]
    table["unrealized_pl_pct"] = np.where(table["cost_basis"] != 0, table["unrealized_pl"] / table["cost_basis"], np.nan)
    table["today_pl"] = table["quantity"] * (table["current_price"] - table["previous_close"])
    table["today_pct"] = np.where(table["previous_close"] != 0, table["current_price"] / table["previous_close"] - 1, np.nan)
    total = table["market_value"].sum(min_count=1)
    table["portfolio_weight"] = table["market_value"] / total if pd.notna(total) and total else np.nan
    return table.sort_values("market_value", ascending=False, na_position="last").reset_index(drop=True)


def concentration_metrics(table: pd.DataFrame) -> dict[str, float]:
    weights = table.get("portfolio_weight", pd.Series(dtype=float)).dropna()
    return {"largest_holding_pct": float(weights.max() if len(weights) else np.nan), "top_3_holding_pct": float(weights.nlargest(3).sum()), "hhi": float((weights ** 2).sum())}


def performance_summary(transactions: pd.DataFrame, sales: pd.DataFrame, holdings_table: pd.DataFrame) -> dict[str, float]:
    buys = transactions[transactions.transaction_type == "Buy"]
    sells = transactions[transactions.transaction_type == "Sell"]
    investment = float((buys.quantity * buys.price).sum())
    proceeds = float((sells.quantity * sells.price).sum())
    current = float(holdings_table.get("market_value", pd.Series(dtype=float)).sum())
    realized = float(sales.get("realized_pl", pd.Series(dtype=float)).sum())
    unrealized = float(holdings_table.get("unrealized_pl", pd.Series(dtype=float)).sum())
    economic = proceeds + current - investment
    return {"total_investment": investment, "total_sell_proceeds": proceeds, "current_value": current, "realized_pl": realized, "unrealized_pl": unrealized, "total_economic_pl": economic, "total_return_pct": economic / investment if investment else np.nan}


def calculate_xirr(transactions: pd.DataFrame, current_value: float, as_of: pd.Timestamp | None = None) -> float:
    """Return annual money-weighted return or NaN if no valid solution exists."""
    if transactions.empty:
        return np.nan
    as_of = pd.Timestamp.today().normalize() if as_of is None else pd.Timestamp(as_of).normalize()
    cashflows = [-(r.quantity * r.price) if r.transaction_type == "Buy" else r.quantity * r.price for r in transactions.itertuples(index=False)]
    dates = list(transactions.date)
    if current_value:
        cashflows.append(current_value); dates.append(as_of)
    if not any(v < 0 for v in cashflows) or not any(v > 0 for v in cashflows):
        return np.nan
    try:
        from pyxirr import xirr
        value = float(xirr(dates, cashflows))
        return value if np.isfinite(value) else np.nan
    except Exception:
        return np.nan


def quantities_over_time(transactions: pd.DataFrame, dates: Iterable[pd.Timestamp]) -> pd.DataFrame:
    """Reconstruct end-of-day quantities for each symbol across dates."""
    symbols = sorted(transactions.ticker.unique())
    result = pd.DataFrame(0.0, index=pd.DatetimeIndex(dates), columns=symbols)
    running = dict.fromkeys(symbols, 0.0)
    ordered = transactions.sort_values("date", kind="stable").reset_index(drop=True)
    transaction_index = 0
    for date in result.index:
        # Apply a weekend/holiday transaction at the next available market close.
        while transaction_index < len(ordered) and ordered.loc[transaction_index, "date"].normalize() <= pd.Timestamp(date).normalize():
            row = ordered.iloc[transaction_index]
            running[row.ticker] += row.quantity if row.transaction_type == "Buy" else -row.quantity
            transaction_index += 1
        result.loc[date] = pd.Series(running)
    return result


def risk_metrics(portfolio_values: pd.Series, benchmark_values: pd.Series | None = None) -> dict[str, float]:
    returns = portfolio_values.pct_change().dropna()
    output = {"annualized_volatility": np.nan, "max_drawdown": np.nan, "beta": np.nan}
    if len(returns) >= 2:
        output["annualized_volatility"] = float(returns.std(ddof=1) * np.sqrt(252))
        output["max_drawdown"] = float((portfolio_values / portfolio_values.cummax() - 1).min())
    if benchmark_values is not None:
        aligned = pd.concat([returns, benchmark_values.pct_change()], axis=1).dropna()
        if len(aligned) >= 2 and aligned.iloc[:, 1].var() > 0:
            output["beta"] = float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / aligned.iloc[:, 1].var())
    return output
