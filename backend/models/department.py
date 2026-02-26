from datetime import datetime
from database import db
from models.doctor import Doctor

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'doctor_count': len([d for d in Doctor.query.filter_by(
                specialization=self.name, 
                is_active=True
            ).all()])
        }
    
    def __repr__(self):
        return f'<Department {self.name}>'