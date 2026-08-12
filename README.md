# Stock Analyst Agent

Phase 1 is a personal US-stock portfolio dashboard. Upload transaction history, reconstruct open positions using deterministic FIFO accounting, retrieve Yahoo Finance prices, review lifetime performance against a benchmark, and optionally ask a Groq-powered analyst about the calculated results.

## Documentation

- [Project overview and architecture](docs/project-overview.md) — product goals, system boundaries, architecture, and technology choices.
- [Phase 1 requirements](docs/phase-1-requirements.md) — user workflow, functional requirements, acceptance criteria, and scope.
- [Phase 1 implementation](docs/phase-1-implementation.md) — code map, data flow, formulas, state, configuration, and tests.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/canreddy/stock-analyst-agent.git
cd stock-analyst-agent
uv sync
cp .env.example .env
uv run streamlit run app.py
```

Set `GROQ_API_KEY` in `.env` to enable AI features. Without it, the dashboard and all deterministic calculations continue to work.

Run tests with:

```bash
uv run pytest
```
