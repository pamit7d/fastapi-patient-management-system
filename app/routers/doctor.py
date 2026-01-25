from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from ..core.database import get_db
from ..models import User, Doctor, Appointment, AppointmentStatus
from ..schemas import doctor as schemas
from .deps import get_doctor, get_current_active_user

router = APIRouter(prefix="/doctor", tags=["Doctor"])

@router.post("/availability")
def set_availability(
    availability: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_doctor)
):
    """
    Expected format:
    {
        "weekly": {"Mon": ["09:00", "10:00"], "Tue": []},
        "specific_dates": {"2026-01-27": ["08:00", "12:00"]}
    }
    """
    doctor = current_user.doctor_profile
    if not doctor:
         raise HTTPException(status_code=404, detail="Doctor profile not found")
         
    doctor.availability = availability
    db.commit()
    return {"message": "Availability updated", "availability": doctor.availability}

@router.get("/availability/settings")
def get_availability_settings(current_user: User = Depends(get_doctor)):
    return current_user.doctor_profile.availability or {"weekly": {}, "specific_dates": {}}

@router.get("/appointments")
def get_my_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_doctor)):
    doctor = current_user.doctor_profile
    if not doctor:
         raise HTTPException(status_code=404, detail="Doctor profile not found")
    
    return db.query(Appointment).filter(Appointment.doctor_id == doctor.id).all()

# --- New Endpoint for Public Availability ---
@router.get("/{doctor_id}/availability")
def get_doctor_availability(
    doctor_id: int, 
    start_date: date, 
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if (end_date - start_date).days > 30:
        raise HTTPException(status_code=400, detail="Range too large")

    availability = doctor.availability or {}
    weekly = availability.get("weekly", {})
    specific = availability.get("specific_dates", {})
    
    # helper
    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # 1. Get existing appointments
    # SQLite/Postgres compatibility: Appointment.date is String (YYYY-MM-DD)
    # We must compare strings, not date objects
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    existing_appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date >= start_str,
        Appointment.date <= end_str,
        Appointment.status != AppointmentStatus.CANCELLED
    ).all()
    
    booked_map = {} # "2026-01-25": ["09:00", "10:00"]
    for a in existing_appts:
        d_str = a.date # Already string
        if d_str not in booked_map: booked_map[d_str] = []
        booked_map[d_str].append(a.time)

    result = {}
    curr = start_date
    while curr <= end_date:
        d_str = curr.isoformat()
        day_name = WEEKDAYS[curr.weekday()]
        
        # Determine base slots
        if d_str in specific:
            slots = specific[d_str] # Override takes precedence
        else:
            slots = weekly.get(day_name, []) # Fallback to weekly
            
        # Filter booked
        booked_today = booked_map.get(d_str, [])
        final_slots = [s for s in slots if s not in booked_today]
        
        result[d_str] = final_slots
        curr += timedelta(days=1)
        
    return result

@router.get("/me", response_model=schemas.Doctor)
def get_doctor_profile(current_user: User = Depends(get_doctor)):
    doc = current_user.doctor_profile
    # Inject user fields into the schema response
    return {
        **doc.__dict__,
        "email": current_user.email,
        "phone": current_user.phone
    }

@router.put("/me", response_model=schemas.Doctor)
def update_doctor_profile(
    doctor_update: schemas.DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_doctor)
):
    doctor = current_user.doctor_profile
    if doctor_update.full_name is not None:
        doctor.full_name = doctor_update.full_name
        current_user.full_name = doctor_update.full_name # Keep in sync
    if doctor_update.specialization is not None:
        doctor.specialization = doctor_update.specialization
    if doctor_update.email is not None:
        current_user.email = doctor_update.email
    if doctor_update.phone is not None:
        current_user.phone = doctor_update.phone
    
    db.commit()
    db.refresh(doctor)
    db.refresh(current_user)
    return {
        **doctor.__dict__,
        "email": current_user.email,
        "phone": current_user.phone
    }

@router.post("/cancel-day")
def cancel_appointments_for_day(
    target_date: str,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_doctor)
):
    doctor = current_user.doctor_profile
    if not doctor:
         raise HTTPException(status_code=404, detail="Doctor profile not found")
         
    # Update all active bookings for this date/doctor
    appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date == target_date,
        Appointment.status == AppointmentStatus.BOOKED
    ).all()
    
    count = 0
    for a in appts:
        a.status = AppointmentStatus.CANCELLED
        count += 1
        
    db.commit()
    return {"message": f"Emergency cancelled {count} appointments for {target_date}"}
