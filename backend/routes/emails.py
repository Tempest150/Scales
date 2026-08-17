from datetime import datetime

import httpx
from quart import Blueprint, jsonify, g

from constants import FetchType
from db import Rimiru
from useCheck import require_user
from EmailClassifier import Duro

emails_bp = Blueprint("emails", __name__)
endpoint = "https://email.austindwomoh.xyz/"

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
    _sync_progress[user_id] = {"status": "syncing", "total": 0, "completed": 0,"failed": 0, "error": None}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{endpoint}pending_emails", params={"user_id": user_id})
            resp.raise_for_status()
            pending_emails = resp.json()

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
                classification = await classifier.classify(text, from_email, subject)
                email["classification"] = classification

                if classification.get("is_application_related"):
                    await resolve_application(db, user_id, email, classification)
                    application_related[email_id] = {
                        "id": email_id,
                        "classification": classification,
                        "status": "classified",
                        "processed_at": datetime.utcnow()
                    }
                else:
                    clear.append(email_id)

            except Exception as e:
                _sync_progress[user_id]["failed"] += 1
                print(f"[classify_pending_emails] user={user_id} email={email_id} failed: {type(e).__name__}: {e!r}")
        # leave this email as pending — don't add to either bucket, so it's retried next sync
            _sync_progress[user_id]["completed"] += 1


      


        if clear:
            await db.delete(table="messages", filters={"id": list(clear)})

        _sync_progress[user_id]["status"] = "done"
        print(f"[classify_pending_emails] user={user_id} classified={len(application_related)} cleared={len(clear)}")
    except Exception as e:
        _sync_progress[user_id]["status"] = "error"
        _sync_progress[user_id]["error"] = f"{type(e).__name__}: {e}"
        print(f"[classify_pending_emails] user={user_id} failed: {type(e).__name__}: {e!r}")

async def resolve_application(conn: Rimiru, user_id: str, email: dict, classification: dict):
    company_name = classification.get("company_name")
    sender_email = email.get("from")
    role_title = classification.get("role_title")
    status = classification.get("status") or "applied"

    if not company_name or not sender_email:
        return None

    company_row = await conn.upsert(
        table="company",
        data={"name": company_name},
        conflict_column="lower(name)",
    )
    company_id = company_row["id"]  # type: ignore

    
    application_id = application_id = await conn.call_function(
                fn="upsert_application",
                params=[user_id, company_id, role_title, sender_email, status],
                fetch_type=FetchType.FETCHVAL.value,
            )
    
    
    r = await conn.execute(
    "UPDATE messages SET application_id = $1, status = $3 WHERE id = $2",
    params=[application_id, email.get("id"), "classified"],
    fetch=False,
    )
    if r == "UPDATE 0":
        print(f"[resolve_application] warning: no messages row updated for email_id={email.get('id')}")

    return application_id