# US Stock Daily Strategy Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a private, click-to-analyze US-stock daily-swing research app that calculates traceable long and short add-on, target, and invalidation zones.

**Architecture:** A modular FastAPI service obtains and caches daily OHLCV data, calculates deterministic indicators and strategy candidates, persists immutable analysis/version/backtest records in SQLite, and exposes a typed REST API. A React/TypeScript client renders a Finviz-inspired dark dashboard with a candlestick chart and strategy cards. An optional OpenAI-compatible adapter explains only engine-provided facts and proposes offline parameter changes; it never supplies live price levels.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, yfinance, pandas/numpy, pytest; React, TypeScript, Vite, Lightweight Charts, Vitest, Testing Library; SQLite and Docker Compose.

---

## File structure

- `backend/app/domain/models.py` defines typed candles, zones, candidates, analysis, version and backtest contracts.
- `backend/app/engine/indicators.py`, `zones.py`, and `strategy.py` implement all deterministic daily calculations.
- `backend/app/services/market_data.py`, `analysis.py`, `llm.py`, and `backtest.py` orchestrate data, storage-safe analysis, explanations and isolated research.
- `backend/app/db.py` and `backend/app/repositories.py` own SQLite entities and persistence.
- `backend/app/api.py` exposes the REST interface; `backend/app/main.py` creates the application.
- `backend/tests/` contains fixed-sample, regression, API, failure-mode and schema tests.
- `frontend/src/` contains API types/client, chart, cards, history view, app shell and UI tests.
- `docker-compose.yml`, Dockerfiles, and `README.md` provide local deployment and operational boundaries.

### Task 1: Bootstrap the repository and contracts

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/domain/models.py`
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`
- Test: `backend/tests/test_models.py`

- [ ] Write a failing test constructing an `OhlcvBar` and rejecting non-positive prices, then run `pytest backend/tests/test_models.py -v` and confirm it fails because imports are absent.
- [ ] Create the minimal Pydantic domain contract with `OhlcvBar`, `PriceZone`, `StrategyCandidate`, and `AnalysisResult`; run the same test until it passes.
- [ ] Add package manifests, formatter/linter/test commands and pinned runtime dependencies.
- [ ] Commit `chore: bootstrap strategy tool contracts`.

### Task 2: Implement indicators using fixed candles

**Files:**
- Create: `backend/app/engine/indicators.py`
- Create: `backend/tests/test_indicators.py`

- [ ] Add a failing test with a fixed 20-bar DataFrame asserting SMA, Wilder ATR(14), SMA50 ten-bar slope and rolling mean volume values.
- [ ] Run `pytest backend/tests/test_indicators.py -v`; confirm the test fails because `compute_indicators` is absent.
- [ ] Implement `compute_indicators(frame)` using rolling SMA, Wilder smoothing (`ewm(alpha=1/14, adjust=False)`) and non-mutating indexed output.
- [ ] Re-run the focused test and full backend suite; commit `feat: calculate daily technical indicators`.

### Task 3: Detect pivots and aggregate support/resistance zones

**Files:**
- Create: `backend/app/engine/zones.py`
- Create: `backend/tests/test_zones.py`

- [ ] Write failing tests for a three-bars-on-each-side swing high/low and for grouping adjacent pivot prices within `max(0.8*ATR, close*0.01)`.
- [ ] Run the focused tests and verify missing-module failure.
- [ ] Implement `find_pivots`, `build_price_zones`, strength from touches plus recency, and deterministic nearest-zone ordering.
- [ ] Verify focused and complete tests; commit `feat: derive support and resistance zones`.

### Task 4: Produce deterministic trade candidates and price levels

**Files:**
- Create: `backend/app/engine/strategy.py`, `backend/app/engine/defaults.py`
- Create: `backend/tests/test_strategy.py`, `backend/tests/fixtures/candles.py`

- [ ] Write fixed-candle failing tests for long pullback, long breakout, short rejection, short breakdown, 1R invalidation, 1.5R/2.5R fallback targets and invalid candidates below 1.5R.
- [ ] Run `pytest backend/tests/test_strategy.py -v`, confirm candidate generation is missing.
- [ ] Implement configured trend/confirmation/score components (35/30/20/15), add zone-centered entry ranges, and ensure every returned numerical level has an engine source.
- [ ] Add regression snapshot assertions for a known sample; verify all tests; commit `feat: generate traceable long and short strategies`.

### Task 5: Persist cache, analyses, versions, and backtests

**Files:**
- Create: `backend/app/db.py`, `backend/app/repositories.py`
- Create: `backend/tests/test_repositories.py`

- [ ] Write failing SQLite tests proving cached candles round-trip, analyses retain engine payload, and strategy versions are immutable.
- [ ] Run the repository test, verify database module is absent.
- [ ] Add SQLAlchemy models/repositories with JSON payloads, explicit timestamps and a local `data/gushen.sqlite3` default.
- [ ] Re-run tests and commit `feat: persist research records in sqlite`.

