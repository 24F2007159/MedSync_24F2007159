from app import app
from database import db
from models import User, Doctor, Patient, Department, DoctorAvailability
from werkzeug.security import generate_password_hash
from datetime import date, timedelta

def seed():
    with app.app_context():
        print("Initializing MedSync database...")
        
        db.create_all()
        print("✓ Tables created")
        
        # create admin
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@medsync.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin created: admin / admin123")
        
        # create departments
        departments = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular system'},
            {'name': 'Neurology', 'description': 'Brain and nervous system'},
            {'name': 'Orthopedics', 'description': 'Bones, joints and muscles'},
            {'name': 'Pediatrics', 'description': 'Medical care for children'},
            {'name': 'Dermatology', 'description': 'Skin, hair and nails'},
        ]
        
        for dept in departments:
            if not Department.query.filter_by(name=dept['name']).first():
                d = Department(name=dept['name'], description=dept['description'])
                db.session.add(d)
        
        db.session.commit()
        print("✓ Departments created")
        
        # create doctors with indian names
        doctors_data = [
            {
                'username': 'dr.rajan',
                'email': 'rajan@medsync.com',
                'password': 'rajan123',
                'name': 'Dr. Suresh Rajan',
                'specialization': 'Cardiology',
                'qualification': 'MBBS, MD (Cardiology)',
                'experience': 15,
                'consultation_fee': 800,
                'phone': '9876543210',
                'bio': 'Senior cardiologist with 15 years experience'
            },
            {
                'username': 'dr.mehta',
                'email': 'mehta@medsync.com',
                'password': 'mehta123',
                'name': 'Dr. Priya Mehta',
                'specialization': 'Neurology',
                'qualification': 'MBBS, DM (Neurology)',
                'experience': 12,
                'consultation_fee': 900,
                'phone': '9876543211',
                'bio': 'Expert neurologist specializing in stroke treatment'
            },
            {
                'username': 'dr.sharma',
                'email': 'sharma@medsync.com',
                'password': 'sharma123',
                'name': 'Dr. Rakesh Sharma',
                'specialization': 'Orthopedics',
                'qualification': 'MBBS, MS (Orthopedics)',
                'experience': 10,
                'consultation_fee': 700,
                'phone': '9876543212',
                'bio': 'Orthopedic surgeon specializing in joint replacement'
            },
            {
                'username': 'dr.iyer',
                'email': 'iyer@medsync.com',
                'password': 'iyer123',
                'name': 'Dr. Lakshmi Iyer',
                'specialization': 'Pediatrics',
                'qualification': 'MBBS, MD (Pediatrics)',
                'experience': 8,
                'consultation_fee': 600,
                'phone': '9876543213',
                'bio': 'Dedicated pediatrician with focus on child development'
            },
            {
                'username': 'dr.khan',
                'email': 'khan@medsync.com',
                'password': 'khan123',
                'name': 'Dr. Imran Khan',
                'specialization': 'Dermatology',
                'qualification': 'MBBS, MD (Dermatology)',
                'experience': 9,
                'consultation_fee': 650,
                'phone': '9876543214',
                'bio': 'Experienced dermatologist treating skin conditions'
            },
        ]
        
        for doc_data in doctors_data:
            if not User.query.filter_by(username=doc_data['username']).first():
                user = User(
                    username=doc_data['username'],
                    email=doc_data['email'],
                    password_hash=generate_password_hash(doc_data['password']),
                    role='doctor'
                )
                db.session.add(user)
                db.session.flush()
                
                doctor = Doctor(
                    user_id=user.id,
                    name=doc_data['name'],
                    specialization=doc_data['specialization'],
                    qualification=doc_data['qualification'],
                    experience=doc_data['experience'],
                    consultation_fee=doc_data['consultation_fee'],
                    phone=doc_data['phone'],
                    bio=doc_data['bio']
                )
                db.session.add(doctor)
                db.session.flush()
                
                # create 7 days availability
                for i in range(7):
                    day = date.today() + timedelta(days=i)
                    for slot in ['morning', 'evening']:
                        avail = DoctorAvailability(
                            doctor_id=doctor.id,
                            availability_date=day,
                            slot_type=slot,
                            is_available=True
                        )
                        db.session.add(avail)
        
        db.session.commit()
        print("✓ Doctors created with 7 day availability")
        
        # create patients with indian names
        patients_data = [
            {
                'username': 'rahul.verma',
                'email': 'rahul@medsync.com',
                'password': 'rahul123',
                'name': 'Rahul Verma',
                'phone': '9123456780',
                'age': 32,
                'gender': 'Male',
                'blood_group': 'O+',
                'address': 'Mumbai, Maharashtra',
                'emergency_contact': '9123456781'
            },
            {
                'username': 'priya.singh',
                'email': 'priya@medsync.com',
                'password': 'priya123',
                'name': 'Priya Singh',
                'phone': '9123456782',
                'age': 28,
                'gender': 'Female',
                'blood_group': 'A+',
                'address': 'Delhi, NCR',
                'emergency_contact': '9123456783'
            },
            {
                'username': 'amit.patel',
                'email': 'amit@medsync.com',
                'password': 'amit123',
                'name': 'Amit Patel',
                'phone': '9123456784',
                'age': 45,
                'gender': 'Male',
                'blood_group': 'B+',
                'address': 'Ahmedabad, Gujarat',
                'emergency_contact': '9123456785'
            },
        ]
        
        for pat_data in patients_data:
            if not User.query.filter_by(username=pat_data['username']).first():
                user = User(
                    username=pat_data['username'],
                    email=pat_data['email'],
                    password_hash=generate_password_hash(pat_data['password']),
                    role='patient'
                )
                db.session.add(user)
                db.session.flush()
                
                patient = Patient(
                    user_id=user.id,
                    name=pat_data['name'],
                    phone=pat_data['phone'],
                    age=pat_data['age'],
                    gender=pat_data['gender'],
                    blood_group=pat_data['blood_group'],
                    address=pat_data['address'],
                    emergency_contact=pat_data['emergency_contact']
                )
                db.session.add(patient)
        
        db.session.commit()
        print("✓ Patients created")
        print("\n✅ MedSync database ready!")
        print("\nLogin credentials:")
        print("Admin:   admin / admin123")
        print("Doctors: dr.rajan / rajan123")
        print("         dr.mehta / mehta123")
        print("         dr.sharma / sharma123")
        print("Patients: rahul.verma / rahul123")
        print("          priya.singh / priya123")
        print("          amit.patel / amit123")

if __name__ == '__main__':
    seed()