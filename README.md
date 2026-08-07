# Scales

Email-driven job application tracker that auto-classifies status updates and syncs with [Libra](https://github.com/Tempest150/libra).

## What it does

n8n watches a Gmail inbox and forwards each new email through a small
cleaning service to a Quart backend, which classifies it via a local Ollama
model (`deepseek-r1:8b`) as job-application-related or not — and if so,
extracts the company, role, and status. The project is mid-migration to a
Tauri desktop app so classification runs against each user's own LLM instead
of a shared server-side one.

For the full picture of what's actually wired up vs. still planned, see the
[wiki](wiki/Home.md) — start with [Overview](wiki/Overview.md) and
[Architecture](wiki/Architecture.md).

## Stack

| Layer | Tech |
|---|---|
| Email trigger / ingest | n8n (Gmail Trigger), external email-cleaner service |
| Backend | Quart, Hypercorn, `quart-cors` |
| Classification | Ollama (`deepseek-r1:8b`) over HTTP via `httpx` |
| Database | Postgres via `asyncpg`, shared with Libra |
| Frontend | React 19 + Vite 8 |
| Desktop shell (in progress) | Tauri v2 |

## Getting started

Prerequisites: Node.js, Python 3, [Ollama](https://ollama.com) (with
`deepseek-r1:8b` pulled), and Rust + platform build tools if you're running
the Tauri shell. Details in [Local Dev Setup](wiki/Local-Dev-Setup.md).

```
npm install   # installs backend (venv) and frontend deps
npm run dev   # runs the Quart backend + Tauri/Vite dev shell
```

`npm run build` produces a native installer via `tauri build`.

## Repo map

```
Scales/
├── backend/        # Quart app, email classifier, db layer
├── frontend/        # React 19 + Vite frontend
├── src-tauri/        # Tauri v2 desktop shell
├── scripts/          # dev bootstrap and backend runner scripts
├── docs/diagrams/    # Mermaid diagrams
├── wiki/              # internal reference docs (architecture, setup, migration plan)
└── .github/workflows/ # CI/notification workflows
```

## License

MIT — see [LICENSE](LICENSE).
