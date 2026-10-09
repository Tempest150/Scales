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

## Download

Get the latest installer for your system from the **[Releases page](https://github.com/OWNER/REPO/releases/latest)**.

| System  | File to download                             |
|---------|----------------------------------------------|
| Windows | `Scales_x.y.z_x64-setup.exe` (or the `.msi`) |
| macOS   | `Scales_x.y.z_aarch64.dmg`                   |
| Linux   | `.AppImage` or `.deb`                        |

Then run the installer. You do **not** need Python, Node, or Docker, because the backend ships inside the app.

Classification currently depends on a local model, so you will also need:

- [Ollama](https://ollama.com) installed and running, with `deepseek-r1:8b` pulled (`ollama pull deepseek-r1:8b`).
- A PostgreSQL database the backend can reach (currently shared with Libra).

### First launch warnings

Early versions are not code-signed, so your OS may warn you:

- **Windows:** "Windows protected your PC" appears. Click **More info**, then **Run anyway**.
- **macOS:** the app may be blocked as unverified. Right-click the app, choose **Open**, then confirm. If macOS says the app is "damaged", run `xattr -cr /Applications/Scales.app` in Terminal and open it again.
- **Linux:** make the AppImage executable (`chmod +x Scales*.AppImage`) and run it, or install the `.deb` with your package manager.

## Stack

| Layer | Tech |
|---|---|
| Email trigger / ingest | n8n (Gmail Trigger), external email-cleaner service |
| Backend | Quart, Hypercorn, `quart-cors` |
| Classification | Ollama (`deepseek-r1:8b`) over HTTP via `httpx` |
| Database | Postgres via `asyncpg`, shared with Libra |
| Frontend | React 19 + Vite 8 |
| Desktop shell (in progress) | Tauri v2 |

## How the desktop app is packaged

```
┌──────────────────────────── Scales (installed app) ─────────────────────────────┐
│                                                                                 │
│  Tauri shell (Rust)  ──starts──▶  Python backend (frozen exe, "sidecar")        │
│        │                                  ▲                                     │
│        ▼                                  │ HTTP on 127.0.0.1:<random port>     │
│  React frontend (webview)  ───────────────┘                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- The **frontend** (`frontend/`) is a React app built with Vite and displayed in a Tauri webview.
- The **backend** (`backend/`) is a Quart app. For releases it is frozen into a single executable with PyInstaller and bundled into the installer as a Tauri *sidecar*.
- On startup, the Rust side picks a free local port, launches the sidecar with `--port <port>`, and gives that port to the frontend through the `backend_port` command. The frontend then polls `/health` until the backend is ready.
- When the app exits, Rust kills the sidecar. The backend also watches its parent process and shuts itself down if the app dies unexpectedly.
- The backend binds to `127.0.0.1` only, so it is not reachable from other machines.

In development, the backend runs separately (`npm run backend`) on a fixed port, and the Rust side connects to that instead of launching a sidecar.

## Getting started

Prerequisites: Node.js 22+, Python 3 (3.13 is used in CI), [Ollama](https://ollama.com) (with
`deepseek-r1:8b` pulled), and Rust + platform build tools if you're running
the Tauri shell. Details in [Local Dev Setup](wiki/Local-Dev-Setup.md).

Platform notes:

- **Windows:** Visual Studio Build Tools with the "Desktop development with C++" workload, and WebView2 (preinstalled on Windows 11).
- **Linux:** `libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf`.

```
npm install   # installs backend (venv) and frontend deps
npm run dev   # runs the Quart backend + Tauri/Vite dev shell
```

You can also run the pieces separately:

```
npm run backend   # backend only
npm run tauri     # Tauri dev shell (needs the backend already running)
```

> The backend's CORS settings must allow `http://localhost:5173` in development and `http://tauri.localhost`, `https://tauri.localhost`, and `tauri://localhost` in the installed app. The dev port used by the Rust side (`DEV_PORT` in `src-tauri/src/lib.rs`) must match the port in `scripts/run-backend.js`.

## Repo map

```
Scales/
├── backend/                  # Quart app, email classifier, db layer
│   ├── main.py               #   entry point (takes --port, runs the server)
│   └── requirements.txt
├── frontend/                 # React 19 + Vite frontend
├── src-tauri/                # Tauri v2 desktop shell
│   ├── src/lib.rs            #   sidecar launch, port handoff, shutdown
│   ├── tauri.conf.json       #   app config (dev)
│   ├── tauri.release.conf.json  # adds the bundled backend for release builds
│   └── binaries/             #   frozen backend placed here at build time (git-ignored)
├── scripts/                  # dev bootstrap and backend runner scripts
│   └── build-sidecar.js      #   freezes the backend and places it for Tauri
├── docs/diagrams/            # Mermaid diagrams
├── wiki/                     # internal reference docs (architecture, setup, migration plan)
└── .github/workflows/        # CI/notification workflows, plus release.yml
```

## Building an installer locally

```
npm run build
```

This freezes the backend with PyInstaller, copies it to `src-tauri/binaries/scales-backend-<target-triple>[.exe]`, and runs `tauri build` with the release config. Installers are written to `src-tauri/target/release/bundle/`.

Installers can only be built for the OS you are running on. Use the release workflow below to produce all three.

### Test the frozen backend on its own

Before trusting a build, check that the backend runs without Python in the loop:

```powershell
.\dist\scales-backend.exe --port 5055
curl.exe http://127.0.0.1:5055/health
```

You should get `{"ok":true}`. If you see a `ModuleNotFoundError`, add `--hidden-import <module>` to the PyInstaller command in `scripts/build-sidecar.js`.

### Checklist for a release build

1. Install the built app on a machine **without** Python, Node, or Rust (a VM or Windows Sandbox works).
2. Confirm the app loads and talks to its backend.
3. Close the app and confirm no `scales-backend` process is left running.

## Releasing

Releases are built by GitHub Actions (`.github/workflows/release.yml`) when a version tag is pushed.

1. Set `version` in `src-tauri/tauri.conf.json` to the new version.
2. Commit and push your changes.
3. Tag and push:
   ```
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Open the **Actions** tab and wait for the `release` workflow to finish (Windows, macOS, Linux).
5. Open **Releases**, review the **draft** release and its attached installers, then click **Publish release**.

If a build fails, fix the problem, delete the tag, and tag again:

```
git push --delete origin v0.1.0
git tag -d v0.1.0
```

## Troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| `Found version mismatched Tauri packages` | A Rust crate and its npm package are on different minor versions. Run `npx tauri info`, then update the older side (`cargo update -p <crate>` or `npm install <package>@latest`). |
| `You must change the bundle identifier` | Set a unique `identifier` in `src-tauri/tauri.conf.json`. Don't change it after release, since installers and updates rely on it. |
| Build says the sidecar file is missing | Run `node scripts/build-sidecar.js` first, or use `npm run build`, which does it for you. |
| App stuck on the loading screen (release build) | The backend didn't start. Run the bundled `scales-backend` executable by hand with `--port 5055` to see the traceback. |
| CORS errors in the dev console | Add the origin shown in the error to the backend's `allow_origin` list. |
| `scales-backend` still running after closing the app | Check the parent-process watchdog in `backend/main.py`, and that the Rust exit handler kills the sidecar. |
| Classification fails or times out | Make sure Ollama is running and `deepseek-r1:8b` has been pulled. |

## Roadmap

- [ ] Code signing (Windows certificate, Apple Developer ID and notarization)
- [ ] Auto-updates with `tauri-plugin-updater`
- [ ] Intel macOS build

## License

MIT — see [LICENSE](LICENSE).