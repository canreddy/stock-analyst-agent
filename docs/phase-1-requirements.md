# Phase 1 Requirements

## Goal

Deliver a local personal portfolio dashboard that turns a valid transaction CSV into current holdings, lifetime performance, benchmark analytics, and optional AI commentary.

## User workflow

1. Start the Streamlit application.
2. Upload a transaction CSV or download the provided sample.
3. Review normalized transactions.
4. Open the Portfolio tab to load quotes and build current holdings.
5. Review allocation, position metrics, concentration, and ticker history.
6. Open Performance to review lifetime results and benchmark analytics.
7. Optionally ask questions in AI Analyst when a Groq API key is configured.

## Input requirements

The CSV must contain exactly the fields used by the application:

| Field | Requirement |
| --- | --- |
| `ticker` | Non-empty; trimmed and converted to uppercase |
| `date` | Valid date |
| `transaction_type` | `Buy` or `Sell` |
| `quantity` | Numeric and greater than zero |
| `price` | Numeric and greater than zero |

Transactions are processed chronologically. Rows sharing a date retain their original CSV order. A sell must not exceed the shares available at that point.

## Portfolio requirements

- Match sold shares against the oldest available purchase lots.
- Retain quantity, cost basis, and average cost for open positions.
- Display current price, prior close, market value, unrealized P/L, daily P/L, and portfolio weight when quotes are available.
- Display allocation, largest holding weight, top-three weight, and HHI.
- Identify best/worst returns and largest gains/losses.
- Provide ticker price history with buy and sell markers.
- Allow current holdings to be downloaded as CSV.

## Performance requirements

- Display total investment and total sell proceeds.
- Separate realized and unrealized P/L.
- Calculate total economic P/L and simple lifetime return.
- Calculate XIRR when the cash-flow pattern has a valid solution.
- Reconstruct historical end-of-day portfolio value.
- Compare portfolio and benchmark as normalized series starting at 100.
- Calculate annualized volatility, maximum drawdown, and beta when enough data exists.
- Display realized P/L by sale and cumulatively.

## Market-data requirements

- Fetch symbols in batches where practical.
- Cache current quotes for five minutes and history for one hour.
- Provide an explicit cache refresh action.
- Continue with partial results when a symbol or request fails.
- Clearly show unavailable values rather than inventing them.

## AI requirements

- AI functionality is optional and controlled by `GROQ_API_KEY`.
- The app remains functional without an API key.
- Portfolio-specific numerical statements must come from calculated context.
- The model must distinguish supplied facts from interpretation.
- Responses must include an educational, non-advisory posture.
- Service errors must return a usable fallback message.

## Acceptance criteria

Phase 1 is complete when a valid CSV can be uploaded and all four tabs behave as specified; invalid or oversold histories are rejected; deterministic tests pass without live network calls; and absent external services do not crash the application.

## Out of scope

- Brokerage integration or automated trading
- User accounts and persistent cloud storage
- Tax-lot elections other than FIFO
- Dividends, fees, splits, options, short sales, and multiple currencies
- Guaranteed real-time or exchange-authoritative pricing
- Personalized investment, tax, or legal advice

