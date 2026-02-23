# Investment Council - Project Documentation

Welcome to the **Investment Council** codebase. This project is a state-of-the-art AI-driven investment advisory platform specifically designed for the Indian Equity Markets (NSE/BSE). It leverages a multi-agent orchestrated system to provide deep market insights and personalized portfolio recommendations.

---

## 🏗️ Architecture Overview

The system is split into a **Next.js Frontend** and a **FastAPI Backend**, communicating via a RESTful API. The core intelligence resides in a **LangGraph-powered Multi-Agent Council**.

### System Flow
1. **User Input**: User provides their risk profile and financial surplus.
2. **Orchestration**: A central graph coordinates multiple specialized AI agents.
3. **Reasoning Loop**: Agents debate (Scout vs. Risk) until the Orchestrator is satisfied.
4. **Personalization**: The final advice is tailored to the specific user's liquidity needs and risk appetite.
5. **UI Rendering**: The frontend displays the market regime, recommended portfolio, and reasoning.

---

## 📂 Project Structure

### 🌐 Backend (`/src`)
Located in the root `src` directory, the backend handles data fetching, AI reasoning, and API serving.

#### 📍 API Layer (`src/api/`)
- **`server.py`**: The main FastAPI application. Defines all REST endpoints, CORS policies, in-memory caching, and `X-Cache: HIT/MISS` response headers on all cacheable routes.
- **`models.py`**: Pydantic models for request/response validation.
  - **Original models** (untouched): `RecommendationRequest`, `PortfolioItem`, `RecommendationResponse`
  - **Phase-1 models** (added): `ChartCandle`, `IndexDetail`, `MoverDetail`, `TopMoversResponse`, `SectorData`, `SectorsResponse`, `SearchResult`, `SearchResponse`, `StockDetail`, `MarketStatusResponse`, `HealthResponse`

#### 🧠 Orchestrator (`src/orchestrator/`)
- **`graph.py`**: **The Heart of the System.** Defines the LangGraph state machine. It registers nodes (agents) and defines the edges (loops and conditional logic).
- **`state.py` (in `src/core/`)**: Defines the `InvestmentState` object which flows through the graph.
    - **Key State Components**:
        - `user_profile`: Risk scores, income, and financial constraints.
        - `market_context`: Market regime (BULL/BEAR) and confidence scores.
        - `scout_recommendations`: List of tickers with quality scores and reasoning.
        - `risk_assessment`: Audit results (verdict, metrics, feedback).
        - `orchestrator_decision`: Final meta-decision (Approved/Reject/Debate).
        - `feedback_for_scout`: Structured directives used during the debate loop.

#### 🤖 AI Agents (`src/agents/`)
Specialized nodes in the LangGraph workflow:
- **`market_node.py`**: Analyzes the current market regime (BULLISH, BEARISH, NEUTRAL).
- **`scout_node.py`**: Uses RAG or market data to suggest high-potential stocks.
- **`risk_node.py`**: Acts as a "Devil's Advocate," auditing recommendations for volatility and correlation risks.
- **`orchestrate_debate_node.py`**: The brain that decides if recommendations are "Council Approved" or need another round of scouting.
- **`personalization_node.py`**: Finalizes the portfolio based on the user's specific financial constraints.

#### 🛠️ Utilities (`src/utils/`)
- **`market_data.py`**: `yfinance` wrappers for real-time/historical data **plus** Phase-1 calculation helpers:
  - `calculate_sma(series, period)` — Rolling simple moving average
  - `calculate_rsi(series, period=14)` — Wilder RSI (matches TradingView)
  - `get_regime(price, sma_50)` → `(regime, confidence)` — BULLISH/BEARISH/NEUTRAL + 0–1 confidence
  - `hist_to_chart(df)` — Converts yfinance DataFrame to IST-timestamped OHLCV list
  - `fetch_tickers_parallel(tickers, period, interval)` — ThreadPoolExecutor parallel fetch for multiple tickers
  - *(Used by agents, untouched)*: `fetch_market_indicators()`, `fetch_sectoral_breadth()`
- **`stock_universe.py`** *(new, Phase 1)*: Hardcoded master list of **79 NSE stocks** (NIFTY 100 subset) with name, sector, and industry. Contains:
  - `STOCK_UNIVERSE` — dict keyed by NSE symbol
  - `SECTOR_CONSTITUENTS` — 8 sectors × 5 tickers for the `/api/sectors` heatmap
  - `search_universe(query, max_results=8)` — fast in-process substring search
- **`behavioral_profiling.py`**: Logic to map user answers to risk categories.
- **`orchestrator_utils.py`**: Helpers for the orchestrator agent.
- **`personalization_tools.py`**: Tools for the personalization agent.
- **`risk_tools.py`**: Tools for the risk audit agent.
- **`scout_tools.py`**: Tools for the scout agent.

---

### 🎨 Frontend (`/frontend`)
A modern, high-performance web application built with **Next.js 16 (Turbopack)**.

