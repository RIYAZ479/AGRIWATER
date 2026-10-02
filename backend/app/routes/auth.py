from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user account into users table.
    Payload: { "name": "Farmer John", "email": "john@agriwater.io", "password": "securepassword123" }
    """
    data = request.get_json() or {}
    name = data.get('name') or data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({
            'success': False,
            'error': 'Name, email, and password are required'
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'error': 'Email is already registered'
        }), 400

    user = User(name=name, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'data': user.to_dict()
    }), 201

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticate user credentials against users table.
    Payload: { "email": "john@agriwater.io", "password": "securepassword123" }
    """
    data = request.get_json() or {}
    email = data.get('email') or data.get('username')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'success': False,
            'error': 'Email and password are required'
        }), 400

    user = User.query.filter((User.email == email) | (User.name == email)).first()

    if not user or not user.check_password(password):
        return jsonify({
            'success': False,
            'error': 'Invalid email or password'
        }), 401

    return jsonify({
        'success': True,
        'message': 'Authentication successful',
        'data': {
            'user': user.to_dict(),
            'token': f"mock-jwt-token-user-{user.id}"
        }
    })
