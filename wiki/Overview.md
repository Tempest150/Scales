# Overview

## What Scales is

Scales is a multi-user job-application tracker. The core idea: instead of
manually logging every application, interview invite, and rejection, Scales
watches a user's Gmail inbox, uses an LLM to recognize which incoming emails
are job-application status updates, and extracts the company, role, and
status from them automatically.

From the README:

> Email-driven job application tracker that auto-classifies status updates
> and syncs with Libra

## Why it exists

Scales is a sister project to **Libra** (a job-listing aggregation/enrichment
API — see `https://github.com/Tempest150/libra`). Libra answers "what jobs
exist"; Scales answers "what happened to the jobs I applied to." They're
separate codebases with their own migrations, but intentionally share the
same Postgres instance: Scales' `application` table has FKs straight into
Libra's `company` and `job_list` tables, so a tracked application can be
linked back to the original posting. See [[Database-Layer]] for the schema
and what's actually wired up today (the FKs exist in the live schema; nothing
in the current codebase populates them yet).

## How it works, today

1. **n8n** polls Gmail every minute for new mail.
2. n8n forwards the email's HTML through a small **email-cleaner** service to
   get plain text, then POSTs `{from, subject, text, user}` to the Scales
   **Quart backend**'s `/emails` route.
3. The backend classifies the email text via a local **Ollama** model
   (`deepseek-r1:8b`), asking it whether the email is job-application-related,
   and if so, extracting `company_name`, `role_title`, and `status`.
4. The classification is returned to n8n as the HTTP response.

That's the whole pipeline as it exists right now — see [[Ingest-Pipeline]] for
the detailed walkthrough and the gaps in it (notably: nothing is persisted to
Postgres yet).

## Where it's going

The project is mid-migration to a **Tauri desktop app**, so that:

- Classification runs against *the user's own* LLM (local Ollama/LM Studio,
  or their own hosted API key) instead of a shared server-side Ollama
  instance the project would otherwise have to pay to run for every user.
- The server's job shrinks to ingest + sync + DB, removing the LLM inference
  load as the main scaling bottleneck.

See [[Desktop-Migration]] for the plan and what's decided vs. still open.

## Stack, at a glance

| Layer | Tech |
|---|---|
| Email trigger / ingest | n8n (Gmail Trigger), external email-cleaner service |
| Backend | Quart (async Flask-like framework), Hypercorn, `quart-cors` |
| Classification | Ollama, `deepseek-r1:8b`, called over HTTP via `httpx` |
| Database | Postgres via `asyncpg`, shared with Libra |
| Frontend | React 19 + Vite 8 (currently the default Vite template) |
| Desktop shell (in progress) | Tauri v2 |
