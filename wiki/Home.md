# Scales Wiki

Internal reference for Scales — a multi-user job-application tracker. Not
user-facing docs; this exists so the actual state of the code (what's wired
up, what's scaffolded, what's still just a plan) doesn't have to be
re-derived from scratch every time.

**What Scales does today:** a user signs in (email/password or Google) and
connects their Gmail through the imap-checker service, which holds the OAuth
token, polls the inbox, cleans each email, and writes it to a shared Postgres
`messages` queue. On login the Quart backend drains that queue: each email is
classified by a local Ollama model (`qwen2.5:7b-instruct`) as job-application
related or not, and if so `resolve_application` attaches it to an
`application` row — grouping by Gmail thread first, then by company — and
advances that application's status. The React dashboard reads applications
(and Libra job postings) back from the backend.

**Where it's headed:** the backend and frontend are being packaged into a
Tauri desktop app so classification runs against *the user's own* LLM
(local or hosted) instead of a server-side Ollama instance. See
[[Desktop-Migration]].

## Pages

- [[Overview]] — what Scales is, why it exists, and how it relates to Libra
- [[Architecture]] — current server-hosted flow and the target Tauri flow
- [[Local-Dev-Setup]] — running the backend, frontend, and Tauri shell locally
- [[Ingest-Pipeline]] — imap-checker queue → `classify_pending_emails` → `resolve_application` (with the old n8n flow as history)
- [[Classification]] — `EmailClassifier.Duro`, the prompt, the verdict gate
- [[Database-Layer]] — `Rimiru` (db.py), the schema, and `resolve_application`
- [[Logging]] — `backend/logger.py`: per-run folders, per-class files, `flow.log`
- [[Desktop-Migration]] — the Tauri migration plan: decided vs. still open
- [[Diagrams]] — index of all Mermaid diagrams in `docs/diagrams`

## Repo map

```
Scales/
├── backend/
│   ├── app.py               # Quart app — registers auth/emails/application blueprints; stub /emails echo route
│   ├── EmailClassifier.py   # Duro: prompt, Ollama call, parse + verdict gate
│   ├── db.py                 # Rimiru: asyncpg pool + CRUD helper — used on the read and write paths
│   ├── logger.py             # per-run structured logging (per-class files, combined.log, flow.log) — see [[Logging]]
│   ├── useCheck.py            # @require_user decorator (session -> g.current_user)
│   ├── routes/
│   │   ├── auth.py            # email/password + Google OAuth login; redirects to imap-checker's Gmail connect
│   │   ├── emails.py          # classify_pending_emails background task, /sync-status, resolve_application
│   │   └── application.py     # GET /api/application/dashboard (applications + Libra jobs)
│   ├── constants.py          # Constants (env config incl. GOOGLE_*, EMAIL_ENDPOINT) + FetchType enum
│   └── requirements.txt      # Quart, quart-cors, asyncpg, authlib, python-dotenv, ...
├── frontend/                 # React 19 + Vite — login + dashboard UI (Dashboardcards, Table, api/client.js)
├── src-tauri/                 # Tauri v2 shell — scaffolded, not yet wired as a sidecar host for the backend
├── scripts/
│   ├── setup.js               # one-shot dev bootstrap (venv, Rust, platform deps, frontend+Tauri CLI) — `npm run setup`
│   ├── install-backend.js     # backend venv + deps, also unconditionally installs Rust — overlaps with setup.js
│   └── run-backend.js         # runs backend/app.py via the venv's python
├── to-do.md                   # Tauri migration plan + open design questions
├── .github/workflows/
│   ├── Notify.yaml             # Discord notifications on push/issue events — no deploy workflow yet
│   └── wiki-sync.yaml          # pushes wiki/ to the GitHub wiki
└── docs/diagrams/              # Mermaid diagrams — see [[Diagrams]]

The **imap-checker** service (Gmail OAuth custody, polling, HTML cleaning,
the `messages` queue; hosted at `email.austindwomoh.xyz`) lives in its own
repo, not here.
```
