# Local Dev Setup

## Prerequisites

- Node.js (for the root scripts, frontend, and Tauri CLI)
- Python 3 (backend venv — `backend/requirements.txt` was generated against
  Python 3.13)
- [Ollama](https://ollama.com), running locally with `deepseek-r1:8b` pulled
  (`ollama pull deepseek-r1:8b`) — `EmailClassifier.Duro` hardcodes
  `http://localhost:11434` as the model host, so it must be reachable there.
- Rust + platform build tools, if you're launching the Tauri shell (`tauri
  dev`/`tauri build`) — see below.
- A `backend/.env` file with `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`,
  `PGDATABASE`, and `SECRET_KEY` (the same Postgres instance a Libra
  deployment would point at). Not currently required for the `/emails` route
  to work, since nothing calls `Rimiru` yet — but `constants.py` loads it via
  `load_dotenv()` regardless, and `db.py` will fail if you exercise it
  without these set.

## Two ways to install dependencies

**`node scripts/setup.js`** is a more thorough, platform-aware one-shot
bootstrap: backend venv + deps, Rust via `winget`/`rustup`-curl/existing-check
depending on OS, platform build deps (WebView2 + VS Build Tools on Windows,
webkit2gtk + build-essential on Linux, Xcode CLT on macOS), then frontend deps
plus `@tauri-apps/cli`/`@tauri-apps/api`. **It isn't wired to any `npm run`
script** — you have to invoke it directly. It duplicates the venv/backend
setup that `install-backend.js` already does; the two aren't kept in sync
with each other today, so if one changes (a new pip dependency, say) the
other can silently drift.



**`npm install` from the repo root** runs `install:backend` +
`install:frontend` in parallel:
- `install:backend` → `scripts/install-backend.js`: creates `backend/venv`,
  installs `requirements.txt`, then unconditionally runs
  `curl ... sh.rustup.rs | sh` to install Rust — with no OS check, so on
  Windows this depends on having a `sh` on PATH (e.g. via Git Bash); it isn't
  guarded the way `scripts/setup.js`'s Rust step is.
- `install:frontend` → `cd frontend && npm install`.



## Running it

From the repo root:

```
npm run dev
```

This runs two things concurrently (via `concurrently`, prefixed `backend`/`tauri`):

- `npm run backend` → `node scripts/run-backend.js`, which runs
  `backend/venv/Scripts/python app.py` (or `bin/python` on macOS/Linux) —
  starts the Quart dev server on `http://localhost:5000` (`app.run(debug=True,
  port=5000)` in `app.py`).
- `npm run tauri` → `tauri dev`, which (per `src-tauri/tauri.conf.json`) runs
  `npm run dev --prefix frontend` to start the Vite dev server, waits for
  `http://localhost:5173`, and opens a native Tauri window pointed at it.

CORS in `app.py` is hardcoded to allow only `http://localhost:5173` — this
matches Tauri's dev `devUrl`, but note it would need updating if that origin
ever changes (e.g. a different dev port, or Tauri's production asset
protocol origin).

## Building a desktop binary

```
npm run build
```

Runs `tauri build`, which builds the frontend (`vite build` → `frontend/dist`)
and bundles it with the Tauri shell into a native installer. **This does not
currently bundle the Python backend** — there's no `externalBin`/sidecar
entry in `tauri.conf.json` yet, so a built app has no way to reach a backend
unless one happens to be running separately. See [[Desktop-Migration]] for
the plan to freeze the backend into a sidecar binary.
