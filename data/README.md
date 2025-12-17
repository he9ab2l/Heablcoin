# Data Directory Overview

Purpose: central place for persisted artifacts. Keep sensitive files out of version control (.gitignore already covers db/json).

- `persist/` (create when needed): long-lived data, e.g. `trades.db`, exported CSV/JSON snapshots.
- `tmp/` (create when needed): short-lived caches or intermediate exports; safe to delete.
- `ingest/` (optional): raw pulls from exchanges/APIs before cleaning.
- `reports/` (optional): generated markdown/HTML/CSV reports saved outside repo root.

Guidelines
- Always note source & timestamp for raw pulls; prefer ISO date naming: `YYYYMMDD-HHMM_source.ext`.
- Keep large binaries out of git; store paths in `.env` or external storage if needed.
- Trade DB default: `data/trades.db` (SQLite). If relocated, update `TRADE_DB_FILE` in `.env`.
- If adding new datasets, document schema/columns here or alongside the producing script.
