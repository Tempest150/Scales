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


def format_due_date(day_num):
    """Convert day number to MM/DD format"""
    if not day_num:
        return None
    # Just return day number formatted - frontend can format as needed
    return f"{day_num:02d}"
