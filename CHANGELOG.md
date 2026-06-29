# Changelog

## 2026-06-29 — E2E Testing Round

### Bugs Fixed

1. **Missing `email-validator` dependency** — Added to `requirements.txt`. Caused ImportError on startup.

2. **`bcrypt` version incompatibility** — `passlib` does not work with bcrypt 5.x (`module 'bcrypt' has no attribute '__about__'`). Pinned `bcrypt==4.2.1`.

3. **Rebalance plan/execute 500 error** — `calculate_rebalance_plan()` and `execute_rebalance()` called `self.get_portfolio(0, portfolio_id)` with `org_id=0` which filtered by `org_id=0`, causing `PortfolioNotFound`. Fixed by:
   - Added `org_id` parameter to both methods
   - When `org_id` is provided: use `get_portfolio(org_id, portfolio_id)` (proper scoping)
   - When `org_id` is None: fallback to direct id lookup (for internal calls where org check already done by router)
   - Updated routers to pass `org.id` to service methods

4. **Same pattern in `sync_from_broker()`** — Fixed with same approach.

5. **Same pattern in `_record_performance_snapshot()`** — Replaced `get_portfolio(0, portfolio_id)` with direct `db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))`.

### Test Suite

- Created `scripts/e2e_comprehensive.py` — 57 tests covering all APIs
- Tests: Auth (register/login/refresh/settings), Orgs (CRUD/members/roles), Brokers (CRUD/test), Portfolios (CRUD/summary), Holdings (CRUD/batch), Rebalance (plan/execute), Allocation, Performance
- Run with: `cd /home/dennis/fundbotai && source backend/venv/bin/activate && python scripts/e2e_comprehensive.py`
- **Result: 57/57 passed ✅**
