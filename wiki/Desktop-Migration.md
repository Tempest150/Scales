# Desktop Migration (Tauri)

Source: `to-do.md` in the repo root, plus what's actually scaffolded in
`src-tauri/` and `package.json` today. See [[architecture_target|Architecture]]
for the end-state diagram.

## Why

Classification currently runs server-side (Ollama on the hosted droplet).
Moving it client-side means:

- Users can point at whatever LLM they want (local Ollama/LM Studio, or their
  own hosted API key) — no model limits imposed by the project.
- The server no longer carries inference load — it only handles
  ingest/sync/DB, a big reduction in resource pressure as user count grows.

## Why Tauri over Electron

Tauri uses the OS's native webview instead of bundling Chromium + Node, so
runtime overhead is a few MB instead of 100-200MB before the app does
anything. Since the whole point is relieving memory pressure, adding another
heavy runtime on top of the LLM's own footprint would work against the goal.

## Status: decided vs. scaffolded vs. open

| Step | Status |
|---|---|
| 1. Freeze the Quart backend into a binary (PyInstaller/Nuitka) | **Not started.** `scripts/run-backend.js` still runs the backend via the venv's Python directly. |
| 2. Set it up as a Tauri sidecar (`externalBin`) | **Not started.** `src-tauri/tauri.conf.json` has no `externalBin` entry. `src-tauri/` itself *is* scaffolded — default Tauri v2 shell, window config, no custom Rust commands yet. |
| 3. Move the LLM off hardcoded Ollama — settings screen, abstracted client (base URL + optional key + model) | **Not started.** `EmailClassifier.Duro` still hardcodes `http://localhost:11434` / `deepseek-r1:8b`. `App.jsx` is still the default Vite template — no settings UI exists. |
| 4. Handle the Ollama dependency explicitly (require separate install vs. detect/prompt; don't bundle model weights) | **Decided, not implemented.** Direction chosen (don't bundle weights); no detection/prompt UI built. |
| 5. Auto-updates via `tauri-plugin-updater` + signed release manifest | **Not started.** No plugin installed, no signing keypair generated. |
| 6. Build and test installers per platform, on a clean machine | **Not started** — blocked on steps 1–2 (no working sidecar to bundle yet). |
| Root dev tooling (`npm run dev` runs backend + `tauri dev` concurrently) | **Scaffolded and working** for local dev — see [[Local-Dev-Setup]]. |
| `scripts/setup.js` (full one-shot environment bootstrap) | **Scaffolded**, but not wired to any `npm run` script, and duplicates venv setup already done by `scripts/install-backend.js` — see [[Local-Dev-Setup]]. |

## Open design questions (not yet decided)

Per `to-do.md`, the pending-classification queue design is still open:

- Queue table shape — what columns, in the shared Postgres instance.
- **Pull vs. push** — does the desktop app poll the queue, or does something
  notify it?
- **Multi-device claiming** — if a user runs the app on two machines, how do
  they avoid double-classifying (or racing to write results for) the same
  queued email?
- Writing results back to Postgres — the shape of that write, and how it
  reconciles with [[Database-Layer]]'s company+role/emails-array model.

These are tracked as a GitHub issue per `to-do.md`; check there for the
latest state rather than assuming this page is current.

## Sequencing note

n8n today POSTs directly to the hosted Quart backend's `/emails` route (see
[[Ingest-Pipeline]]). The queue-based design means that call is replaced with
an `INSERT` into Postgres — which itself is a change to a system (the n8n
workflow) that lives outside this repo, so it isn't something a Scales PR
alone can complete.
