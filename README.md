# MedSync — Hospital Management System (V2)

A full-stack Hospital Management System built for **MAD-II (Modern Application Development II)**.

## Overview

MedSync supports three distinct user roles, each with a tailored workflow:

| Role | Capabilities |
|------|-------------|
| **Admin** | Manages doctors, patients, departments, and appointments |
| **Doctor** | Views appointments, sets availability, adds treatment records |
| **Patient** | Books/cancels appointments, views medical history, exports CSV |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask, SQLAlchemy, SQLite |
| Frontend | Vue.js 3 (CDN), Bootstrap 5 |
| Auth | JWT (flask-jwt-extended) |
| Cache | Redis |
| Async Jobs | Celery + Redis |
| Email | Flask-Mail (Gmail SMTP) |

## Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily reminders | 8 AM IST daily | Emails patients with appointments today |
| Monthly report | 1st of each month | HTML activity report emailed to each doctor |
| CSV export | User-triggered | Patient treatment history exported and emailed |

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Copy `backend/.env.example` to `backend/.env` and fill in your own values:

```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

> **Note:** Never commit a real `.env` file. Use a [Gmail App Password](https://support.google.com/accounts/answer/185833) rather than your actual account password.

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

## Default Accounts

On first run, a seed script creates a default **Admin** account. Doctor accounts are created by the Admin through the app — no credentials are hardcoded.

> See `backend/seed.py` (or your seeding script) for how the initial admin account is generated, and change the password immediately after first login.

## License

Add a license (e.g. MIT) if you intend this repo to be public.
