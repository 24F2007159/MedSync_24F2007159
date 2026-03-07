from flask import Blueprint, request, jsonify
from database import db
from models import User, Doctor, Patient, Appointment, Treatment, DoctorAvailability, Department
from decorators import patient_required, patient_or_admin_required, get_current_user_id
from datetime import datetime, date, time, timedelta

patient_bp = Blueprint('patient', __name__)

# patient dashboard
@patient_bp.route('/dashboard', methods=['GET'])
@patient_required
def get_dashboard():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    upcoming = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date >= date.today(),
        Appointment.status == 'booked'
    ).count()
    
    total = Appointment.query.filter_by(patient_id=patient.id).count()
    
    doctors_visited = db.session.query(Appointment.doctor_id).filter_by(
        patient_id=patient.id
    ).distinct().count()
    
    return jsonify({
        'success': True,
        'data': {
            'patient': patient.to_dict(),
            'upcoming_appointments': upcoming,
            'total_appointments': total,
            'doctors_visited': doctors_visited
        }
    })

# get all departments
@patient_bp.route('/departments', methods=['GET'])
@patient_or_admin_required
def get_departments():
    from flask import current_app
    import json
    
    # check redis cache first
    cache = current_app.config.get('CACHE')
    cache_key = 'medsync_departments'
    
    if cache:
        try:
            cached = cache.get(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'message': 'Departments retrieved (cached)',
                    'data': {'departments': json.loads(cached)}
                })
        except:
            pass
    
    # not in cache - fetch from database
    departments = Department.query.filter_by(is_active=True).all()
    
    data = []
    for dept in departments:
        doctors = Doctor.query.filter_by(
            specialization=dept.name,
            is_active=True
        ).all()
        
        dept_info = {
            'id': dept.id,
            'name': dept.name,
            'description': dept.description,
            'doctor_count': len(doctors),
            'doctors': [d.to_dict() for d in doctors]
        }
        data.append(dept_info)
    
    # save to cache for 5 minutes
    if cache:
        try:
            cache.setex(cache_key, 300, json.dumps(data))
        except:
            pass
    
    return jsonify({
        'success': True,
        'data': {'departments': data}
    })

# get doctors by department
@patient_bp.route('/departments/<int:dept_id>/doctors', methods=['GET'])
@patient_or_admin_required
def get_doctors_by_department(dept_id):
    """Get all doctors in a specific department"""
    department = Department.query.get(dept_id)
    if not department or not department.is_active:
        return jsonify({'success': False, 'message': 'Department not found'}), 404
    
    # Get doctors with matching specialization
    doctors = Doctor.query.filter_by(
        specialization=department.name,
        is_active=True
    ).all()
    
    return jsonify({
        'success': True,
        'data': {
            'doctors': [d.to_dict() for d in doctors],
            'department': department.to_dict()
        }
    })

# get available slots for a doctor)

# get available slots for a doctor
@patient_bp.route('/available-slots', methods=['GET'])
@patient_or_admin_required
def get_available_slots():
    doctor_id = request.args.get('doctor_id')
    date_str = request.args.get('date')
    
    if not doctor_id:
        return jsonify({'success': False, 'message': 'Doctor ID is required'}), 400
    if not date_str:
        return jsonify({'success': False, 'message': 'Date is required'}), 400
    
    try:
        apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # get IST time
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now.date()
    current_hour = now.hour
    is_today = (apt_date == today)
    
    # check doctor availability
    morning_avail = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        availability_date=apt_date,
        slot_type='morning',
        is_available=True
    ).first()
    
    evening_avail = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        availability_date=apt_date,
        slot_type='evening',
        is_available=True
    ).first()
    
    # check cache for this doctor+date combo
    from flask import current_app
    import json
    cache = current_app.config.get('CACHE')
    cache_key = f'slots_{doctor_id}_{date_str}'
    if cache:
        try:
            cached = cache.get(cache_key)
            if cached:
                return jsonify({
                    'success': True,
                    'data': {'slots': json.loads(cached), 'date': apt_date.isoformat()}
                })
        except:
            pass

    slots = []

    def add_slots(start_hour, end_hour, slot_type):
        for h in range(start_hour, end_hour):
            slot_time = time(h, 0)
            
            # check if already booked
            booked = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=apt_date,
                appointment_time=slot_time,
                status='booked'
            ).first()
            
            # check if time has passed today
            is_passed = is_today and current_hour >= h
            
            if not is_passed:
                start_obj = datetime.strptime(f'{h}:00', '%H:%M')
                end_obj = datetime.strptime(f'{h+1}:00', '%H:%M')
                display = f"{start_obj.strftime('%I:%M %p')} - {end_obj.strftime('%I:%M %p')}"
                
                slots.append({
                    'slot_type': slot_type,
                    'time': f'{h:02d}:00',
                    'display': display,
                    'status': 'booked' if booked else 'available'
                })
    
    if morning_avail:
        add_slots(9, 13, 'morning')
    if evening_avail:
        add_slots(15, 19, 'evening')

    # cache slots for 60 seconds
    if cache:
        try:
            cache.setex(cache_key, 60, json.dumps(slots))
        except:
            pass

    return jsonify({
        'success': True,
        'data': {'slots': slots, 'date': apt_date.isoformat()}
    })

