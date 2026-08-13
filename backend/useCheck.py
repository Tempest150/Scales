
from db import Rimiru
from functools import wraps
from quart import session, jsonify, g

def require_user(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
     
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        db = await Rimiru.shion()
        rows = await db.select(table='users', filters={'id': user_id})
        if not rows:
            session.clear()
            return jsonify({'error': 'Invalid session'}), 401

        g.current_user = rows[0]
        return await f(*args, **kwargs)
    return wrapper