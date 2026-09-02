# Logging

`backend/logger.py` is the backend's logging layer. Every module gets a
logger via `get_logger(__name__)` (or `get_logger("emails")`); the name is
reduced to its last dotted segment, so `routes.emails` and a bare `"emails"`
share one logger and one file.

## On-disk layout

Each process start creates its own folder — the Quart reloader spawns two
processes, so you get two folders per `python app.py`:

```
backend/logs/
├── LATEST_RUN.txt                       # name + start time of the newest run
└── run_<YYYYMMDD-HHMMSS>_pid<pid>/
    ├── <ClassName>.log                  # one per logger: db.log, emails.log, EmailClassifier.log, auth.log, ...
    ├── combined.log                     # every line from every logger, interleaved
    └── flow.log                         # only section enter/exit markers — a high-level trace
```

`backend/logs/` is git-ignored (added to `.gitignore`).

The console (`stdout`) still gets every line, unchanged — the files are
additive.

## Log lines

Level is a label on the line, not a separate file:

```
2026-09-02 10:13:09  INFO    EmailClassifier: llm raw response -> {...}
2026-09-02 10:13:09  DEBUG   db: upsert company data={'name': 'Acme'}
2026-09-02 10:13:09  ERROR   emails: email 42 failed: TimeoutError
```

`RunLogger` exposes `debug / info / warning / error / exception` — thin
pass-throughs to a stdlib logger under the `scales.<name>` tree
(`propagate=True` so lines also reach `combined.log` and the console).

## Sections

`log.section("<method>", **context)` at the top of a request handler or
background task writes a banner into that logger's file, `combined.log`, and
`flow.log`, and sets a `ContextVar` recording the current stage (shown as
`(from: <previous stage>)` in the next banner — a cheap call trace).

Used as a context manager it also records the exit and whether it raised:

```python
with log.section("classify", from_email=from_email, subject=subject):
    ...
# -> flow.log:
#   >>> ENTER EmailClassifier.classify from_email=... subject=...   (from: emails.classify_pending)
#   <<< EXIT  EmailClassifier.classify  (ok)
```

Fire-and-forget form (no exit marker) is used for one-shot events like
`log.section("serve", port=5010)` in `app.py`.

## Where it's wired

`app.py`, `db.py`, `routes/auth.py`, `routes/application.py`,
`routes/emails.py`, and `EmailClassifier.py` all use it. `auth.py` and
`application.py` replaced their `print()` calls; `emails.py` and
`EmailClassifier.py` use `log.section` around the classify / resolve flow so
`flow.log` shows a full "login → sync → classify → resolve" trace across
files.

## Reading a run

- **What ran, in order** → `flow.log`
- **Everything, one timeline** → `combined.log`
- **Just one component** → `db.log`, `EmailClassifier.log`, etc.
- **Most recent run folder** → name is in `LATEST_RUN.txt`
