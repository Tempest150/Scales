import re
from datetime import datetime

import httpx
from quart import Blueprint, jsonify, g

from constants import Constants
from db import Rimiru
from logger import get_logger
from useCheck import require_user
from EmailClassifier import Duro

emails_bp = Blueprint("emails", __name__)
log = get_logger("emails")

# user_id -> {"status": "idle"|"syncing"|"done"|"error", "total": int, "completed": int, "error": str|None}
_sync_progress = {}


@emails_bp.route('/api/emails/sync-status', methods=['GET'])
@require_user
async def sync_status():
    progress = _sync_progress.get(g.current_user['id'], {
        "status": "idle", "total": 0, "completed": 0, "failed": 0, "error": None,
    })
    return jsonify(progress)


async def classify_pending_emails(user_id):
    """Fetch a user's pending emails, classify them, and store application-related ones.

    Runs as a fire-and-forget background task after login, not as a request handler,
    so it has no request/session context of its own — user_id is passed in directly.
    Updates _sync_progress as it goes so the frontend can poll /api/emails/sync-status
    and drive a "3/10 processed" style spinner.
    """
    with log.section("classify_pending", user_id=user_id):
        _sync_progress[user_id] = {"status": "syncing", "total": 0, "completed": 0,"failed": 0, "error": None}
        try:
            log.info("user=%s starting classification", user_id)
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{Constants.EMAIL_ENDPOINT}pending_emails", params={"user_id": user_id})
                resp.raise_for_status()
                pending_emails = resp.json()

            log.info("user=%s fetched %s pending email(s) from imap-checker", user_id, len(pending_emails))
            _sync_progress[user_id]["total"] = len(pending_emails)
            db = await Rimiru.shion()
            classifier = Duro()
            application_related = {}
            clear = []
            for email in pending_emails:
                email_id = email.get("id")
                try:
                    text = email.get("text", "")
                    subject = email.get("subject", "")
                    from_email = email.get("from", "")
                    log.info("user=%s classifying email=%s from=%s subject=%r", user_id, email_id, from_email, subject)
                    classification = await classifier.classify(text, from_email, subject)
                    email["classification"] = classification
                    log.info("user=%s email=%s -> %s", user_id, email_id, classification)

                    if classification.get("is_application_related"):
                        application_id = await resolve_application(db, user_id, email, classification)
                        application_related[email_id] = {
                            "id": email_id,
                            "classification": classification,
                            "status": "classified",
                            "processed_at": datetime.utcnow()
                        }
                        log.info("user=%s email=%s stored as application-related (application_id=%s)", user_id, email_id, application_id)
                    else:
                        clear.append(email_id)
                        row = await db.upsert(table="ignore_list", data={"email": from_email}, conflict_column="email")
                        log.info("user=%s email=%s not application-related; added %s to ignore_list -> %s", user_id, email_id, from_email, row)
                except Exception as e:
                    _sync_progress[user_id]["failed"] += 1
                    log.error("user=%s email=%s failed: %s: %r", user_id, email_id, type(e).__name__, e)
                # leave this email as pending — don't add to either bucket, so it's retried next sync
                _sync_progress[user_id]["completed"] += 1

            if clear:
                deleted = await db.delete(table="messages", filters={"id": list(clear)})
                log.info("user=%s deleted %s cleared message row(s)", user_id, len(deleted))

            _sync_progress[user_id]["status"] = "done"
            log.info("user=%s run complete: classified=%s cleared=%s failed=%s",
                     user_id, len(application_related), len(clear), _sync_progress[user_id]["failed"])
        except Exception as e:
            _sync_progress[user_id]["status"] = "error"
            _sync_progress[user_id]["error"] = f"{type(e).__name__}: {e}"
            log.exception("user=%s classification run failed: %s", user_id, type(e).__name__)

# How far along the pipeline each status sits. A later email only ever moves an
# application forward — an "interview" email that arrives after we've already
# recorded "offer" shouldn't demote it. rejected/offer are both terminal.
_STATUS_RANK = {
    "applied": 0,
    "ghosted": 1,
    "oa": 1,
    "interview": 2,
    "rejected": 3,
    "offer": 3,
}

# Trailing legal-entity suffixes an LLM sprinkles inconsistently onto the same
# employer ("Google", "Google LLC", "Google, Inc.") — stripped so they all
# resolve to one company row.
_COMPANY_SUFFIX_RE = re.compile(
    r"[,\s]+(?:inc|incorporated|llc|l\.l\.c\.|ltd|limited|corp|corporation|"
    r"co|company|gmbh|plc|s\.a\.|s\.l\.|ag|bv|pvt|holdings?)\.?\s*$",
    re.IGNORECASE,
)


