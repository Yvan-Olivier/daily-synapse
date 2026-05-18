# ADR 0002 — Schema migration strategy in M3

**Date:** 2026-05-18
**Status:** Accepted

## Context

M3 introduces two new columns on `anthropic_articles` (`criticized_at`,
`critic_approved`) as part of the fix for two silent-loss bugs in the
LangGraph pipeline (Critic API failure conflated with rejection;
delivery failure leaving Articles permanently unsent).

The dev DB already contains M0–M3 test data. We need to decide how to
apply the schema change.

## Decision

Drop and recreate the DB locally. No migration tooling in M3.

Procedure:
1. `docker compose down -v` — removes the Postgres volume
2. `docker compose up -d` — fresh Postgres
3. `uv run python -m app.database.create_tables` — recreates schema from
   `models.py`
4. Re-run the Pipeline to repopulate from RSS

`create_tables.py` remains a one-liner over `Base.metadata.create_all()`.

## Why not Alembic now

Alembic gives us proper versioned, reversible migrations. We will
absolutely need it before M8 (Azure deployment with production data).

But in M3:
- The dev DB contains no business-critical data — only RSS test articles
  reproducible from feeds
- Adding Alembic now means writing the first migration manually plus
  baselining the existing schema — non-trivial setup cost
- That setup investment is better paid once, with intent, when we
  actually deploy a non-disposable database

## Why not idempotent ALTER in `create_tables.py`

Manually writing `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` inside
`create_tables.py` would let us preserve existing rows. But:
- It mixes "create schema from scratch" and "migrate schema forward" in
  one script — two distinct concerns
- It's a hand-rolled mini-migration system that we'd throw away when
  Alembic arrives
- The dev data has zero value, so the only benefit of preserving it
  doesn't apply

## Consequences

- Each schema change in M3–M7 will require a manual DB drop in dev
- Acceptable as long as data is reproducible from RSS feeds
- A follow-up ADR will introduce Alembic when M8 deployment is in scope
- M8 will also need a baseline migration capturing the final M7 schema
