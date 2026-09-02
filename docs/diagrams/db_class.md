# Class diagram — `backend/db.py`

```mermaid
classDiagram
    class Rimiru {
        -_instance: Rimiru$
        -_pool: asyncpg.Pool$
        -pool: asyncpg.Pool
        +__init__(pool)
        +shion()$ Rimiru
        +transaction()
        +select(table, columns, filters, raw_where, raw_params, order_by, limit) list~dict~
        +selectOne(table, columns, filters, order_by) dict
        +upsert(table, data, conflict_column?) dict
        +delete(table, filters) list
        +call_function(fn, params, fetch_type) list|scalar|dict
        +execute(sql, params, fetch) list~dict~|None
    }
    class FetchType {
        <<enumeration>>
        FETCH
        FETCHVAL
        FETCHROW
    }
    Rimiru ..> FetchType : call_function() fetch_type param
    note for Rimiru "Singleton via classmethod factory\nshion(), not create()/similar — same\npattern as Libra's JobDatabase.create(),\ndifferent name. min_size=2, max_size=10,\nSSL enabled with hostname check and\ncert verification both disabled."
```

## Notes

- `shion()` is the async factory/singleton accessor — mirrors Libra's
  `JobDatabase.create()` pattern (pool built once, cached on the class), just
  named differently. There is no table-name constant anywhere in this file —
  every caller passes its own table string. Callers today: `routes/auth.py`,
  `routes/emails.py`, `routes/application.py`.
- `execute()`'s docstring is the only place in the file warning that
  table/column names must come from trusted code, not request data — `sql`
  itself is never validated, only parameterized via `$1, $2...` placeholders.
  `execute(..., fetch=False)` returns the raw asyncpg status string.
- `conflict_column` is optional. When the only column written is the conflict
  column, `upsert()` emits `ON CONFLICT DO NOTHING` with no `RETURNING` and
  returns `None` — callers that need the existing row's id must do an explicit
  insert-or-get instead (as `resolve_application` does for `company`).
- `upsert()` now logs and re-raises on exception (via [[Logging]]).
- Every method emits `DEBUG`/`INFO` log lines; the per-run `db.log` is a full
  statement trace.
- `Rimiru`/`Duro` names don't describe what the classes do (a DB layer and an
  LLM classifier, respectively) — likely a naming convention or in-joke
  carried over from elsewhere in the codebase, not something with functional
  significance for readers of this doc.