#### 🚀 Core App (`frontend/src/app/`)
- **`layout.tsx`**: Defines the global structure and font loading (Inter & Outfit).
- **`page.tsx`**: The main dashboard. Contains the Market Strip, Indices Grid, and the "Convene the Council" trigger.
- **`globals.css`**: Expertly crafted CSS variables and animations (glassmorphism, skeleton loaders).

#### 🧩 Components (`frontend/src/components/`)
- **`ui/`**: Atomic components like `Card.tsx`, `Badge.tsx`, and buttons.
- **Visuals**: Uses `lucide-react` for iconography and custom Tailwind animations for a premium feel.

#### 🔌 Data Fetching (`frontend/src/lib/`)
- **`api.ts`**: Axios-based client for communicating with the FastAPI backend.
- **`utils.ts`**: Formatting helpers for INR currency and percentages.

---

## 📡 API Endpoints

### Infrastructure
| Endpoint | Method | Cache | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | None | Server heartbeat — `{ status, timestamp }` in IST |
| `/api/market-status` | `GET` | None | NSE session info — `is_open`, `session`, `next_open` |

### Market Data
| Endpoint | Method | Cache | Description |
| :--- | :--- | :--- | :--- |
| `/api/market-indices` | `GET` | 5 min | NIFTY 50, SENSEX, BANK NIFTY with sparkline, year h/l, and regime |
| `/api/top-movers` | `GET` | 3 min | Top 5 gainers/losers with volume surge flag, sector, sparkline |
| `/api/sectors` | `GET` | 10 min | Sector heatmap — 8 sectors, 1d/1w/1m performance, market cap (₹ cr) |
| `/api/search?q=` | `GET` | None | Instant search across 79 NSE stocks — returns price, sector, market cap |
| `/api/stock/{symbol}` | `GET` | 2 min | Full detail: 5 chart timeframes, SMA 20/50/200, RSI, all fundamentals |

### AI Council
| Endpoint | Method | Cache | Description |
| :--- | :--- | :--- | :--- |
| `/api/council/analyze` | `POST` | None | Triggers the LangGraph multi-agent workflow. Returns portfolio + reasoning. |

> **Caching note**: Every cacheable endpoint sets an `X-Cache: HIT` or `X-Cache: MISS` response header so the frontend can detect staleness.

### `/api/stock/{symbol}` Response Shape (key fields)
```
price, change, change_pct, open, day_high, day_low, prev_close, year_high, year_low
volume, avg_volume
market_cap_cr, pe_ratio, pb_ratio, dividend_yield, eps, roe, debt_to_equity
revenue_cr, profit_cr
chart_1d  (5-min OHLCV for today)
chart_1w  (15-min OHLCV for past 5 days)
chart_1m  (daily OHLCV for past month)
chart_1y  (daily OHLCV for past year)
chart_5y  (weekly OHLCV for past 5 years)
sma_20, sma_50, sma_200, rsi_14, above_sma_50, above_sma_200
regime, regime_confidence
```

---

## 🛠️ Setup & Development

### Backend (Python)
1. Navigate to root: `cd InvestmentCouncil`
2. Install: `pip install -r requirements.txt`
3. Run: `python -m uvicorn src.api.server:app --reload --port 8000`
4. Open API docs: `http://localhost:8000/docs`

### Frontend (Next.js)
1. Navigate to frontend: `cd frontend`
2. Install: `npm install`
3. Run: `npm run dev` (http://localhost:3000)
4. Build: `npm run build`

---

## 📝 Coding Standards
- **Strict Typing**: Use Pydantic models for Backend and TypeScript interfaces for Frontend.
- **State Persistence**: The backend uses LangGraph's `MemorySaver` for thread-safe state management.
- **Performance**: Frontend uses `SWR` for optimistic UI updates and efficient caching. Backend uses `ThreadPoolExecutor` for parallel yfinance fetching in the sectors endpoint.
- **Monetary Values**: All INR values are in **crores** (`_cr` suffix). Conversion rate: 1 USD = 83 INR.
- **Timestamps**: All timestamps returned by the API are in **IST** (Asia/Kolkata), ISO 8601 format.
- **Error Handling**: If yfinance returns empty data, endpoints return a clean `404` with `{ "error": "...", "symbol": "..." }`.
- **Aesthetics**: Follow the "Premium UI" guidelines — use the custom HSL color tokens defined in `tailwind.config.ts`.

---

## 🗺️ Development Progress

### ✅ Phase 1 — Backend Market Data Layer (Complete)
- [x] `src/utils/stock_universe.py` — 79-stock NSE master list
- [x] `src/utils/market_data.py` — RSI, SMA, regime, parallel fetch helpers
- [x] `src/api/models.py` — 9 new Pydantic response models
- [x] `src/api/server.py` — 3 new endpoints + 4 enriched endpoints + X-Cache headers
- [x] Server verified running at `http://localhost:8000`

### 🔲 Phase 2 — Frontend Integration (Upcoming)
- [ ] Wire market-indices to live sparklines
- [ ] Build `/sectors` heatmap component
- [ ] Build stock detail page with multi-timeframe charts
- [ ] Connect search bar to `/api/search`
- [ ] Build "Convene the Council" flow with form + result display
