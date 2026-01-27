# CampusX Patient Management System

A robust, full-stack patient management system built with **FastAPI** and **PostgreSQL**. Designed for scalability, security, and ease of deployment on **Render**.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)
![Render](https://img.shields.io/badge/Deploy%20on-Render-black?style=for-the-badge&logo=render)

## 🚀 Features

### 👨‍⚕️ Admin Module
- **Dashboard**: Real-time statistics (Doctor/Patient counts).
- **Doctor Management**: Create, view, and search doctors.
- **Analytics**: Monitor appointment trends.

### 🩺 Doctor Module
- **Availability**: Manage weekly schedules and specific dates.
- **Appointments**: View upcoming bookings and update status (Pending -> Completed).
- **Emergency**: Cancel an entire day's appointments with one click.

### 🏥 Patient Module
- **Profile**: Create and manage personal health profile.
- **Booking**: Search doctors and book appointments.
- **History**: View past and upcoming appointments.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (Production) / SQLite (Local Dev)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Deployment**: Docker & Render

---

## For demo & testing purposes only
- An admin user is automatically created at application startup:
   - Username: admin
   - Password: admin123
 
---


## 📂 Project Structure

```bash
.
├── app/
│   ├── core/          # Config & Database logic
│   ├── crud/          # DB interactions (Create, Read, Update, Delete)
│   ├── models/        # SQLAlchemy Database Models
│   ├── routers/       # API Endpoints (Admin, Doctor, Patient)
│   ├── schemas/       # Pydantic Models for Validation
│   ├── static/        # Frontend Static Files
│   └── tests/         # E2E Verification Scripts
├── render.yaml        # Render Deployment Config
├── Dockerfile         # Docker Container Config
└── requirements.txt   # Python Dependencies
```

---

## ⚡ Quick Start (Local)

### Prerequisites
- Python 3.10+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/fastapi-patient-system.git
cd fastapi-patient-system
```

### 2. Setup Environment
Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Application
```bash
./entrypoint.sh
# Check http://localhost:8000/docs for Swagger UI
```

---

## 🧪 Testing
We have included a robust End-to-End (E2E) verification script.

```bash
# Ensure server is running on localhost:8000
python app/tests/e2e_verify.py
```

---

## ☁️ Deployment on Render

This project is configured for **Zero-Config Deployment** on Render.

1. **Push to GitHub**: Make sure your repo is public or accessible.
2. **New Web Service**: Connect your repo on Render.
3. **Environment Variables**:
   - `DATABASE_URL`: (Add your specific Render Postgres Internal URL here)
   - `SECRET_KEY`: (Generate a random string)
   - `ALGORITHM`: `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `30`
4. **Deploy**: Render will automatically detect the `docker` environment or `python` build command.

> **Note**: This app uses a hybrid database approach. It defaults to SQLite locally but switches to PostgreSQL automatically when `DATABASE_URL` contains "postgres".

---

## 🛡️ License
This project is for educational purposes. 
