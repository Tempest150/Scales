# Scales

Email-driven job application tracker that auto-classifies status updates and syncs with [Libra](https://github.com/Tempest150/libra).

## What it does

n8n watches a Gmail inbox and forwards each new email through a small
cleaning service to a Quart backend, which classifies it via a local Ollama
model (`qwen2.5:7b-instruct`) as job-application-related or not — and if so,
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
| Classification | Ollama (`qwen2.5:7b-instruct`) over HTTP via `httpx` |
| Database | Postgres via `asyncpg`, shared with Libra |
| Frontend | React 19 + Vite 8 |
| Desktop shell (in progress) | Tauri v2 |

## Getting started

Prerequisites: Node.js, Python 3, [Ollama](https://ollama.com) (with
`qwen2.5:7b-instruct` pulled), and Rust + platform build tools if you're running
the Tauri shell. Details in [Local Dev Setup](wiki/Local-Dev-Setup.md).

```
npm install   # installs backend (venv) and frontend deps
npm run dev   # runs the Quart backend + Tauri/Vite dev shell
```

`npm run build` produces a native installer via `tauri build`.

### Running with Docker

Only Docker is needed — no local Python/Node/Rust. You get the web UI in a
browser (the Tauri desktop shell isn't containerised).

```
cp backend/.env.example backend/.env   # fill in the shared DB + Google creds (ask a maintainer)
docker compose up --build
```

- UI: http://localhost:5173 · API: http://localhost:5010
- The API connects to the shared Postgres in `backend/.env`. Each developer
  should get their own limited DB user, and schema changes go through
  migrations. See [db/README.md](db/README.md).
- Source is bind-mounted, so backend and frontend both hot-reload. Logs land in
  `backend/logs/` on your machine.
- Ollama: by default the container uses Ollama running on your host
  (`host.docker.internal:11434`). To run it in Docker instead:
  `OLLAMA_HOST=http://ollama:11434 docker compose --profile ollama up`, then
  `docker compose exec ollama ollama pull qwen2.5:7b-instruct`.
- Google sign-in redirects to `http://localhost:5010/api/auth/google/callback`,
  which must be listed as an authorised redirect URI in the Google OAuth client.

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
