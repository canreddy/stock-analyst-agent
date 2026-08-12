# Project Overview and Architecture

## Purpose

Stock Analyst Agent is a personal US-stock portfolio analysis application. It converts a transaction history into auditable portfolio calculations, enriches the results with market data, and optionally provides AI-assisted interpretation.

The project separates deterministic financial calculations from external data and generative AI. Market-data or AI failures must not change the accounting results.

## Visual overview of the application to be built

The application guides the user through four connected views:

```text
1. Upload transactions --> 2. Review current portfolio
                                  |
                                  v
4. Ask the AI analyst <-- 3. Analyze performance
```

<table>
  <tr>
    <td width="50%">
      <strong>1. Data Upload</strong><br><br>
      Upload and validate the transaction CSV, then review the cleaned transaction history.<br><br>
      <img src="screenshots/data-upload.png" alt="Data Upload tab" width="100%">
    </td>
    <td width="50%">
      <strong>2. Consolidated Portfolio</strong><br><br>
      Review current value, FIFO holdings, allocation, gains and losses, and concentration.<br><br>
      <img src="screenshots/portfolio.png" alt="Consolidated Portfolio tab" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%">
      <strong>3. Historical Performance</strong><br><br>
      Analyze lifetime returns, XIRR, portfolio history, benchmark comparison, and risk metrics.<br><br>
      <img src="screenshots/performance.png" alt="Historical Performance tab" width="100%">
    </td>
    <td width="50%">
      <strong>4. AI Analyst</strong><br><br>
      Ask grounded questions about the calculated portfolio results through the Groq-powered chat.<br><br>
      <img src="screenshots/ai-analyst.png" alt="AI Analyst tab" width="100%">
    </td>
  </tr>
</table>

This visual follows the four-tab concept described in the [original project outline](https://docs.google.com/document/d/16oLxxmYK2GZM5efp3aSS7HSyjIDyy-p8J5TY6CRyqAo/edit?tab=t.wtxcv7qlsdnx).

## Project requirements

### Functional requirements

- Accept a user's stock transaction history in CSV format.
- Validate and normalize transactions before analysis.
- Reconstruct open positions and realized sales using FIFO accounting.
- Show current holdings, allocation, gains and losses, and concentration.
- Calculate lifetime performance, money-weighted return, and risk indicators.
- Compare portfolio history with a configurable market benchmark.
- Allow calculated holdings data to be exported.
- Optionally explain calculated results through an AI analyst.

### Quality requirements

- Financial calculations must be deterministic and independently testable.
- Invalid transactions, including chronological oversells, must be rejected.
- Missing market data must degrade gracefully instead of crashing the app.
- The AI must use supplied calculated context and must not invent portfolio facts.
- Raw transaction rows should not be sent to the AI service unnecessarily.
- The application must remain useful when the AI service is not configured.

## Architecture

The application uses a layered structure:

```text
CSV upload
   |
   v
Validation and normalization
   |
   v
FIFO accounting and portfolio calculations
   |                         |
   v                         v
Yahoo Finance enrichment     Compact AI context
   |                         |
   v                         v
Streamlit dashboard          Groq analyst
```

### Presentation layer

`app.py` configures the Streamlit page, shared session state, sidebar, and tabs. Files under `components/` render the upload, portfolio, performance, and AI views.

### Domain layer

Files under `utils/` contain validation, FIFO matching, performance formulas, risk calculations, market-data access, and AI integration. Accounting functions operate on pandas data frames and do not depend on the user interface.

### External services

- Yahoo Finance supplies current and historical prices through `yfinance`.
- Groq supplies optional portfolio explanations using `llama-3.3-70b-versatile`.

### State and persistence

The application stores the current upload and derived results in Streamlit session state. It does not include a database or permanent user account storage. Restarting the session clears the working portfolio.

## Technology stack

- Python 3.12+
- Streamlit
- pandas and NumPy
- Plotly
- yfinance
- pyxirr
- Groq SDK
- pytest
- uv for dependency and environment management

## Scope boundaries

The project is an analytical tool, not a brokerage, tax engine, trading system, or source of financial advice. It currently targets long-only US-stock transactions expressed as buys and sells.
