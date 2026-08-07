# Architecture

## Current, server-hosted state

This is the path that actually runs against real Gmail traffic today.

```mermaid
flowchart TD
    Gmail[Gmail inbox] -->|polled every minute| N8N[n8n workflow]
    N8N --> Cleaner["email-cleaner service<br/>(sibling container, not in this repo)"]
    N8N -->|"POST /emails<br/>{from, subject, text, user}"| API["Quart backend<br/>backend/app.py<br/>hosted at application.austindwomoh.xyz"]
    API --> Duro["EmailClassifier.Duro<br/>backend/EmailClassifier.py"]
    Duro -->|"POST /api/generate<br/>model: deepseek-r1:8b"| Ollama["Ollama<br/>co-located with the backend"]
    Ollama --> Duro
    Duro --> API
    API -->|"200 JSON classification"| N8N

    DB[("Postgres<br/>shared with Libra")]
    Rimiru["db.py: Rimiru<br/>(pool + CRUD helper)"]
    API -.->|"imported, never called<br/>from /emails"| Rimiru
    Rimiru -.->|not wired up| DB

    style DB stroke-dasharray: 5 5
    style Rimiru stroke-dasharray: 5 5
```

Solid arrows are exercised on every real request. Dashed arrows exist in code
but nothing on the live path calls them — see [[Ingest-Pipeline]] for the
full walkthrough and [[Database-Layer]] for what `Rimiru` can do once it's
actually wired up.

There is no deploy workflow for Scales in `.github/workflows/` (only
`Notify.yaml`, a Discord notifier) — how the hosted backend actually gets
updated isn't automated or documented in this repo. The React frontend
(`frontend/src/App.jsx`) is still the unmodified Vite starter template; it
doesn't call the backend at all yet.

## Target: Tauri desktop state

Where the migration in `to-do.md` is headed. Nothing below is running yet
except the pieces marked "scaffolded" in [[Desktop-Migration]].

```mermaid
flowchart TD
    Gmail[Gmail inbox] -->|"polled every minute"| N8N[n8n workflow]
    N8N --> Cleaner["email-cleaner service"]
    N8N -->|"INSERT into queue table<br/>(not yet designed)"| Queue[("Postgres: pending-classification<br/>queue — shared DB with Libra")]

    subgraph Desktop["User's machine — Tauri app"]
        UI["React frontend<br/>(bundled static assets)"]
        Sidecar["Quart backend, frozen to a single<br/>binary via PyInstaller/Nuitka,<br/>run as a Tauri sidecar process"]
        Settings["Settings screen:<br/>LLM base URL + optional API key + model"]
        UI <--> Sidecar
        Settings --> Sidecar
    end

    Queue -->|"app pulls pending emails on load<br/>(pull vs. push: open question)"| Sidecar
    Sidecar -->|"abstracted LLM client<br/>(OpenAI-compatible shape)"| LLM["User's own LLM:<br/>local Ollama / LM Studio / llama.cpp,<br/>or a hosted API key"]
    LLM --> Sidecar
    Sidecar -->|"write classification result back"| Queue

    style Queue stroke-dasharray: 5 5
    style Settings stroke-dasharray: 5 5
    style LLM stroke-dasharray: 5 5
```

## Backend module map

The backend is four files today:

- `app.py` — Quart app, single `/emails` route, CORS locked to
  `http://localhost:5173` (the Vite/Tauri dev origin).
- `EmailClassifier.py` — `Duro`, the Ollama-backed classifier. See
  [[Classification]] and `docs/diagrams/classification_class.md`.
- `db.py` — `Rimiru`, a generic asyncpg pool + CRUD layer (select/upsert/
  delete/execute), currently unused. See [[Database-Layer]] and
  `docs/diagrams/db_class.md`.
- `constants.py` — reads `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/`PGDATABASE`/
  `SECRET_KEY` from the environment via `python-dotenv`, plus an unrelated
  `format_due_date()` helper and a `FetchType` enum used by `Rimiru.call_function`.

See [[Diagrams]] for the full index of Mermaid diagrams backing this page.
