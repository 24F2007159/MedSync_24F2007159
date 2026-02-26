from datetime import datetime
from database import db

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200))
    experience = db.Column(db.Integer, default=0)  # in years
    consultation_fee = db.Column(db.Float, default=0.0)
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'specialization': self.specialization,
            'qualification': self.qualification,
            'experience': self.experience,
            'consultation_fee': self.consultation_fee,
            'phone': self.phone,
            'bio': self.bio,
            'is_active': self.is_active,
            'email': self.user.email if self.user else None
        }
    
    def __repr__(self):
        return f'<Doctor {self.name}>'