from celery_app import celery
from flask import Flask
from database import db
from config import Config


def create_app():
    app = Flask(__name__, static_folder='../../frontend', static_url_path='/static')
    app.config.from_object(Config)
    db.init_app(app)
    return app


@celery.task(name='celery_tasks.email_tasks.send_daily_reminders')
def send_daily_reminders():
    """
    Scheduled task (runs daily at 8 AM IST):
    Send appointment reminder emails to patients with bookings today.
    """
    app = create_app()
    with app.app_context():
        from datetime import date
        from models import Appointment, Patient
        from flask_mail import Mail, Message

        today = date.today()
        appointments = (
            Appointment.query
            .filter_by(appointment_date=today, status='booked')
            .all()
        )

        if not appointments:
            return {'sent': 0, 'message': 'No appointments today'}

        mail_app = Flask(__name__)
        mail_app.config.from_object(Config)
        mail = Mail(mail_app)

        sent = 0
        errors = []

        with mail_app.app_context():
            for apt in appointments:
                patient = apt.patient
                doctor = apt.doctor
                if not patient or not patient.user:
                    continue

                patient_email = patient.user.email
                apt_time = apt.appointment_time.strftime('%I:%M %p') if apt.appointment_time else ''

                try:
                    msg = Message(
                        subject='MedSync - Appointment Reminder for Today',
                        sender=Config.MAIL_USERNAME,
                        recipients=[patient_email]
                    )
                    msg.html = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #0d6efd;">MedSync - Appointment Reminder</h2>
                        <p>Dear <strong>{patient.name}</strong>,</p>
                        <p>This is a reminder that you have an appointment scheduled <strong>today</strong>.</p>
                        <table style="border-collapse: collapse; margin: 15px 0;">
                            <tr>
                                <td style="padding: 6px 12px; font-weight: bold;">Doctor</td>
                                <td style="padding: 6px 12px;">{doctor.name if doctor else 'N/A'}</td>
                            </tr>
                            <tr style="background:#f8f9fa;">
                                <td style="padding: 6px 12px; font-weight: bold;">Specialization</td>
                                <td style="padding: 6px 12px;">{doctor.specialization if doctor else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 12px; font-weight: bold;">Date</td>
                                <td style="padding: 6px 12px;">{apt.appointment_date}</td>
                            </tr>
                            <tr style="background:#f8f9fa;">
                                <td style="padding: 6px 12px; font-weight: bold;">Time</td>
                                <td style="padding: 6px 12px;">{apt_time}</td>
                            </tr>
                        </table>
                        <p>Please arrive 10 minutes early. If you need to cancel, log in to MedSync.</p>
                        <p style="color: #666;">Regards,<br><strong>MedSync Team</strong></p>
                    </body>
                    </html>
                    """
                    mail.send(msg)
                    sent += 1
                except Exception as e:
                    errors.append(f'{patient_email}: {str(e)}')

        return {'sent': sent, 'errors': errors}


@celery.task(name='celery_tasks.email_tasks.send_monthly_reports')
def send_monthly_reports():
    """
    Scheduled task (runs on the 1st of each month at 9 AM IST):
    Send monthly activity report to each doctor via email.
    """
    app = create_app()
    with app.app_context():
        from datetime import date
        from models import Doctor, Appointment, Treatment
        from flask_mail import Mail, Message

        today = date.today()
        # report covers the previous full month
        first_of_this_month = today.replace(day=1)
        if first_of_this_month.month == 1:
            first_of_last_month = first_of_this_month.replace(year=first_of_this_month.year - 1, month=12)
        else:
            first_of_last_month = first_of_this_month.replace(month=first_of_this_month.month - 1)
        last_of_last_month = first_of_this_month

        month_name = first_of_last_month.strftime('%B %Y')

        doctors = Doctor.query.filter_by(is_active=True).all()

        mail_app = Flask(__name__)
        mail_app.config.from_object(Config)
        mail = Mail(mail_app)

        sent = 0
        errors = []

        with mail_app.app_context():
            for doctor in doctors:
                if not doctor.user:
                    continue

                doctor_email = doctor.user.email

                appointments = (
                    Appointment.query
                    .filter(
                        Appointment.doctor_id == doctor.id,
                        Appointment.appointment_date >= first_of_last_month,
                        Appointment.appointment_date < last_of_last_month
                    )
                    .order_by(Appointment.appointment_date.asc())
                    .all()
                )

                total = len(appointments)
                completed = sum(1 for a in appointments if a.status == 'completed')
                cancelled = sum(1 for a in appointments if a.status == 'cancelled')

                # build appointment rows for the HTML report
                rows_html = ''
                for apt in appointments:
                    patient_name = apt.patient.name if apt.patient else 'N/A'
                    treatment = apt.treatment
                    diagnosis = treatment.diagnosis if treatment else '-'
                    prescription = treatment.prescription if treatment else '-'
                    apt_time = apt.appointment_time.strftime('%I:%M %p') if apt.appointment_time else ''
                    rows_html += f"""
                    <tr>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{apt.appointment_date}</td>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{apt_time}</td>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{patient_name}</td>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{apt.status.capitalize()}</td>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{diagnosis}</td>
                        <td style="padding:6px 10px;border:1px solid #dee2e6;">{prescription}</td>
                    </tr>
                    """

                html_report = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333; max-width: 900px; margin: auto;">
                    <div style="background:#0d6efd;color:white;padding:20px 30px;border-radius:8px 8px 0 0;">
                        <h1 style="margin:0;">MedSync Monthly Report</h1>
                        <p style="margin:5px 0 0;">{month_name}</p>
                    </div>
                    <div style="padding:20px 30px;background:#f8f9fa;">
                        <p>Dear <strong>Dr. {doctor.name}</strong>,</p>
                        <p>Here is your activity summary for <strong>{month_name}</strong>.</p>

                        <div style="display:flex;gap:20px;margin:20px 0;">
                            <div style="background:#0d6efd;color:white;padding:15px 25px;border-radius:8px;text-align:center;">
                                <div style="font-size:2rem;font-weight:700;">{total}</div>
                                <div>Total Appointments</div>
                            </div>
                            <div style="background:#198754;color:white;padding:15px 25px;border-radius:8px;text-align:center;">
                                <div style="font-size:2rem;font-weight:700;">{completed}</div>
                                <div>Completed</div>
                            </div>
                            <div style="background:#dc3545;color:white;padding:15px 25px;border-radius:8px;text-align:center;">
                                <div style="font-size:2rem;font-weight:700;">{cancelled}</div>
                                <div>Cancelled</div>
                            </div>
                        </div>

                        <h3>Appointment Details</h3>
                        {'<p style="color:#666;">No appointments this month.</p>' if not appointments else f"""
                        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
                            <thead>
                                <tr style="background:#e9ecef;">
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Date</th>
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Time</th>
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Patient</th>
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Status</th>
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Diagnosis</th>
                                    <th style="padding:8px 10px;border:1px solid #dee2e6;text-align:left;">Prescription</th>
                                </tr>
                            </thead>
                            <tbody>{rows_html}</tbody>
                        </table>
                        """}

                        <p style="margin-top:30px;color:#666;">
                            This report was automatically generated by MedSync.<br>
                            <strong>MedSync Team</strong>
                        </p>
                    </div>
                </body>
                </html>
                """

                try:
                    msg = Message(
                        subject=f'MedSync - Monthly Activity Report ({month_name})',
                        sender=Config.MAIL_USERNAME,
                        recipients=[doctor_email]
                    )
                    msg.html = html_report
                    mail.send(msg)
                    sent += 1
                except Exception as e:
                    errors.append(f'{doctor_email}: {str(e)}')

        return {'sent': sent, 'errors': errors, 'month': month_name}