# book appointment
@patient_bp.route('/appointments', methods=['POST'])
@patient_required
def book_appointment():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    if patient.is_blacklisted:
        return jsonify({'success': False, 'message': 'Your account is blacklisted. Contact admin.'}), 403
    
    data = request.get_json()
    
    if not data.get('doctor_id'):
        return jsonify({'success': False, 'message': 'Doctor ID is required'}), 400
    if not data.get('appointment_date'):
        return jsonify({'success': False, 'message': 'Date is required'}), 400
    if not data.get('appointment_time'):
        return jsonify({'success': False, 'message': 'Time is required'}), 400
    
    doctor = Doctor.query.get(data['doctor_id'])
    if not doctor or not doctor.is_active:
        return jsonify({'success': False, 'message': 'Doctor not found or inactive'}), 404
    
    try:
        apt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # validate not in past
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now.date()
    
    if apt_date < today:
        return jsonify({'success': False, 'message': 'Cannot book appointments for past dates'}), 400
    
    # parse time
    try:
        apt_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid time format'}), 400
    
    # determine slot type
    hour = apt_time.hour
    if 9 <= hour < 13:
        slot_type = 'morning'
    elif 15 <= hour < 19:
        slot_type = 'evening'
    else:
        return jsonify({'success': False, 'message': 'Invalid time slot'}), 400
    
    # check doctor availability
    availability = DoctorAvailability.query.filter_by(
        doctor_id=data['doctor_id'],
        availability_date=apt_date,
        slot_type=slot_type,
        is_available=True
    ).first()
    
    if not availability:
        return jsonify({'success': False, 'message': 'Doctor not available on this date'}), 400
    
    # prevent double booking
    existing = Appointment.query.filter_by(
        doctor_id=data['doctor_id'],
        appointment_date=apt_date,
        appointment_time=apt_time,
        status='booked'
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'This slot is already booked'}), 400
    
    # check patient doesn't have another appointment at same time
    conflict = Appointment.query.filter_by(
        patient_id=patient.id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        status='booked'
    ).first()
    
    if conflict:
        return jsonify({'success': False, 'message': 'You already have an appointment at this time'}), 400
    
    # create appointment
    appointment = Appointment(
        doctor_id=data['doctor_id'],
        patient_id=patient.id,
        appointment_date=apt_date,
        appointment_time=apt_time,
        status='booked',
        notes=data.get('notes', '')
    )
    
    db.session.add(appointment)
    db.session.commit()

    # invalidate slot cache for this doctor+date
    from flask import current_app
    cache = current_app.config.get('CACHE')
    if cache:
        try:
            cache.delete(f'slots_{data["doctor_id"]}_{data["appointment_date"]}')
        except:
            pass

    return jsonify({
        'success': True,
        'message': 'Appointment booked successfully!',
        'data': {'appointment': appointment.to_dict()}
    }), 201

# get patient appointments
@patient_bp.route('/appointments', methods=['GET'])
@patient_required
def get_appointments():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    status = request.args.get('status', '')
    query = Appointment.query.filter_by(patient_id=patient.id)
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(
        Appointment.appointment_date.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': {'appointments': [a.to_dict() for a in appointments]}
    })

