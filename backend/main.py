# backend/main.py
import argparse, asyncio, multiprocessing, os, threading, time
import psutil
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart_cors import cors
from app import app  # your Quart app

app = cors(app, allow_origin=[
    "http://tauri.localhost", "https://tauri.localhost", "tauri://localhost"
])

@app.get("/health")
async def health():
    return {"ok": True}

def watch_parent():
    # If Tauri kills us or dies, don't linger as an orphan
    parent = psutil.Process(os.getppid())
    while parent.is_running():
        time.sleep(2)
    os._exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    args = ap.parse_args()

    threading.Thread(target=watch_parent, daemon=True).start()

    cfg = Config()
    cfg.bind = [f"127.0.0.1:{args.port}"]
    asyncio.run(serve(app, cfg))