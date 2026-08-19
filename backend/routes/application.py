from datetime import datetime

import httpx
from quart import Blueprint, jsonify, g

from constants import FetchType, Constants
from db import Rimiru
from useCheck import require_user
from EmailClassifier import Duro

app_bp = Blueprint("application", __name__)

@app_bp.route("/api/application/dashboard", methods=["GET"])
@require_user
async def get_dashboard():
    """
    Get the dashboard data for the user.
    """
    user_id = g.current_user['id']
    db =await  Rimiru.shion()
    applications  = await db.execute(
        sql="""
            SELECT
                a.id AS application_id,
                c.name AS company,
                a.role_title AS role_title,
                a.status AS status,
                a.status_changed_at AS status_changed_at,
                m.id AS message_id
            FROM application a
            JOIN company c ON a.company = c.id
            LEFT JOIN LATERAL (
                SELECT id
                FROM messages
                WHERE application_id = a.id
                ORDER BY received_at DESC
                LIMIT 1
            ) m ON true
            WHERE a.user_id = $1
            ORDER BY a.created_at DESC
            LIMIT 10""",
        params =[user_id]
        )
   
    jobs =  await db.execute(
        sql="""
        SELECT
            j.title AS job_title,
            j.apply_url AS apply_url,
            j.tags AS tags,
            j.summary AS summary,
            c.name AS company_name
        FROM job_list j
        JOIN company c ON j.company = c.id
        WHERE j.enriched = TRUE
        ORDER BY j.created_at DESC LIMIT 10
        """,
        )
   
    # Combine user data and external data
    return jsonify({
        "applications": applications,
        "jobs": jobs,
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