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
linked back to the original posting. See [[Database-Layer]] for the schema.
`application.company` is populated today; `application.job_id` is not (no
`job_list` matching exists yet).

## How it works, today

1. A user signs in (email/password or Google) and connects Gmail. The
   **imap-checker** service (separate repo, `email.austindwomoh.xyz`) holds
   the OAuth refresh token, polls the inbox, renders + strips each email to
   plain text, and inserts it into a shared Postgres **`messages`** queue as
   `status = 'pending'`.
2. On login the **Quart backend** fire-and-forgets `classify_pending_emails`,
   which pulls the user's pending rows and classifies each via a local
   **Ollama** model (`qwen2.5:7b-instruct`) — job-application related or not,
   and if so `company_name` / `role_title` / `status`.
3. Non-related → sender added to `ignore_list`, row deleted. Related →
   `resolve_application` attaches it to an `application` row (matching by
   Gmail thread, then by canonicalized company name) and moves that
   application's status forward.
4. The **React dashboard** polls `/api/emails/sync-status` for progress, then
   reads applications + Libra job postings from `/api/application/dashboard`.

See [[Ingest-Pipeline]] and [[Classification]] for the detailed walkthrough.

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
| Email ingest | imap-checker service (Gmail API + OAuth, Playwright HTML clean) → Postgres `messages` queue |
| Backend | Quart (async Flask-like framework), `quart-cors`, `authlib` for Google OAuth |
| Classification | Ollama, `qwen2.5:7b-instruct`, called over HTTP via `httpx` |
| Database | Postgres via `asyncpg`, shared with Libra |
| Frontend | React 19 + Vite — login + dashboard UI |
| Desktop shell (in progress) | Tauri v2 |
