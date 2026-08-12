"""Groq integration; deterministic calculations stay outside this module."""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = """You are an analytical personal portfolio assistant. Use only supplied context for portfolio-specific numerical claims. Never fabricate prices, transactions, returns, metrics, news, or holdings. Clearly distinguish facts from interpretation. All calculations are externally performed and must not be recalculated or overridden. Be concise. This is educational information, not personalized investment advice."""


def get_groq_client():
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=key)
    except Exception:
        return None


def build_portfolio_context(summary: dict[str, Any], holdings, sales, concentration: dict[str, Any], benchmark: dict[str, Any] | None = None) -> str:
    """Build compact, calculated context and deliberately omit raw transaction rows."""
    data = {"portfolio_summary": summary, "holdings": holdings.to_dict("records") if not holdings.empty else [], "realized_sales": sales.to_dict("records") if not sales.empty else [], "concentration": concentration, "benchmark": benchmark or {}}
    return json.dumps(data, default=str, separators=(",", ":"))


def _chat(prompt: str) -> str | None:
    client = get_groq_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(model=MODEL, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=0.2, max_tokens=350)
        return response.choices[0].message.content
    except Exception:
        return None


def generate_portfolio_health_summary(context: str) -> str | None:
    return _chat(f"Provide a concise 2-3 sentence portfolio health assessment. Discuss concentration, diversification and notable exposure only from this context:\n{context}")


def answer_portfolio_question(question: str, context: str) -> str | None:
    return _chat(f"Portfolio context:\n{context}\n\nQuestion: {question}")
