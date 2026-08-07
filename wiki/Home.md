# Scales Wiki

Internal reference for Scales — a multi-user job-application tracker. Not
user-facing docs; this exists so the actual state of the code (what's wired
up, what's scaffolded, what's still just a plan) doesn't have to be
re-derived from scratch every time.

**What Scales does today:** n8n watches a Gmail inbox, forwards each new
email through a small cleaning service and then to a Quart backend, which
classifies it via a local Ollama model (`deepseek-r1:8b`) as job-application-related
or not — and if so, extracts company, role, and status. The classification
result is currently returned to n8n and **not** persisted anywhere.

**Where it's headed:** the backend and frontend are being packaged into a
Tauri desktop app so classification runs against *the user's own* LLM
(local or hosted) instead of a server-side Ollama instance, with n8n writing
to a shared Postgres queue (same database Libra uses) instead of calling the
backend directly. See [[Desktop-Migration]].

## Pages

- [[Overview]] — what Scales is, why it exists, and how it relates to Libra
- [[Architecture]] — current server-hosted flow and the target Tauri flow
- [[Local-Dev-Setup]] — running the backend, frontend, and Tauri shell locally
- [[Ingest-Pipeline]] — the n8n → email-cleaner → Quart → Ollama request path
- [[Classification]] — `EmailClassifier.Duro`, the prompt, and its Ollama dependency
- [[Database-Layer]] — `Rimiru` (db.py), the shared Postgres, and schema status
- [[Desktop-Migration]] — the Tauri migration plan: decided vs. still open
- [[Diagrams]] — index of all Mermaid diagrams in `docs/diagrams`

## Repo map

```
Scales/
├── backend/
│   ├── app.py               # Quart app — single POST /emails route
│   ├── EmailClassifier.py   # Duro: builds prompt, calls Ollama, parses response
│   ├── db.py                 # Rimiru: asyncpg pool + CRUD helper — not called from app.py yet
│   ├── constants.py          # Constants (env-var config) + FetchType enum + format_due_date()
│   └── requirements.txt      # Quart, quart-cors, asyncpg, Hypercorn, python-dotenv, ...
├── frontend/                 # React 19 + Vite 8 — still the default Vite template, no product UI yet
├── src-tauri/                 # Tauri v2 shell — scaffolded, not yet wired as a sidecar host for the backend
├── scripts/
│   ├── setup.js               # full one-shot dev bootstrap (venv, Rust, platform deps, frontend+Tauri CLI) — not wired to any npm script
│   ├── install-backend.js     # backend venv + deps, also unconditionally installs Rust — overlaps with setup.js
│   └── run-backend.js         # runs backend/app.py via the venv's python
├── to-do.md                   # Tauri migration plan + open design questions
├── .github/workflows/
│   └── Notify.yaml             # Discord notifications on push/issue events — no deploy workflow yet
└── docs/diagrams/              # Mermaid diagrams — see [[Diagrams]]
```
