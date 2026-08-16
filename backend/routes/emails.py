from datetime import datetime

import httpx
from quart import Blueprint, jsonify, g

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
        "status": "idle", "total": 0, "completed": 0, "error": None,
    })
    return jsonify(progress)


async def classify_pending_emails(user_id):
    """Fetch a user's pending emails, classify them, and store application-related ones.

    Runs as a fire-and-forget background task after login, not as a request handler,
    so it has no request/session context of its own — user_id is passed in directly.
    Updates _sync_progress as it goes so the frontend can poll /api/emails/sync-status
    and drive a "3/10 processed" style spinner.
    """
    _sync_progress[user_id] = {"status": "syncing", "total": 0, "completed": 0, "error": None}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{endpoint}pending_emails", params={"user_id": user_id})
            resp.raise_for_status()
            pending_emails = resp.json()

        _sync_progress[user_id]["total"] = len(pending_emails)

        classifier = Duro()
        application_related = {}
        clear = []
        for email in pending_emails:
            text = email.get("text", "")
            subject = email.get("subject", "")
            from_email = email.get("from", "")
            classification = await classifier.classify(text, from_email, subject)
            email["classification"] = classification
            if classification.get("is_application_related"):
                application_related[email.get("id")] = {
                    "id": email.get("id"),
                    "classification": classification,
                    "status": "classified",
                    "processed_at": datetime.utcnow()
                }
            else:
                clear.append(email.get("id"))
            _sync_progress[user_id]["completed"] += 1

        db = await Rimiru.shion()
        if application_related:
            for email_id, data in application_related.items():
                await db.upsert(table="messages", data=data, conflict_column="id")

        if clear:
            await db.delete(table="messages", filters={"id": list(clear)})

        _sync_progress[user_id]["status"] = "done"
        print(f"[classify_pending_emails] user={user_id} classified={len(application_related)} cleared={len(clear)}")
    except Exception as e:
        _sync_progress[user_id]["status"] = "error"
        _sync_progress[user_id]["error"] = str(e)
        print(f"[classify_pending_emails] user={user_id} failed: {e}")
