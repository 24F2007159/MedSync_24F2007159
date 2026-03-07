# MedSync - Hospital Management System (V2)

A full-stack Hospital Management System built for MAD-II (Modern Application Development II).

## Roles
- **Admin** — Manages doctors, patients, departments, and appointments
- **Doctor** — Views appointments, sets availability, adds treatment records
- **Patient** — Books/cancels appointments, views medical history, exports CSV

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Flask, SQLAlchemy, SQLite |
| Frontend | Vue.js 3 (CDN), Bootstrap 5 |
| Auth | JWT (flask-jwt-extended) |
| Cache | Redis |
| Async Jobs | Celery + Redis |
| Email | Flask-Mail (Gmail SMTP) |

## Setup

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment
Edit `backend/.env`:
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

### 3. Start Redis (required for caching and Celery)
```bash
redis-server
```

### 4. Run the Flask app
```bash
cd backend
python app.py
```

### 5. Run Celery worker (for async jobs)
```bash
cd backend
celery -A celery_app worker --loglevel=info
```

### 6. Run Celery beat scheduler (for periodic jobs)
```bash
cd backend
celery -A celery_app beat --loglevel=info
```

## Default credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | (set by admin) | doctor123 |

## Background Jobs
| Job | Schedule | Description |
|-----|----------|-------------|
| Daily reminders | 8 AM IST daily | Emails patients with appointments today |
| Monthly report | 1st of each month | HTML activity report emailed to each doctor |
| CSV export | User-triggered | Patient treatment history exported and emailed |
