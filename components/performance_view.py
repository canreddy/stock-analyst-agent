"""Lifetime performance and benchmark analytics."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.market_data import get_price_history
from utils.portfolio_math import calculate_xirr, fifo_match, performance_summary, quantities_over_time, risk_metrics

def _money(v): return "N/A" if pd.isna(v) else f"${v:,.2f}"
def render(benchmark: str) -> None:
    tx=st.session_state.get("transactions"); table=st.session_state.get("holdings_table")
    if tx is None or table is None: st.info("Upload data and open Portfolio to load market data first."); return
    _,sales=fifo_match(tx); summary=performance_summary(tx,sales,table); xirr=calculate_xirr(tx,summary["current_value"])
    labels=["Total Investment","Total Sell Proceeds","Current Portfolio Value","Realized P/L","Unrealized P/L","Total Economic P/L","Simple Lifetime Return","XIRR"]
    values=[_money(summary[k]) for k in ["total_investment","total_sell_proceeds","current_value","realized_pl","unrealized_pl","total_economic_pl"]]+[f"{summary['total_return_pct']:.2%}" if pd.notna(summary['total_return_pct']) else "N/A",f"{xirr:.2%}" if pd.notna(xirr) else "N/A"]
    for i in range(0,8,4):
        for col,l,v in zip(st.columns(4),labels[i:i+4],values[i:i+4]): col.metric(l,v)
    st.caption("Simple lifetime return is Total Economic P/L ÷ Total Investment; it is not a money-weighted return.")
    symbols=tuple(tx.ticker.unique()); start=str(tx.date.min().date()); prices=get_price_history(symbols,start)
    if prices.empty: st.warning("Historical prices are currently unavailable."); return
    quantities=quantities_over_time(tx,prices.index); portfolio=(quantities.reindex(columns=prices.columns,fill_value=0)*prices).sum(axis=1)
    st.plotly_chart(px.line(portfolio,title="Portfolio value over time",labels={"value":"Value","index":"Date"}),use_container_width=True)
    bench=get_price_history((benchmark,),start)
    if not bench.empty and benchmark in bench:
        compare=pd.concat([portfolio.rename("Portfolio"),bench[benchmark].rename(benchmark)],axis=1).dropna()
        if not compare.empty:
            normalized=compare.div(compare.iloc[0]).mul(100); st.plotly_chart(px.line(normalized,title=f"Normalized comparison (start = 100): Portfolio vs {benchmark}"),use_container_width=True)
            st.caption("This normalized comparison is an analytical reference, not money-weighted portfolio performance.")
            risk=risk_metrics(portfolio,bench[benchmark]); a,b,c=st.columns(3)
            a.metric("Annualized volatility",f"{risk['annualized_volatility']:.2%}" if pd.notna(risk['annualized_volatility']) else "N/A"); b.metric("Maximum drawdown",f"{risk['max_drawdown']:.2%}" if pd.notna(risk['max_drawdown']) else "N/A"); c.metric(f"Beta vs {benchmark}",f"{risk['beta']:.2f}" if pd.notna(risk['beta']) else "N/A")
    if not sales.empty:
        fig=go.Figure(); fig.add_bar(x=sales.date,y=sales.realized_pl,name="Sale P/L"); fig.add_scatter(x=sales.date,y=sales.realized_pl.cumsum(),name="Cumulative P/L"); st.plotly_chart(fig.update_layout(title="Realized P/L history"),use_container_width=True)