### Task 6: Add resilient yfinance data retrieval

**Files:**
- Create: `backend/app/services/market_data.py`
- Create: `backend/tests/test_market_data.py`

- [ ] Write failing tests using a fake downloader for canonical ticker normalization, cache-first behavior, fetch failure fallback, insufficient data and stale-cache metadata.
- [ ] Confirm tests fail before the adapter exists.
- [ ] Implement `MarketDataService` with a downloader protocol, daily OHLCV normalization, 24-hour cache freshness and structured `MarketDataError` codes; production wiring uses `yfinance.download` without API keys.
- [ ] Run the complete suite and commit `feat: retrieve and degrade daily market data safely`.

### Task 7: Orchestrate analysis and constrain LLM output

**Files:**
- Create: `backend/app/services/analysis.py`, `backend/app/services/llm.py`
- Create: `backend/tests/test_analysis_service.py`, `backend/tests/test_llm.py`

- [ ] Add failing tests that analysis saves timestamped output and that an LLM response is rejected when a price is not equal to an engine level.
- [ ] Run focused tests to confirm missing service failures.
- [ ] Implement `AnalysisService`, factual explanation request/validation, environment-only configuration, and a safe no-LLM fallback. Never log credentials or make LLM prices authoritative.
- [ ] Verify tests and commit `feat: orchestrate analysis with constrained explanations`.

### Task 8: Implement time-isolated parameter research and backtesting

**Files:**
- Create: `backend/app/services/backtest.py`, `backend/app/services/optimization.py`
- Create: `backend/tests/test_backtest.py`, `backend/tests/test_optimization.py`

- [ ] Write failing tests ensuring an optimizer dataset ends at 2025-12-31 and a sample 2026 bar never reaches the proposal prompt; add a deterministic target/invalidation outcome test.
- [ ] Run focused tests and verify expected failure.
- [ ] Implement long/short candidate simulation, metrics (returns, win rate, max drawdown, payoff, count, target and invalidation rates), immutable proposals and baseline-vs-candidate adoption recommendation only.
- [ ] Run complete tests; commit `feat: add isolated backtesting and parameter proposals`.

### Task 9: Expose a safe REST API

**Files:**
- Create: `backend/app/api.py`, `backend/app/main.py`
- Create: `backend/tests/test_api.py`

- [ ] Write failing FastAPI client tests for `POST /api/analysis`, validation errors, data-failure responses, history listing/detail, strategies and backtest report endpoints.
- [ ] Run `pytest backend/tests/test_api.py -v` and verify routes do not exist.
- [ ] Add dependency wiring, CORS for the local client, error mapping, OpenAPI response models and a `/health` endpoint.
- [ ] Run backend tests; commit `feat: expose strategy research api`.

### Task 10: Build the chart-first frontend

**Files:**
- Create: `frontend/src/api.ts`, `frontend/src/types.ts`, `frontend/src/App.tsx`, `frontend/src/styles.css`
- Create: `frontend/src/components/PriceChart.tsx`, `StrategyCard.tsx`, `AnalysisPanel.tsx`, `HistoryPanel.tsx`
- Create: `frontend/src/*.test.tsx`

- [ ] Write failing component tests for loading, usable strategy, no-opportunity, market-data failure and history display states.
- [ ] Run `npm test -- --run` in `frontend`, confirm components are absent.
- [ ] Implement typed API calls and responsive Finviz-like dark UI. Render OHLCV candles, SMA series, zones/levels, main long candidate and secondary short candidate without inventing values.
- [ ] Run frontend tests and production build; commit `feat: add chart-first research dashboard`.

### Task 11: Package, document, and verify the system

**Files:**
- Create: `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `README.md`, `.env.example`
- Modify: `.gitignore`

- [ ] Write a smoke test script or API test asserting the packaged app health endpoint.
- [ ] Add containers, environment documentation (placeholder names only), explicit research-only disclaimer, runbook, test commands and known yfinance limitations.
- [ ] Execute `pytest`, `npm test -- --run`, `npm run build`, and compose configuration validation; correct any failures.
- [ ] Commit `docs: package and document strategy tool`.

## Self-review

- Spec coverage: Tasks 2–4 implement all indicators, zones, templates, scoring and price rules; Tasks 5–6 cover caching/persistence/data failure; Task 7 keeps LLM factual; Task 8 enforces 2023–2025 research and 2026-H1 isolation; Tasks 9–10 implement required UI/API states and history; Task 11 documents deployment and boundaries.
- Placeholder scan: no implementation step delegates behavior without a named file, test, command or expected outcome.
- Type consistency: `OhlcvBar`, `PriceZone`, `StrategyCandidate`, `AnalysisResult`, `MarketDataService`, `AnalysisService`, and version/backtest contracts are introduced before their consumers.
