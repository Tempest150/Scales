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
| 3. Move the LLM off hardcoded Ollama — settings screen, abstracted client (base URL + optional key + model) | **Not started.** `EmailClassifier.Duro` still hardcodes `http://localhost:11434` / `qwen2.5:7b-instruct`. No settings UI exists (the frontend now has login + dashboard screens, but nothing for LLM config). |
| 4. Handle the Ollama dependency explicitly (require separate install vs. detect/prompt; don't bundle model weights) | **Decided, not implemented.** Direction chosen (don't bundle weights); no detection/prompt UI built. |
| 5. Auto-updates via `tauri-plugin-updater` + signed release manifest | **Not started.** No plugin installed, no signing keypair generated. |
| 6. Build and test installers per platform, on a clean machine | **Not started** — blocked on steps 1–2 (no working sidecar to bundle yet). |
| Root dev tooling (`npm run dev` runs backend + `tauri dev` concurrently) | **Scaffolded and working** for local dev — see [[Local-Dev-Setup]]. |
| `scripts/setup.js` (full one-shot environment bootstrap) | **Scaffolded**, wired as `npm run setup`; still duplicates venv setup already done by `scripts/install-backend.js` — see [[Local-Dev-Setup]]. |

## Queue design — partly resolved

The pending-classification queue now exists: the **imap-checker** service
`INSERT`s cleaned emails into the shared `messages` table
(`status = 'pending'`), and the Quart backend drains it via
`classify_pending_emails` on login (see [[Ingest-Pipeline]] and
[[Database-Layer]]). Ingest no longer depends on n8n.

Still open:

- **Pull vs. push** — today it's pull, and only on login. Nothing re-checks
  while the app is open or notifies it of new mail.
- **Multi-device claiming** — `classify_pending_emails` has no per-row lock or
  claim, so two concurrent runs for the same user (two devices, or a fast
  re-login) would classify the same rows twice.
- When classification moves client-side, the Ollama call in
  `EmailClassifier.Duro` is what the sidecar runs against the user's own LLM;
  `resolve_application` (the DB write) can stay server-side or move with it —
  not decided.
