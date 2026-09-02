"""Per-run, per-class logging for the Scales backend.

Layout
------
Every process start creates its own folder so runs never overwrite each other
(the Quart reloader spawns two processes -- each gets its own folder):

    backend/logs/run_<YYYYMMDD-HHMMSS>_pid<pid>/
        <ClassName>.log   one file per class / module that logs
        combined.log      every line from every class, interleaved
        flow.log          just the section headers -- a high-level trace of
                          which stage ran, in order, with enter/exit markers

``backend/logs/LATEST_RUN.txt`` always points at the newest run folder.

The console keeps printing every line (stdout), unchanged.

Log lines
---------
The level is a label on each line, not a separate file:

    2026-09-02 10:13:09  INFO    EmailClassifier: llm raw response -> {...}
    2026-09-02 10:13:09  DEBUG   db: upsert company data={'name': 'Acme'}
    2026-09-02 10:13:09  ERROR   emails: email 42 failed: TimeoutError

Sections
--------
Call ``log.section("<method>", **context)`` at the top of a class's main
method. It writes a header banner into that class's own file, into
combined.log and into flow.log, so you can see exactly where each stage
starts and follow the flow across files. Used as a context manager it also
records where the stage ends:

    with log.section("classify", from_email=from_email):
        ...

    # or fire-and-forget (no exit marker):
    log.section("serve", port=5010)
"""

from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path

LOG_ROOT = Path(__file__).resolve().parent / "logs"

_RUN_STARTED = datetime.now()
_RUN_ID = f"run_{_RUN_STARTED:%Y%m%d-%H%M%S}_pid{os.getpid()}"
RUN_DIR = LOG_ROOT / _RUN_ID

_ROOT_NAME = "scales"
_FMT = "%(asctime)s  %(levelname)-7s %(sclass)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

# The stage currently in effect (``<class>.<method>``). Cosmetic -- shown in
# section banners and flow.log so you can see what ran before what.
_current_process: ContextVar[str] = ContextVar("scales_process", default="startup")

_loggers: dict[str, "RunLogger"] = {}
_root_ready = False


class _Formatter(logging.Formatter):
    """Formatter that exposes the short class name as ``%(sclass)s``."""

    def format(self, record: logging.LogRecord) -> str:
        record.sclass = record.name.split(".")[-1]
        return super().format(record)


def _ensure_root() -> None:
    global _root_ready
    if _root_ready:
        return

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    fmt = _Formatter(_FMT, _DATEFMT)

    root = logging.getLogger(_ROOT_NAME)
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.propagate = False

    combined = logging.FileHandler(RUN_DIR / "combined.log", encoding="utf-8")
    combined.setFormatter(fmt)
    combined.setLevel(logging.DEBUG)
    root.addHandler(combined)

    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(logging.DEBUG)
    root.addHandler(console)

    try:
        (LOG_ROOT / "LATEST_RUN.txt").write_text(
            f"{_RUN_ID}\nstarted {_RUN_STARTED.isoformat()}\n", encoding="utf-8"
        )
    except OSError:
        pass

    _root_ready = True


def _append(path: Path, text: str) -> None:
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    except OSError:
        pass


class _Section:
    """Returned by :meth:`RunLogger.section`. Optionally a context manager."""

    def __init__(self, owner: "RunLogger", stage: str, previous: str):
        self._owner = owner
        self._stage = stage
        self._previous = previous

    def __enter__(self) -> "_Section":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        stamp = datetime.now().strftime(_DATEFMT)
        outcome = "ok" if exc_type is None else f"{exc_type.__name__}: {exc}"
        _append(RUN_DIR / "flow.log", f"{stamp}  <<< EXIT  {self._stage}  ({outcome})\n")
        self._owner._raw(f"{'-' * 78}\n{stamp}  <<< EXIT {self._stage}  ({outcome})\n{'-' * 78}")
        _current_process.set(self._previous)


class RunLogger:
    """Thin wrapper over a stdlib logger that owns one per-class file."""

    def __init__(self, name: str):
        _ensure_root()
        self.name = name
        self._log = logging.getLogger(f"{_ROOT_NAME}.{name}")
        self._log.setLevel(logging.DEBUG)
        self._log.propagate = True  # also lands in combined.log + console

        self._file = RUN_DIR / f"{name}.log"
        tag = f"scales:{self._file}"
        if not any(getattr(h, "_scales_tag", None) == tag for h in self._log.handlers):
            fh = logging.FileHandler(self._file, encoding="utf-8")
            fh.setFormatter(_Formatter(_FMT, _DATEFMT))
            fh.setLevel(logging.DEBUG)
            fh._scales_tag = tag  # type: ignore[attr-defined]
            self._log.addHandler(fh)

    # -- level-labelled lines -------------------------------------------------
    def debug(self, msg, *args, **kwargs):
        self._log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log.exception(msg, *args, **kwargs)

    # -- raw writer used for section banners --------------------------------
    def _raw(self, text: str) -> None:
        block = text if text.endswith("\n") else text + "\n"
        _append(self._file, block)
        _append(RUN_DIR / "combined.log", block)
        print(block, end="", file=sys.stdout, flush=True)

    # -- section header ----------------------------------------------------
    def section(self, label: str, **context) -> _Section:
        """Mark that work has entered ``<this class>.<label>``.

        Drops a header banner into this class's file, combined.log and
        flow.log. Use ``with log.section(...):`` to also record the exit.
        """
        previous = _current_process.get()
        stage = f"{self.name}.{label}"
        _current_process.set(stage)

        stamp = datetime.now().strftime(_DATEFMT)
        extra = ("  " + " ".join(f"{k}={v}" for k, v in context.items())) if context else ""
        bar = "=" * 78
        self._raw(f"{bar}\n{stamp}  >>> {stage}{extra}   (from: {previous})\n{bar}")
        _append(RUN_DIR / "flow.log", f"{stamp}  >>> ENTER {stage}{extra}   (from: {previous})\n")
        return _Section(self, stage, previous)


def get_logger(name: str | None = None) -> RunLogger:
    """Return the :class:`RunLogger` for ``name`` (one file per distinct name)."""
    short = (name or "app").split(".")[-1] or "app"
    if short == "__main__":
        short = "app"
    if short not in _loggers:
        _loggers[short] = RunLogger(short)
    return _loggers[short]


def current_process() -> str:
    return _current_process.get()


# Configure immediately so every module shares this run's folder.
_ensure_root()
