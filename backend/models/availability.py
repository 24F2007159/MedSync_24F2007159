from datetime import datetime
from database import db

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    availability_date = db.Column(db.Date, nullable=False)
    slot_type = db.Column(db.String(20), nullable=False)  # morning, evening
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'availability_date': self.availability_date.isoformat() if self.availability_date else None,
            'slot_type': self.slot_type,
            'is_available': self.is_available
        }
    
    def __repr__(self):
        return f'<DoctorAvailability {self.doctor_id} - {self.availability_date} - {self.slot_type}>'