from datetime import datetime

import httpx
from quart import Blueprint, jsonify, g, request

from constants import FetchType, Constants
from db import Rimiru
from logger import get_logger
from useCheck import require_user
from EmailClassifier import Duro

app_bp = Blueprint("application", __name__)
log = get_logger("application")

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def _parse_pagination(args):
    """Read page/page_size/search from request.args with safe defaults/bounds."""
    try:
        page = max(1, int(args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(args.get("page_size", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))

    search = (args.get("search") or "").strip() or None
    offset = (page - 1) * page_size
    return page, page_size, search, offset


async def _fetch_applications(db, user_id, page_size, offset, search):
    rows = await db.execute(
        sql="""
            SELECT
                a.id AS application_id,
                c.name AS company,
                a.role_title AS role_title,
                a.status AS status,
                a.status_changed_at AS status_changed_at,
                m.gmail_message_id AS gmail_message_id,
                COUNT(*) OVER() AS total_count
            FROM application a
            JOIN company c ON a.company = c.id
            LEFT JOIN LATERAL (
                SELECT gmail_message_id
                FROM messages
                WHERE application_id = a.id
                ORDER BY received_at DESC
                LIMIT 1
            ) m ON true
            WHERE a.user_id = $1
              AND (
                  $2::text IS NULL
                  OR c.name ILIKE '%' || $2 || '%'
                  OR a.role_title ILIKE '%' || $2 || '%'
              )
            ORDER BY a.created_at DESC
            LIMIT $3 OFFSET $4""",
        params=[user_id, search, page_size, offset],
    )
    total = rows[0]["total_count"] if rows else 0
    for row in rows:
        row.pop("total_count", None)
    return rows, total


async def _fetch_jobs(db, page_size, offset, search):
    rows = await db.execute(
        sql="""
            SELECT
                INITCAP(j.title) AS job_title,
                j.apply_url AS apply_url,
                j.tags AS tags,
                j.summary AS summary,
                INITCAP(c.name) AS company_name,
                COUNT(*) OVER() AS total_count
            FROM job_list j
            JOIN company c ON j.company = c.id
            WHERE j.enriched = TRUE
              AND (
                  $1::text IS NULL
                  OR j.title ILIKE '%' || $1 || '%'
                  OR c.name ILIKE '%' || $1 || '%'
              )
            ORDER BY j.created_at DESC
            LIMIT $2 OFFSET $3""",
        params=[search, page_size, offset],
    )
    total = rows[0]["total_count"] if rows else 0
    for row in rows:
        row.pop("total_count", None)
    return rows, total


@app_bp.route("/api/application/dashboard", methods=["GET"])
@require_user
async def get_dashboard():
    """
    Get the dashboard data for the user. Kept unpaginated (first page,
    no search) for the initial combined load; the applications/jobs tabs
    page and search independently via /api/application/applications and
    /api/application/jobs.
    """
    user_id = g.current_user['id']
    with log.section("get_dashboard", user_id=user_id):
        db = await Rimiru.shion()
        applications, _ = await _fetch_applications(db, user_id, DEFAULT_PAGE_SIZE, 0, None)
        jobs, _ = await _fetch_jobs(db, DEFAULT_PAGE_SIZE, 0, None)

        log.info("dashboard for user=%s: %s application(s), %s job(s)", user_id, len(applications), len(jobs))

        # Combine user data and external data
        return jsonify({
            "applications": applications,
            "jobs": jobs,
        })


@app_bp.route("/api/application/applications", methods=["GET"])
@require_user
async def get_applications():
    """
    Paginated + searchable applications list for the dashboard's applications tab.
    Query params: page (default 1), page_size (default 10, max 50), search (optional).
    """
    user_id = g.current_user['id']
    page, page_size, search, offset = _parse_pagination(request.args)
    with log.section("get_applications", user_id=user_id, page=page, search=search):
        db = await Rimiru.shion()
        applications, total = await _fetch_applications(db, user_id, page_size, offset, search)

        log.info("applications for user=%s: page=%s page_size=%s search=%r -> %s/%s",
                  user_id, page, page_size, search, len(applications), total)

        return jsonify({
            "applications": applications,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        })


@app_bp.route("/api/application/jobs", methods=["GET"])
@require_user
async def get_jobs():
    """
    Paginated + searchable job listings for the dashboard's jobs tab.
    Query params: page (default 1), page_size (default 10, max 50), search (optional).
    """
    page, page_size, search, offset = _parse_pagination(request.args)
    with log.section("get_jobs", page=page, search=search):
        db = await Rimiru.shion()
        jobs, total = await _fetch_jobs(db, page_size, offset, search)

        log.info("jobs: page=%s page_size=%s search=%r -> %s/%s", page, page_size, search, len(jobs), total)

        return jsonify({
            "jobs": jobs,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        })




""" 
@emails_bp.route('/api/messages/<message_id>', methods=['GET'])
@require_user
async def get_message(message_id):
    db = await Rimiru.shion()
    rows = await db.select(
        table='messages',
        filters={'id': message_id, 'user_id': g.current_user['id']},  # scope to the logged-in user
    )
    if not rows:
        return jsonify({'error': 'not found'}), 404

    return jsonify(rows[0]) """