def _canonical_company(name: str | None) -> str:
    """Collapse the many ways the same employer gets written down to one string."""
    n = re.sub(r"\s+", " ", (name or "").strip())
    prev = None
    while prev != n:  # strip stacked suffixes, e.g. "Foo Co, Ltd"
        prev = n
        n = _COMPANY_SUFFIX_RE.sub("", n).strip()
    return n


async def _resolve_company_id(conn: Rimiru, company_name: str | None):
    canon = _canonical_company(company_name)
    if not canon:
        return None
    rows = await conn.execute(
        "SELECT id FROM company WHERE lower(name) = lower($1) ORDER BY id LIMIT 1",
        params=[canon],
    )
    if rows:
        return rows[0]["id"]
    created = await conn.execute(
        """INSERT INTO company (name) VALUES ($1)
           ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
           RETURNING id""",
        params=[canon],
    )
    return created[0]["id"] if created else None


async def _link_message(conn: Rimiru, email_id, application_id):
    r = await conn.execute(
        "UPDATE messages SET application_id = $1, status = 'classified' WHERE id = $2",
        params=[application_id, email_id],
        fetch=False,
    )
    if r == "UPDATE 0":
        log.warning("no messages row updated for email_id=%s", email_id)


async def _advance_status(conn: Rimiru, application_id, new_status: str):
    """Move the application's status forward, never backward."""
    if new_status not in _STATUS_RANK:
        return
    rows = await conn.execute(
        "SELECT status FROM application WHERE id = $1", params=[application_id]
    )
    current = rows[0]["status"] if rows else None
    if current is not None and _STATUS_RANK.get(new_status, -1) <= _STATUS_RANK.get(current, -1):
        log.info("application=%s keeping status=%s over incoming=%s", application_id, current, new_status)
        return
    await conn.execute(
        """UPDATE application
           SET status = $2, status_changed_at = now(), updated_at = now()
           WHERE id = $1""",
        params=[application_id, new_status],
        fetch=False,
    )
    log.info("application=%s status %s -> %s", application_id, current, new_status)


async def resolve_application(conn: Rimiru, user_id: str, email: dict, classification: dict):
    with log.section("resolve_application", user_id=user_id, email_id=email.get("id")):
        try:
            thread_id = email.get("gmail_thread_id")
            company_name = classification.get("company_name")
            role_title = classification.get("role_title")
            new_status = (classification.get("status") or "applied").lower()
            sender_email = email.get("from")

            # 1. Same Gmail conversation as an email we've already filed?
            #    This is what stops a recruiter's personal-address reply, or an
            #    OA email from an assessment vendor, from spawning a second
            #    application for a process we already track.
            if thread_id:
                prior = await conn.execute(
                    """SELECT application_id FROM messages
                       WHERE user_id = $1 AND gmail_thread_id = $2
                         AND application_id IS NOT NULL
                       ORDER BY received_at DESC
                       LIMIT 1""",
                    params=[user_id, thread_id],
                )
                if prior:
                    application_id = prior[0]["application_id"]
                    await _link_message(conn, email.get("id"), application_id)
                    await _advance_status(conn, application_id, new_status)
                    log.info("thread=%s matched existing application=%s", thread_id, application_id)
                    return application_id

            # 2. No thread match — fall back to one application per (user, company).
            #    That needs a company name we can pin down.
            if not company_name:
                log.info("no thread match and no company_name; leaving email pending")
                return None

            company_id = await _resolve_company_id(conn, company_name)
            if not company_id:
                log.warning("could not resolve company for name=%r", company_name)
                return None
            log.info("company name=%r -> id=%s", company_name, company_id)

            existing = await conn.execute(
                """SELECT id FROM application
                   WHERE user_id = $1 AND company = $2
                   ORDER BY created_at
                   LIMIT 1""",
                params=[user_id, company_id],
            )
            if existing:
                application_id = existing[0]["id"]
                log.info("matched existing application=%s for (user=%s company=%s)", application_id, user_id, company_id)
            else:
                created = await conn.execute(
                    """INSERT INTO application (user_id, company, role_title, sender_email, status)
                       VALUES ($1, $2, $3, $4, $5)
                       RETURNING id""",
                    params=[user_id, company_id, role_title, sender_email, new_status],
                )
                if not created:
                    log.warning("application insert returned nothing (user=%s company=%s)", user_id, company_id)
                    return None
                application_id = created[0]["id"]
                log.info("created application=%s (user=%s company=%s role=%r status=%s)",
                         application_id, user_id, company_id, role_title, new_status)

            await _link_message(conn, email.get("id"), application_id)
            await _advance_status(conn, application_id, new_status)
            return application_id
        except Exception as e:
            log.exception("user=%s email=%s failed: %s", user_id, email.get('id'), type(e).__name__)
            return None
    