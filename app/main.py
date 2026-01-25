from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .core.database import engine, Base
from .routers import auth, users, patients, appointments
from .models import User, Patient, Doctor, Appointment # Ensure models are loaded

# Create database tables
# In production, use Alembic migrations instead of create_all
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CampusX Patient Management System",
    description="A robust FastAPI application for managing patient records.",
    version="1.0.0"
)

from .initial_data import init_db
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(appointments.router)
from .routers import admin, doctor
app.include_router(admin.router)
app.include_router(doctor.router)

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")
