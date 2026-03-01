from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from database import db
from models import User, Doctor, Patient
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

# patient registration
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # validate required fields
    if not data.get('username'):
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    if not data.get('email'):
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    if not data.get('password'):
        return jsonify({'success': False, 'message': 'Password is required'}), 400
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    # check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    # check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    # create user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='patient'
    )
    db.session.add(user)
    db.session.flush()
    
    # create patient profile
    patient = Patient(
        user_id=user.id,
        name=data['name'],
        phone=data.get('phone', ''),
        age=data.get('age'),
        gender=data.get('gender', ''),
        blood_group=data.get('blood_group', ''),
        address=data.get('address', '')
    )
    db.session.add(patient)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful! Please login.'
    }), 201

# login for all users
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('username'):
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    if not data.get('password'):
        return jsonify({'success': False, 'message': 'Password is required'}), 400
    
    # find user
    user = User.query.filter_by(username=data['username']).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    if not user.is_active:
        return jsonify({'success': False, 'message': 'Your account has been deactivated'}), 403
    
    # create jwt token with role info
    token = create_access_token(
        identity=str(user.id),        
        additional_claims={'role': user.role},
        expires_delta=timedelta(hours=24)
    )
    
    return jsonify({
        'success': True,
        'message': f'Welcome back, {user.username}!',
        'data': {
            'token': token,
            'role': user.role,
            'username': user.username,
            'user_id': user.id
        }
    })

# get current user info
@auth_bp.route('/me', methods=['GET'])
def get_me():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {'user': user.to_dict()}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401