# reschedule appointment
@patient_bp.route('/appointments/<int:appointment_id>/reschedule', methods=['PUT'])
@patient_required
def reschedule_appointment(appointment_id):
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()

    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()

    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404

    if appointment.status != 'booked':
        return jsonify({'success': False, 'message': 'Can only reschedule booked appointments'}), 400

    data = request.get_json()

    if not data.get('appointment_date'):
        return jsonify({'success': False, 'message': 'New date is required'}), 400
    if not data.get('appointment_time'):
        return jsonify({'success': False, 'message': 'New time is required'}), 400

    try:
        new_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400

    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    if new_date < now.date():
        return jsonify({'success': False, 'message': 'Cannot reschedule to a past date'}), 400

    try:
        new_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid time format'}), 400

    hour = new_time.hour
    if 9 <= hour < 13:
        slot_type = 'morning'
    elif 15 <= hour < 19:
        slot_type = 'evening'
    else:
        return jsonify({'success': False, 'message': 'Invalid time slot'}), 400

    availability = DoctorAvailability.query.filter_by(
        doctor_id=appointment.doctor_id,
        availability_date=new_date,
        slot_type=slot_type,
        is_available=True
    ).first()

    if not availability:
        return jsonify({'success': False, 'message': 'Doctor not available on this date'}), 400

    # prevent double booking (exclude this appointment)
    conflict_doctor = Appointment.query.filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.appointment_date == new_date,
        Appointment.appointment_time == new_time,
        Appointment.status == 'booked',
        Appointment.id != appointment_id
    ).first()

    if conflict_doctor:
        return jsonify({'success': False, 'message': 'This slot is already booked'}), 400

    conflict_patient = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.appointment_date == new_date,
        Appointment.appointment_time == new_time,
        Appointment.status == 'booked',
        Appointment.id != appointment_id
    ).first()

    if conflict_patient:
        return jsonify({'success': False, 'message': 'You already have an appointment at this time'}), 400

    old_date = appointment.appointment_date.isoformat()
    doctor_id = appointment.doctor_id
    appointment.appointment_date = new_date
    appointment.appointment_time = new_time
    appointment.updated_at = datetime.utcnow()
    db.session.commit()

    from flask import current_app
    cache = current_app.config.get('CACHE')
    if cache:
        try:
            cache.delete(f'slots_{doctor_id}_{old_date}')
            cache.delete(f'slots_{doctor_id}_{new_date.isoformat()}')
        except:
            pass

    return jsonify({
        'success': True,
        'message': 'Appointment rescheduled successfully',
        'data': {'appointment': appointment.to_dict()}
    })

# cancel appointment
@patient_bp.route('/appointments/<int:appointment_id>/cancel', methods=['PUT'])
@patient_required
def cancel_appointment(appointment_id):
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404
    
    if appointment.status != 'booked':
        return jsonify({'success': False, 'message': 'Can only cancel booked appointments'}), 400
    
    old_date = appointment.appointment_date.isoformat()
    old_doctor_id = appointment.doctor_id
    appointment.status = 'cancelled'
    appointment.updated_at = datetime.utcnow()
    db.session.commit()

    from flask import current_app
    cache = current_app.config.get('CACHE')
    if cache:
        try:
            cache.delete(f'slots_{old_doctor_id}_{old_date}')
        except:
            pass

    return jsonify({
        'success': True,
        'message': 'Appointment cancelled successfully'
    })

# get patient medical history
@patient_bp.route('/history', methods=['GET'])
@patient_required
def get_history():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    treatments = db.session.query(Treatment).join(Appointment).filter(
        Appointment.patient_id == patient.id
    ).order_by(Treatment.created_at.desc()).all()
    
    treatment_data = []
    for t in treatments:
        t_dict = t.to_dict()
        appointment = Appointment.query.get(t.appointment_id)
        if appointment:
            t_dict['appointment_date'] = appointment.appointment_date.isoformat()
            t_dict['appointment_time'] = str(appointment.appointment_time)
            if appointment.doctor:
                t_dict['doctor_name'] = appointment.doctor.name
                t_dict['specialization'] = appointment.doctor.specialization
        treatment_data.append(t_dict)
    
    return jsonify({
        'success': True,
        'data': {'treatments': treatment_data}
    })

# update patient profile
@patient_bp.route('/profile', methods=['PUT'])
@patient_required
def update_profile():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        patient.name = data['name']
    if 'phone' in data:
        patient.phone = data['phone']
    if 'address' in data:
        patient.address = data['address']
    if 'age' in data:
        patient.age = data['age']
    if 'gender' in data:
        patient.gender = data['gender']
    if 'blood_group' in data:
        patient.blood_group = data['blood_group']
    if 'emergency_contact' in data:
        patient.emergency_contact = data['emergency_contact']
    if 'email' in data:
        patient.user.email = data['email']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'data': {'patient': patient.to_dict()}
    })

# trigger csv export
@patient_bp.route('/export', methods=['POST'])
@patient_required
def export_history():
    user_id = get_current_user_id()
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
    
    try:
        from celery_tasks.export_tasks import export_patient_csv
        task = export_patient_csv.delay(patient.id)
        return jsonify({
            'success': True,
            'message': 'Export started! You will be notified when ready.',
            'data': {'task_id': task.id}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Export failed: {str(e)}'}), 500

