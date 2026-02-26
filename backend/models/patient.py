from datetime import datetime
from database import db

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    medical_history = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'age': self.age,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'medical_history': self.medical_history,
            'emergency_contact': self.emergency_contact,
            'is_blacklisted': self.is_blacklisted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'username': self.user.username if self.user else None,
            'email': self.user.email if self.user else None
        }
    
    def __repr__(self):
        return f'<Patient {self.name}>'