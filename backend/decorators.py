from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def doctor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'doctor':
            return jsonify({'success': False, 'message': 'Doctor access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def patient_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'patient':
            return jsonify({'success': False, 'message': 'Patient access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def patient_or_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') not in ['patient', 'admin']:
            return jsonify({'success': False, 'message': 'Access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def get_current_user_id():
    from flask_jwt_extended import get_jwt_identity
    return int(get_jwt_identity())