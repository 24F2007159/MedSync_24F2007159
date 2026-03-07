import csv
import os
import io
from celery_app import celery
from flask import Flask
from database import db
from config import Config


def create_app():
    app = Flask(__name__, static_folder='../../frontend', static_url_path='/static')
    app.config.from_object(Config)
    db.init_app(app)
    return app


@celery.task(bind=True, name='celery_tasks.export_tasks.export_patient_csv')
def export_patient_csv(self, patient_id):
    """
    Async task: export all treatment records for a patient as CSV,
    then email the file to the patient.
    """
    app = create_app()
    with app.app_context():
        from models import Patient, Appointment, Treatment
        from flask_mail import Mail, Message

        patient = Patient.query.get(patient_id)
        if not patient:
            return {'success': False, 'message': 'Patient not found'}

        # collect treatment data
        treatments = (
            db.session.query(Treatment)
            .join(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .order_by(Treatment.created_at.desc())
            .all()
        )

        # build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Patient ID', 'Username', 'Consulting Doctor', 'Specialization',
            'Appointment Date', 'Appointment Time', 'Diagnosis',
            'Prescription', 'Notes', 'Next Visit'
        ])

        for t in treatments:
            apt = Appointment.query.get(t.appointment_id)
            doctor = apt.doctor if apt else None
            writer.writerow([
                patient.id,
                patient.user.username if patient.user else '',
                doctor.name if doctor else '',
                doctor.specialization if doctor else '',
                apt.appointment_date.isoformat() if apt else '',
                str(apt.appointment_time) if apt else '',
                t.diagnosis or '',
                t.prescription or '',
                t.notes or '',
                t.next_visit.isoformat() if t.next_visit else ''
            ])

        csv_content = output.getvalue()
        output.close()

        # send via email
        patient_email = patient.user.email if patient.user else None
        if patient_email:
            try:
                mail_app = Flask(__name__)
                mail_app.config.from_object(Config)
                mail = Mail(mail_app)

                with mail_app.app_context():
                    msg = Message(
                        subject='MedSync - Your Treatment History Export',
                        sender=Config.MAIL_USERNAME,
                        recipients=[patient_email]
                    )
                    msg.body = (
                        f'Dear {patient.name},\n\n'
                        'Please find your treatment history attached as a CSV file.\n\n'
                        'Regards,\nMedSync Team'
                    )
                    msg.attach(
                        filename='treatment_history.csv',
                        content_type='text/csv',
                        data=csv_content
                    )
                    mail.send(msg)
            except Exception as e:
                return {'success': False, 'message': f'CSV generated but email failed: {str(e)}'}

        return {
            'success': True,
            'message': f'Export complete. Sent to {patient_email}',
            'rows': len(treatments)
        }
