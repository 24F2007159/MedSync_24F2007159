from flask import Blueprint, request, jsonify
from database import db
from models import User, Doctor, Patient, Appointment, Treatment, Department
from decorators import admin_required
from werkzeug.security import generate_password_hash
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# admin dashboard stats
@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    total_patients = Patient.query.filter_by(is_blacklisted=False).count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='booked').count()
    completed_appointments = Appointment.query.filter_by(status='completed').count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'completed_appointments': completed_appointments
        }
    })

# get all doctors
@admin_bp.route('/doctors', methods=['GET'])
@admin_required
def get_doctors():
    search = request.args.get('search', '')
    doctors = Doctor.query.join(User)
    
    if search:
        doctors = doctors.filter(
            db.or_(
                Doctor.name.ilike(f'%{search}%'),
                Doctor.specialization.ilike(f'%{search}%')
            )
        )
    
    doctors = doctors.all()
    return jsonify({
        'success': True,
        'data': {'doctors': [d.to_dict() for d in doctors]}
    })

# add new doctor
@admin_bp.route('/doctors', methods=['POST'])
@admin_required
def add_doctor():
    data = request.get_json()
    
    if not data.get('username'):
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    if not data.get('email'):
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    if not data.get('specialization'):
        return jsonify({'success': False, 'message': 'Specialization is required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    # create user account for doctor
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data.get('password', 'doctor123')),
        role='doctor'
    )
    db.session.add(user)
    db.session.flush()
    
    # create doctor profile
    doctor = Doctor(
        user_id=user.id,
        name=data['name'],
        specialization=data['specialization'],
        qualification=data.get('qualification', ''),
        experience=data.get('experience', 0),
        consultation_fee=data.get('consultation_fee', 0),
        phone=data.get('phone', ''),
        bio=data.get('bio', '')
    )
    db.session.add(doctor)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Doctor added successfully',
        'data': {'doctor': doctor.to_dict()}
    }), 201

# update doctor
@admin_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@admin_required
def update_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        doctor.name = data['name']
    if 'specialization' in data:
        doctor.specialization = data['specialization']
    if 'qualification' in data:
        doctor.qualification = data['qualification']
    if 'experience' in data:
        doctor.experience = data['experience']
    if 'consultation_fee' in data:
        doctor.consultation_fee = data['consultation_fee']
    if 'phone' in data:
        doctor.phone = data['phone']
    if 'bio' in data:
        doctor.bio = data['bio']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Doctor updated successfully',
        'data': {'doctor': doctor.to_dict()}
    })

# blacklist/activate doctor
@admin_bp.route('/doctors/<int:doctor_id>/blacklist', methods=['PUT'])
@admin_required
def toggle_doctor_status(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor not found'}), 404
    
    doctor.is_active = not doctor.is_active
    db.session.commit()
    
    status = 'activated' if doctor.is_active else 'blacklisted'
    return jsonify({
        'success': True,
        'message': f'Doctor {status} successfully'
    })

# get all patients
@admin_bp.route('/patients', methods=['GET'])
@admin_required
def get_patients():
    from flask import current_app
    import json
    search = request.args.get('search', '')
    cache = current_app.config.get('CACHE')
    cache_key = f'admin_patients_{search}'

    if cache:
        try:
            cached = cache.get(cache_key)
            if cached:
                return jsonify({'success': True, 'data': {'patients': json.loads(cached)}})
        except:
            pass

    patients = Patient.query.join(User)

    if search:
        patients = patients.filter(
            db.or_(
                Patient.name.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    patients = patients.all()
    data = [p.to_dict() for p in patients]

    if cache:
        try:
            cache.setex(cache_key, 300, json.dumps(data))
        except:
            pass

    return jsonify({
        'success': True,
        'data': {'patients': data}
    })

# blacklist/activate patient
@admin_bp.route('/patients/<int:patient_id>/blacklist', methods=['PUT'])
@admin_required
def toggle_patient_status(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404
    
    patient.is_blacklisted = not patient.is_blacklisted
    db.session.commit()

    # invalidate patient list cache
    from flask import current_app
    cache = current_app.config.get('CACHE')
    if cache:
        try:
            for key in cache.scan_iter('admin_patients_*'):
                cache.delete(key)
        except:
            pass

    status = 'blacklisted' if patient.is_blacklisted else 'activated'
    return jsonify({
        'success': True,
        'message': f'Patient {status} successfully'
    })

# get all appointments
@admin_bp.route('/appointments', methods=['GET'])
@admin_required
def get_appointments():
    status = request.args.get('status', '')
    appointments = Appointment.query
    
    if status:
        appointments = appointments.filter_by(status=status)
    
    appointments = appointments.order_by(
        Appointment.appointment_date.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': {'appointments': [a.to_dict() for a in appointments]}
    })

# get all departments
@admin_bp.route('/departments', methods=['GET'])
@admin_required
def get_departments():
    departments = Department.query.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'data': {'departments': [d.to_dict() for d in departments]}
    })

# chart data for admin dashboard
@admin_bp.route('/chart-data', methods=['GET'])
@admin_required
def get_chart_data():
    booked = Appointment.query.filter_by(status='booked').count()
    completed = Appointment.query.filter_by(status='completed').count()
    cancelled = Appointment.query.filter_by(status='cancelled').count()

    departments = Department.query.filter_by(is_active=True).all()
    dept_labels = []
    dept_counts = []
    for dept in departments:
        count = Doctor.query.filter_by(specialization=dept.name, is_active=True).count()
        dept_labels.append(dept.name)
        dept_counts.append(count)

    return jsonify({
        'success': True,
        'data': {
            'appointments_by_status': {
                'labels': ['Booked', 'Completed', 'Cancelled'],
                'values': [booked, completed, cancelled]
            },
            'doctors_per_dept': {
                'labels': dept_labels,
                'values': dept_counts
            }
        }
    })

# add department
@admin_bp.route('/departments', methods=['POST'])
@admin_required
def add_department():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Department name is required'}), 400
    
    if Department.query.filter_by(name=data['name']).first():
        return jsonify({'success': False, 'message': 'Department already exists'}), 400
    
    dept = Department(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(dept)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Department added successfully',
        'data': {'department': dept.to_dict()}
    }), 201