# Turning Scales into a Desktop App (Tauri)

## Why
Classification currently runs server-side (Ollama on the droplet). Moving it
client-side means:
- Users can point at whatever LLM they want (local Ollama/LM Studio, or their
  own hosted API key) — no model limits imposed by us.
- The server no longer carries inference load — it only handles
  ingest/sync/DB, which is a big reduction in resource pressure as user count
  grows.

## Why Tauri over Electron
Tauri uses the OS's native webview instead of bundling Chromium + Node, so
the runtime overhead is a few MB instead of 100-200MB before the app does
anything. Since the whole point is relieving memory pressure, we shouldn't
add another heavy runtime on top of the LLM's footprint.

## Steps

### 1. Freeze the Python backend into a binary
Use PyInstaller (or Nuitka for smaller output) to compile the Quart backend
into a single executable. This avoids shipping a Python interpreter/venv
separately — Tauri can spawn the binary like any other process.

### 2. Set it up as a Tauri sidecar
Tauri has a built-in "sidecar" pattern for bundling external binaries
(`tauri.conf.json > bundle > externalBin`). On launch, Tauri starts the
Quart binary on localhost, and the React frontend (built as static assets,
also bundled by Tauri) talks to it over HTTP exactly like it does in dev.

### 3. Move the LLM out of the shared server model
Don't hardcode Ollama. Add a settings screen where the user configures:
- A local Ollama / LM Studio / llama.cpp endpoint (OpenAI-compatible shape), or
- Their own API key for a hosted model (OpenAI, Anthropic, etc.)

The backend's classification step should call an abstracted interface
(base URL + optional key + model name), not a hardcoded Ollama client.

### 4. Handle the Ollama dependency explicitly
Ollama isn't something to bundle inside the app binary — it's a separate
runtime with multi-GB model weights. Either require users to install it
themselves (simplest, keeps the installer small) or detect/prompt for it on
first launch. Don't bundle model weights into the installer.

### 5. Add auto-updates
Use `tauri-plugin-updater`. Host a small JSON manifest (version, changelog,
signed binary URLs) — even a GitHub Releases page works. The app checks on
launch, downloads, verifies the signature, and installs. Generate a signing
keypair with `tauri signer generate` and keep the private key safe — every
build gets signed with it so the app trusts its own updates.

### 6. Build and test the installer per platform
Run `tauri build` to produce a native installer (.dmg, .msi,
.AppImage/.deb). Test on a clean machine without the dev environment —
sidecar path and permission bugs usually show up first there.

## Open design questions (not yet decided)
See the GitHub issue for the pending-classification queue design — details
on queue table, pull-vs-push, multi-device claiming, and writing results
back to Postgres.