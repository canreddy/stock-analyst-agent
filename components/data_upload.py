"""Data upload tab."""
from __future__ import annotations
import hashlib

import streamlit as st
from utils.data_processing import TransactionValidationError, sample_csv_bytes, validate_transactions

def render() -> None:
    st.header("Upload transaction history")
    if st.session_state.get("transactions") is None:
        st.info("1. Upload your stock transaction CSV.  2. We reconstruct holdings with FIFO.  3. Yahoo Finance supplies current prices.  4. Performance and AI analysis are calculated from those inputs.")
    st.caption("Required schema: ticker, date, transaction_type, quantity, price")
    st.download_button("Download sample CSV", sample_csv_bytes(), "sample_transactions.csv", "text/csv")
    file = st.file_uploader("Transaction CSV", type="csv", key="transaction_csv")
    if file:
        signature = hashlib.sha256(file.getvalue()).hexdigest()
        if signature == st.session_state.get("upload_signature"):
            file = None
    if file:
        try:
            frame = validate_transactions(file)
            st.session_state.transactions = frame
            st.session_state.uploaded_filename = file.name
            st.session_state.upload_signature = signature
            # These values belong to the preceding file and must not appear for a new upload.
            st.session_state.holdings_table = None
            st.session_state.sales = None
            st.session_state.market_refreshed = None
            st.rerun()
        except TransactionValidationError as exc:
            st.error(str(exc)); return
    frame = st.session_state.get("transactions")
    if frame is not None:
        a,b,c,d = st.columns(4)
        a.metric("Transactions", len(frame)); b.metric("Tickers", frame.ticker.nunique()); c.metric("Earliest", str(frame.date.min().date())); d.metric("Latest", str(frame.date.max().date()))
        st.dataframe(frame, use_container_width=True, hide_index=True)
