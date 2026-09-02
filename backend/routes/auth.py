import asyncio
import hashlib
import secrets
import httpx

from quart import Blueprint, request, jsonify, session, g, url_for, redirect
from authlib.integrations.httpx_client import AsyncOAuth2Client
from constants import Constants
from db import Rimiru
from logger import get_logger
from useCheck import require_user
from routes.emails import classify_pending_emails
auth_bp = Blueprint("auth", __name__)
log = get_logger("auth")

# Hold strong refs to fire-and-forget tasks so asyncio doesn't GC them mid-run.
_background_tasks = set()


def fire_and_forget(coro):
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task

GOOGLE_AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://openidconnect.googleapis.com/v1/userinfo'


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@auth_bp.route('/api/auth/login', methods=['POST'])
async def login():
    log.section("login")
    data = await request.get_json()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        log.warning("login rejected: missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400

    db = await Rimiru.shion()
    rows = await db.select(table='users', filters={'email': email})
    if not rows:
        log.warning("login failed: no user for email=%s", email)
        return jsonify({'error': 'Invalid credentials'}), 401

    user = rows[0]
    if not user.get('password') or user['password'] != hash_password(password):
        log.warning("login failed: bad password for user=%s", user['id'])
        return jsonify({'error': 'Invalid credentials'}), 401

    session["user_id"] = user['id']
    log.info("user=%s logged in (gmail_status=%s)", user['id'], user.get('gmail_status'))

    if user.get('gmail_status') != 'connected':
        log.info("user=%s needs Gmail connect", user['id'])
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': user.get('name') or email,
            'gmail_connect_url': f"{Constants.EMAIL_ENDPOINT}connect/start?user_id={user['id']}",
        })

    log.info("user=%s Gmail connected; kicking off classify_pending_emails", user['id'])
    fire_and_forget(classify_pending_emails(user['id']))
    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'name': user.get('name') or email,
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
async def register():
    log.section("register")
    data = await request.get_json()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name = data.get('name') or email

    if not email or not password:
        log.warning("register rejected: missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400

    db = await Rimiru.shion()
    existing_users = await db.select(table='users', filters={'email': email})
    if existing_users:
        log.warning("register rejected: email=%s already registered", email)
        return jsonify({'error': 'Email already registered'}), 400

    password_hash = hash_password(password)
    new_user = await db.upsert(
        table='users',
        data={'email': email, 'password': password_hash, 'name': name},
        conflict_column='lower(email)',
    )
    log.info("registered new user=%s email=%s", new_user['id'], email)  # type: ignore

    session["user_id"] = new_user['id']  # type: ignore
    return jsonify({
        'id': new_user['id'],  # type: ignore
        'email': new_user['email'],  # type: ignore
        'name': new_user.get('name') or email,  # type: ignore
    }), 201


@auth_bp.route('/api/auth/me', methods=['GET'])
@require_user
async def me():
    return jsonify({
        'id': g.current_user['id'],
        'email': g.current_user['email'],
        'name': g.current_user.get('name') or g.current_user['email'],
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
async def logout():
    log.section("logout")
    log.info("user=%s logged out", session.get('user_id'))
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})


@auth_bp.route('/api/auth/google/login')
async def google_login():
    log.section("google_login")
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    redirect_uri = url_for('auth.google_callback', _external=True)
    log.debug("google redirect_uri=%s", redirect_uri)
    client = AsyncOAuth2Client(
        client_id=Constants.GOOGLE_CLIENT_ID,
        client_secret=Constants.GOOGLE_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        scope='openid email profile',
    )
    uri, state = client.create_authorization_url(GOOGLE_AUTHORIZE_URL, state=state)
    session['oauth_state'] = state
    return redirect(uri)


@auth_bp.route('/api/auth/google/callback')
async def google_callback():
    log.section("google_callback")
    if request.args.get('state') != session.get('oauth_state'):
        log.warning("google callback rejected: state mismatch")
        return jsonify({'error': 'Invalid state'}), 400

    client = AsyncOAuth2Client(
        client_id=Constants.GOOGLE_CLIENT_ID,
        client_secret=Constants.GOOGLE_CLIENT_SECRET,
        redirect_uri=url_for('auth.google_callback', _external=True),
    )
    token = await client.fetch_token(
        GOOGLE_TOKEN_URL,
        authorization_response=request.url,
    )

    resp = await client.get(GOOGLE_USERINFO_URL)  # type: ignore
    userinfo = resp.json()
    email = (userinfo.get('email') or '').strip().lower()
    log.info("google userinfo email=%s name=%r", email, userinfo.get('name'))

    if not email:
        log.warning("google callback rejected: account has no email")
        return jsonify({'error': 'Google account has no email'}), 400

    db = await Rimiru.shion()
    existing = await db.select(table='users', filters={'email': email})

    if existing:
        user = existing[0]
        if not user.get('name') and userinfo.get('name'):
            user = await db.upsert(
                table='users',
                data={'id': user['id'], 'email': user['email'], 'name': userinfo['name']},
                conflict_column='lower(email)',
            )
        log.info("matched existing user=%s for email=%s", user['id'], email)
    else:
        user = await db.upsert(
            table='users',
            data={'email': email, 'name': userinfo.get('name')},
            conflict_column='lower(email)',
        )
        log.info("created user=%s for email=%s via Google OAuth", user['id'], email)  # type: ignore

    session["user_id"] = user['id']  # type: ignore
    log.info("user=%s logged in via Google OAuth (gmail_status=%s)", user['id'], user.get('gmail_status'))  # type: ignore

    if user.get('gmail_status') != 'connected':  # type: ignore
        # Send the BROWSER to imap-checker's consent flow — not an httpx call.
        log.info("user=%s needs Gmail connect; redirecting to imap-checker", user['id'])  # type: ignore
        return redirect(f"{Constants.EMAIL_ENDPOINT}connect/start?user_id={user['id']}")  # type: ignore

    log.info("user=%s Gmail connected; kicking off classify_pending_emails", user['id'])  # type: ignore
    fire_and_forget(classify_pending_emails(user['id']))  # type: ignore
    return redirect(f'{Constants.FRONTEND_URL}/dashboard')