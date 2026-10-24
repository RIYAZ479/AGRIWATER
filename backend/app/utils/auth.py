from functools import wraps
from flask import request, jsonify, current_app, g
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.models.user import User


def _get_serializer():
    """Returns an itsdangerous serializer initialized with the application SECRET_KEY."""
    secret = current_app.config.get('SECRET_KEY', 'agriwater-ai-secret-key-2026-secure')
    return URLSafeTimedSerializer(secret, salt='agriwater-auth-v1')


def generate_auth_token(user_id, expires_in=86400):
    """
    Generates a cryptographically signed, URL-safe authentication token.
    Default validity: 86,400 seconds (24 hours).
    """
    serializer = _get_serializer()
    return serializer.dumps({'user_id': user_id})


def verify_auth_token(token, max_age=86400):
    """
    Verifies the cryptographic signature and expiration of a token.
    Returns the User model instance if valid, or None if invalid/expired.
    """
    if not token or not isinstance(token, str):
        return None

    serializer = _get_serializer()
    try:
        data = serializer.loads(token, max_age=max_age)
        user_id = data.get('user_id')
        if not user_id:
            return None
        return User.query.get(user_id)
    except (SignatureExpired, BadSignature, KeyError, TypeError, ValueError):
        return None


def token_required(f):
    """
    Decorator protecting routes that require an authenticated user.
    Extracts Bearer token from 'Authorization' header or query parameter 'token'.
    Attaches authenticated User instance to flask.g.current_user.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif auth_header:
            token = auth_header.strip()
        elif 'token' in request.args:
            token = request.args.get('token')

        if not token:
            return jsonify({
                'success': False,
                'error': 'Authentication token is required.'
            }), 401

        user = verify_auth_token(token)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Invalid, tampered, or expired token.'
            }), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated
