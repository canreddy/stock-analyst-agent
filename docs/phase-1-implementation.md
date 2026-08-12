# Phase 1 Implementation

## Code map

| Path | Responsibility |
| --- | --- |
| `app.py` | Page configuration, session state, sidebar, and tab orchestration |
| `components/data_upload.py` | CSV upload, sample download, validation feedback, and transaction display |
| `components/portfolio_view.py` | Holdings dashboard, allocation, concentration, drilldown, and AI health summary |
| `components/performance_view.py` | Lifetime metrics, history, benchmark comparison, risk, and realized P/L charts |
| `components/ai_analyst.py` | Portfolio chat interface and chat history |
| `utils/data_processing.py` | CSV parsing, normalization, validation, and oversell detection |
| `utils/portfolio_math.py` | FIFO matching and deterministic portfolio calculations |
| `utils/market_data.py` | Cached Yahoo Finance quote and history access |
| `utils/llm_agent.py` | Groq client, compact context construction, and prompts |
| `tests/` | Validation, FIFO, summary, concentration, and XIRR unit tests |

## Runtime data flow

### Upload

`validate_transactions()` reads the CSV, selects required columns, normalizes values, sorts rows stably by date, and tracks available shares per ticker. A SHA-256 signature prevents Streamlit reruns from processing the same uploaded file repeatedly.

A new upload clears holdings, sales, and market refresh state so results from a previous portfolio cannot leak into the new one.

### FIFO accounting

`fifo_match()` maintains a queue of purchase lots for every ticker. Each sell consumes the oldest lots until its quantity is satisfied. It returns:

- remaining holdings with quantity, cost basis, and average cost;
- sales with proceeds, matched cost basis, and realized P/L.

For a sale:

```text
realized P/L = sale proceeds - FIFO cost basis consumed
```

### Market enrichment

`get_quotes()` downloads five daily observations and uses the final two closes as current price and previous close. `build_holdings_table()` joins those quotes to FIFO holdings and calculates position values.

```text
market value     = quantity x current price
unrealized P/L   = market value - remaining cost basis
today's P/L      = quantity x (current price - previous close)
portfolio weight = market value / total market value
```

Quote calls tolerate missing symbols and return empty or partial frames on failure. Streamlit caching limits repeated network calls.

### Performance

`performance_summary()` calculates:

```text
total economic P/L = sell proceeds + current value - total buy investment
simple return      = total economic P/L / total buy investment
```

`calculate_xirr()` represents buys as negative cash flows, sells as positive cash flows, and current portfolio value as a terminal positive cash flow. It returns `NaN` when no valid solution exists.

Historical quantity is reconstructed for each trading date and multiplied by adjusted closing prices. The benchmark chart normalizes both series to 100; it is a comparison view rather than a money-weighted return.

Risk calculations use daily percentage changes:

- annualized volatility: daily sample standard deviation multiplied by the square root of 252;
- maximum drawdown: worst decline from the running portfolio peak;
- beta: covariance with benchmark returns divided by benchmark variance.

### AI integration

`build_portfolio_context()` serializes calculated summaries, holdings, realized sales, concentration, and optional benchmark values. Raw transaction rows are deliberately omitted.

The system prompt instructs the model to use only supplied context for numerical portfolio claims. A low temperature is used, and failures return `None` so the interface can show a fallback without affecting portfolio calculations.

## Session state

Important keys include:

| Key | Contents |
| --- | --- |
| `transactions` | Validated transaction data frame |
| `uploaded_filename` | Current source filename |
| `upload_signature` | Hash of current upload |
| `holdings_table` | FIFO holdings enriched with quotes |
| `sales` | FIFO realized-sale details |
| `market_refreshed` | Last quote refresh timestamp |
| `chat_history` | Current AI conversation |

## Configuration and execution

Install and run:

```bash
uv sync
cp .env.example .env
uv run streamlit run app.py
```

Set `GROQ_API_KEY` in `.env` only when AI features are required. Market and deterministic portfolio features do not depend on that key.

Run tests with:

```bash
uv run pytest
```

The tests intentionally avoid live market-data and AI calls. They cover data validation, chronological oversells, FIFO lot consumption, liquidation and repurchase, multi-ticker sales, summary metrics, concentration, and valid/invalid XIRR cases.

## Known implementation constraints

- Application state exists only for the active Streamlit session.
- Yahoo Finance availability and values are outside the application's control.
- A transaction occurring on a non-trading day is applied at the next available market close in historical reconstruction.
- The historical portfolio series values positions using available close data and does not model intraday movements.
- Current exception handling favors a stable UI; external-service details are not exposed to end users.

