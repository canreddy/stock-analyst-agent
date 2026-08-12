"""Current holdings dashboard."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.llm_agent import build_portfolio_context, generate_portfolio_health_summary
from utils.market_data import get_price_history, get_quotes
from utils.portfolio_math import build_holdings_table, concentration_metrics, fifo_match

def _money(v): return "N/A" if pd.isna(v) else f"${v:,.2f}"
def render() -> None:
    tx = st.session_state.get("transactions")
    if tx is None: st.info("Upload a transaction CSV first."); return
    holdings, sales = fifo_match(tx)
    if holdings.empty: st.info("There are no active holdings."); return
    with st.spinner("Loading latest market data..."):
        quotes, refreshed = get_quotes(tuple(holdings.ticker))
    table = build_holdings_table(holdings, quotes); st.session_state.holdings_table = table; st.session_state.sales = sales; st.session_state.market_refreshed = refreshed
    total = table.market_value.sum(); unrealized = table.unrealized_pl.sum(); today = table.today_pl.sum()
    cols = st.columns(4)
    for col,label,value in zip(cols,["Current Portfolio Value","Unrealized Gain/Loss","Today's Gain/Loss","Active Holdings"],[_money(total),_money(unrealized),_money(today),str(len(table))]): col.metric(label,value)
    left,right = st.columns([1,2])
    with left:
        st.plotly_chart(px.pie(table.dropna(subset=["market_value"]), names="ticker", values="market_value", hole=.55, title="Allocation"), use_container_width=True)
    with right:
        display = table.copy()
        for col in ["avg_cost_basis","cost_basis","current_price","market_value","unrealized_pl","today_pl"]: display[col] = display[col].map(_money)
        for col in ["unrealized_pl_pct","today_pct","portfolio_weight"]: display[col] = display[col].map(lambda x: "N/A" if pd.isna(x) else f"{x:.2%}")
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.download_button("Download current holdings", table.to_csv(index=False).encode(), "current_holdings.csv", "text/csv")
    concentration = concentration_metrics(table); st.subheader("Portfolio concentration")
    a,b,c=st.columns(3); a.metric("Largest holding",f"{concentration['largest_holding_pct']:.1%}"); b.metric("Top 3 holdings",f"{concentration['top_3_holding_pct']:.1%}"); c.metric("HHI",f"{concentration['hhi']:.3f}")
    valid=table.dropna(subset=["unrealized_pl_pct"])
    if not valid.empty:
        st.subheader("Winners and losers")
        cards=st.columns(4); vals=[("Best return",valid.loc[valid.unrealized_pl_pct.idxmax()]),("Worst return",valid.loc[valid.unrealized_pl_pct.idxmin()]),("Largest gain",valid.loc[valid.unrealized_pl.idxmax()]),("Largest loss",valid.loc[valid.unrealized_pl.idxmin()])]
        for card,(label,row) in zip(cards,vals): card.metric(label,row.ticker, _money(row.unrealized_pl))
    st.subheader("Ticker drilldown")
    ticker=st.selectbox("Active ticker",table.ticker)
    row=table[table.ticker==ticker].iloc[0]; realized=sales.loc[sales.ticker==ticker,"realized_pl"].sum(); deployed=(tx.loc[(tx.ticker==ticker)&(tx.transaction_type=="Buy"),"quantity"]*tx.loc[(tx.ticker==ticker)&(tx.transaction_type=="Buy"),"price"]).sum()
    st.write(f"**Quantity:** {row.quantity:g}  |  **Remaining cost:** {_money(row.cost_basis)}  |  **Average cost:** {_money(row.avg_cost_basis)}  |  **Lifetime realized P/L:** {_money(realized)}  |  **Unrealized P/L:** {_money(row.unrealized_pl)}  |  **Capital deployed:** {_money(deployed)}")
    hist=get_price_history((ticker,),str(tx.date.min().date()))
    if not hist.empty:
        fig=go.Figure(go.Scatter(x=hist.index,y=hist[ticker],name="Close")); t=tx[tx.ticker==ticker]
        for kind,color,symbol in [("Buy","green","triangle-up"),("Sell","red","triangle-down")]:
            x=t[t.transaction_type==kind]; fig.add_trace(go.Scatter(x=x.date,y=x.price,mode="markers",name=kind,marker={"color":color,"symbol":symbol,"size":11}))
        st.plotly_chart(fig.update_layout(title=f"{ticker} price and transactions"),use_container_width=True)
    st.subheader("AI Portfolio Health")
    context=build_portfolio_context({"current_value":total,"unrealized_pl":unrealized,"today_pl":today},table,sales,concentration)
    health=generate_portfolio_health_summary(context)
    st.write(health if health else "AI analysis is unavailable. Add GROQ_API_KEY to .env to enable it.")
