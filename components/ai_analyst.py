"""Conversational analyst tab."""
from __future__ import annotations
import streamlit as st
from utils.llm_agent import answer_portfolio_question, build_portfolio_context, get_groq_client
from utils.portfolio_math import concentration_metrics, performance_summary

def render() -> None:
    tx=st.session_state.get("transactions"); table=st.session_state.get("holdings_table"); sales=st.session_state.get("sales")
    if tx is None or table is None: st.info("Upload data and load Portfolio before using the AI analyst."); return
    if get_groq_client() is None: st.warning("AI analyst is unavailable. Set GROQ_API_KEY in .env, then restart Streamlit."); return
    history=st.session_state.setdefault("chat_history",[])
    for message in history:
        with st.chat_message(message["role"]): st.write(message["content"])
    question=st.chat_input("Ask about your portfolio")
    if question:
        history.append({"role":"user","content":question})
        with st.chat_message("user"): st.write(question)
        context=build_portfolio_context(performance_summary(tx,sales,table),table,sales,concentration_metrics(table))
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your calculated portfolio data..."):
                answer=answer_portfolio_question(question,context) or "I could not reach the AI service. Please try again."
            st.write(answer)
        history.append({"role":"assistant","content":answer})
