"""Stock Analyst Agent: Phase 1 personal portfolio dashboard."""
from __future__ import annotations
from datetime import datetime
import streamlit as st
from components import ai_analyst, data_upload, performance_view, portfolio_view
from utils.llm_agent import MODEL, get_groq_client
from utils.market_data import refresh_market_cache

st.set_page_config(page_title="Stock Analyst Agent", layout="wide")
st.title("Stock Analyst Agent")
st.caption("Personal Portfolio Dashboard · FIFO accounting · market-aware analytics")
for key,value in {"transactions":None,"uploaded_filename":None,"holdings_table":None,"sales":None,"market_refreshed":None,"upload_signature":None}.items(): st.session_state.setdefault(key,value)
with st.sidebar:
    st.header("Portfolio")
    st.write(f"**File:** {st.session_state.uploaded_filename or 'None uploaded'}")
    st.write(f"**Transactions:** {len(st.session_state.transactions) if st.session_state.transactions is not None else 0}")
    st.write(f"**Active holdings:** {len(st.session_state.holdings_table) if st.session_state.holdings_table is not None else 0}")
    st.header("Market Data"); benchmark=st.text_input("Benchmark",value="SPY").strip().upper() or "SPY"
    stamp=st.session_state.market_refreshed
    st.caption(f"Last refreshed: {stamp or 'Not yet loaded'}")
    if st.button("Refresh Market Data"):
        refresh_market_cache(); st.session_state.market_refreshed=datetime.now().isoformat(); st.rerun()
    st.header("AI"); st.write("Groq status: " + ("Configured" if get_groq_client() else "Unavailable")); st.caption(f"Model: {MODEL}")
tabs=st.tabs(["Data Upload","Portfolio","Performance","AI Analyst"])
with tabs[0]: data_upload.render()
with tabs[1]: portfolio_view.render()
with tabs[2]: performance_view.render(benchmark)
with tabs[3]: ai_analyst.render()
