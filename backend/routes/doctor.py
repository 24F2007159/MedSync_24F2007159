from flask import Blueprint, request, jsonify
from database import db
from models import User, Doctor, Patient, Appointment, Treatment, DoctorAvailability
from decorators import doctor_required, get_current_user_id
from datetime import datetime, date, timedelta

doctor_bp = Blueprint('doctor', __name__)

# doctor dashboard stats
@doctor_bp.route('/dashboard', methods=['GET'])
@doctor_required
def get_dashboard():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    today = date.today()
    
    total_appointments = Appointment.query.filter_by(doctor_id=doctor.id).count()
    todays_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today,
        status='booked'
    ).count()
    total_patients = db.session.query(Appointment.patient_id).filter_by(
        doctor_id=doctor.id
    ).distinct().count()
    completed_today = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today,
        status='completed'
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'doctor': doctor.to_dict(),
            'total_appointments': total_appointments,
            'todays_appointments': todays_appointments,
            'total_patients': total_patients,
            'completed_today': completed_today
        }
    })

# get doctor's appointments
@doctor_bp.route('/appointments', methods=['GET'])
@doctor_required
def get_appointments():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    status = request.args.get('status', '')
    filter_date = request.args.get('date', '')
    
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if status:
        query = query.filter_by(status=status)
    
    if filter_date:
        try:
            apt_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=apt_date)
        except ValueError:
            pass
    
    appointments = query.order_by(
        Appointment.appointment_date.asc(),
        Appointment.appointment_time.asc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': {'appointments': [a.to_dict() for a in appointments]}
    })

# mark appointment as completed or cancelled
@doctor_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
@doctor_required
def update_appointment_status(appointment_id):
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    if appointment.status != 'booked':
        return jsonify({'success': False, 'message': 'Can only update booked appointments'}), 400
    
    appointment.status = new_status
    appointment.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Appointment marked as {new_status}'
    })

# add treatment record
@doctor_bp.route('/appointments/<int:appointment_id>/treatment', methods=['POST'])
@doctor_required
def add_treatment(appointment_id):
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404
    
    data = request.get_json()
    
    if not data.get('diagnosis'):
        return jsonify({'success': False, 'message': 'Diagnosis is required'}), 400
    
    # check if treatment already exists
    existing = Treatment.query.filter_by(appointment_id=appointment_id).first()
    
    if existing:
        # update existing treatment
        existing.diagnosis = data['diagnosis']
        existing.prescription = data.get('prescription', '')
        existing.notes = data.get('notes', '')
        if data.get('next_visit'):
            try:
                existing.next_visit = datetime.strptime(
                    data['next_visit'], '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        existing.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Treatment updated successfully'
        })
    
    # create new treatment
    treatment = Treatment(
        appointment_id=appointment_id,
        diagnosis=data['diagnosis'],
        prescription=data.get('prescription', ''),
        notes=data.get('notes', '')
    )
    
    if data.get('next_visit'):
        try:
            treatment.next_visit = datetime.strptime(
                data['next_visit'], '%Y-%m-%d'
            ).date()
        except ValueError:
            pass
    
    # mark appointment as completed
    appointment.status = 'completed'
    appointment.updated_at = datetime.utcnow()
    
    db.session.add(treatment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Treatment added successfully',
        'data': {'treatment': treatment.to_dict()}
    }), 201

# get patient history
@doctor_bp.route('/patients/<int:patient_id>/history', methods=['GET'])
@doctor_required
def get_patient_history(patient_id):
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404
    
    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient_id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    return jsonify({
        'success': True,
        'data': {
            'patient': patient.to_dict(),
            'appointments': [a.to_dict() for a in appointments]
        }
    })

# get assigned patients
@doctor_bp.route('/patients', methods=['GET'])
@doctor_required
def get_patients():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    patient_ids = db.session.query(Appointment.patient_id).filter_by(
        doctor_id=doctor.id
    ).distinct().all()
    
    patient_ids = [p[0] for p in patient_ids]
    patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    return jsonify({
        'success': True,
        'data': {'patients': [p.to_dict() for p in patients]}
    })

# set availability
@doctor_bp.route('/availability', methods=['POST'])
@doctor_required
def set_availability():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    data = request.get_json()
    availability_data = data.get('availability', [])
    
    for item in availability_data:
        try:
            avail_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except ValueError:
            continue
        
        for slot_type in ['morning', 'evening']:
            existing = DoctorAvailability.query.filter_by(
                doctor_id=doctor.id,
                availability_date=avail_date,
                slot_type=slot_type
            ).first()
            
            is_available = item.get(slot_type, False)
            
            if existing:
                existing.is_available = is_available
            else:
                new_avail = DoctorAvailability(
                    doctor_id=doctor.id,
                    availability_date=avail_date,
                    slot_type=slot_type,
                    is_available=is_available
                )
                db.session.add(new_avail)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Availability updated successfully'
    })

# get own availability
@doctor_bp.route('/availability', methods=['GET'])
@doctor_required
def get_availability():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    today = date.today()
    next_7_days = today + timedelta(days=7)
    
    availability = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.availability_date >= today,
        DoctorAvailability.availability_date <= next_7_days
    ).order_by(DoctorAvailability.availability_date.asc()).all()
    
    return jsonify({
        'success': True,
        'data': {'availability': [a.to_dict() for a in availability]}
    })

# update doctor profile
@doctor_bp.route('/profile', methods=['PUT'])
@doctor_required
def update_profile():
    user_id = get_current_user_id()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    
    data = request.get_json()
    
    if 'phone' in data:
        doctor.phone = data['phone']
    if 'bio' in data:
        doctor.bio = data['bio']
    if 'qualification' in data:
        doctor.qualification = data['qualification']
    if 'consultation_fee' in data:
        doctor.consultation_fee = data['consultation_fee']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'data': {'doctor': doctor.to_dict()}
    })