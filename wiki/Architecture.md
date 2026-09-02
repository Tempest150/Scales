# Architecture

> The flowcharts on this page predate the per-user Gmail OAuth + `messages`
> queue rework and are kept for the target-state comparison. For the flow that
> actually runs today see [[Ingest-Pipeline]] ("Current flow") and
> [[Database-Layer]].

## Earlier server-hosted state (n8n, superseded)

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

- `app.py` — Quart app; registers the `auth`, `emails`, and `application`
  blueprints; CORS locked to `http://localhost:5173`. The `/emails` route
  here is a leftover stub that echoes its body — the real ingest path is the
  `messages` queue.
- `routes/auth.py` — email/password login + register, Google OAuth login.
  When a user has no Gmail connection it redirects the browser to
  imap-checker's `connect/start`; once connected, login fire-and-forgets
  `classify_pending_emails`.
- `routes/emails.py` — `classify_pending_emails` (background queue drain),
  `/api/emails/sync-status` (poll for the "N/M processed" spinner), and
  `resolve_application` (thread- then company-based grouping). See
  [[Database-Layer]].
- `routes/application.py` — `GET /api/application/dashboard`: the user's
  applications joined to `company` and their latest message, plus recent
  enriched `job_list` rows from Libra.
- `EmailClassifier.py` — `Duro`, the Ollama-backed classifier. See
  [[Classification]] and `docs/diagrams/classification_class.md`.
- `db.py` — `Rimiru`, an asyncpg pool + CRUD layer
  (select/upsert/delete/call_function/execute), now used on both the read and
  write paths. See [[Database-Layer]] and `docs/diagrams/db_class.md`.
- `logger.py` — per-run structured logging. See [[Logging]].
- `useCheck.py` — `@require_user`, resolves the session cookie to
  `g.current_user` or returns 401.
- `constants.py` — env config (`PG*`, `SECRET_KEY`, `GOOGLE_CLIENT_ID/SECRET`,
  `FRONTEND_URL`, `EMAIL_ENDPOINT`) via `python-dotenv`, plus a `FetchType`
  enum and an unrelated `format_due_date()` helper.

See [[Diagrams]] for the full index of Mermaid diagrams backing this page.
