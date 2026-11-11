from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()


class FetchType(Enum):
    FETCH = "fetch"
    FETCHVAL = "fetchval"
    FETCHROW = "fetchrow"


class Constants:
    PGHOST = os.getenv("PGHOST")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGUSER = os.getenv("PGUSER")
    PGPASSWORD = os.getenv("PGPASSWORD")
    PGDATABASE = os.getenv("PGDATABASE")
    SECRET_KEY = os.getenv("SECRET_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    # Comma-separated list of origins allowed by CORS (defaults to FRONTEND_URL).
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", FRONTEND_URL).split(",") if o.strip()]
    # libpq-style: disable | require | verify-ca | verify-full (default). See Rimiru._ssl_context.
    PGSSLMODE = os.getenv("PGSSLMODE", "verify-full").strip().lower()
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    # Pin the OAuth callback when the request Host isn't what the browser sees (e.g. behind the Docker proxy).
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI") or None
    API_HOST =os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "5010"))
    # Debug mode = auto-reload + tracebacks in responses. Set API_DEBUG=0 anywhere that isn't a dev box.
    API_DEBUG = os.getenv("API_DEBUG", "1").strip().lower() not in ("0", "false", "no", "off")
    EMAIL_ENDPOINT ="https://email.austindwomoh.xyz/"

def format_due_date(day_num):
    """Convert day number to MM/DD format"""
    if not day_num:
        return None
    # Just return day number formatted - frontend can format as needed
    return f"{day_num:02d}"
