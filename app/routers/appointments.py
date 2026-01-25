from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..models import Appointment, Doctor, User, AppointmentStatus
from ..schemas import appointment as schemas
from .deps import get_current_active_user, get_doctor

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/book", response_model=schemas.Appointment)
def book_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    
    # Check if patient profile exists
    if not current_user.patient_profile:
        raise HTTPException(status_code=400, detail="Please complete your patient profile first.")

    # 1. Double Booking Check (Doctor Side)
    existing_appt = db.query(Appointment).filter(
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.date == appointment.date,
        Appointment.time == appointment.time,
        Appointment.status != AppointmentStatus.CANCELLED
    ).first()
    
    if existing_appt:
        raise HTTPException(status_code=400, detail="This slot is already booked.")

    # 2. Patient-Doctor Active Limit Check (Restrictions)
    # Check if this patient already has a "Booked" appointment with this doctor
    active_appt = db.query(Appointment).filter(
        Appointment.patient_id == current_user.patient_profile.id,
        Appointment.doctor_id == appointment.doctor_id,
        Appointment.status == AppointmentStatus.BOOKED
    ).first()

    if active_appt:
        raise HTTPException(status_code=400, detail="You already have an upcoming appointment with this doctor. Please complete it first.")

    # 2. Check Doctor Availability (Optional: Validate against doctor.availability JSON)
    # For now, we trust the frontend/user to pick a valid slot, or rely on double booking check.

    new_appt = Appointment(
        patient_id=current_user.patient_profile.id,
        doctor_id=appointment.doctor_id,
        date=appointment.date,
        time=appointment.time,
        status=AppointmentStatus.BOOKED
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)
    return new_appt

from sqlalchemy.orm import joinedload

@router.get("/my", response_model=List[schemas.Appointment])
def get_my_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role == "patient":
        if not current_user.patient_profile: return []
        return db.query(Appointment).options(joinedload(Appointment.doctor)).filter(Appointment.patient_id == current_user.patient_profile.id).all()
    elif current_user.role == "doctor":
        if not current_user.doctor_profile: return []
        return db.query(Appointment).options(joinedload(Appointment.patient)).filter(Appointment.doctor_id == current_user.doctor_profile.id).all()
    elif current_user.role == "admin":
        return db.query(Appointment).options(joinedload(Appointment.doctor), joinedload(Appointment.patient)).all()
    
    return []

@router.put("/{appointment_id}/status", response_model=schemas.Appointment)
def update_status(
    appointment_id: int,
    update_data: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_doctor) # Only doctors update status/medical info normally
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    # Verify ownership
    if appt.doctor_id != current_user.doctor_profile.id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    if appt.status == AppointmentStatus.CANCELLED:
         raise HTTPException(status_code=400, detail="Cannot edit a cancelled appointment")

    if update_data.status:
        appt.status = update_data.status
    if update_data.diagnosis:
        appt.diagnosis = update_data.diagnosis
    if update_data.notes:
        appt.notes = update_data.notes
    if update_data.prescription:
        appt.prescription = update_data.prescription
        
    db.commit()
    db.refresh(appt)
    return appt
    db.commit()
    db.refresh(appt)
    return appt

@router.put("/{appointment_id}/cancel", response_model=schemas.Appointment)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Verify ownership (Patient can cancel their own, Doctor can cancel their assigned)
    is_patient_owner = current_user.role == "patient" and current_user.patient_profile and appt.patient_id == current_user.patient_profile.id
    is_doctor_owner = current_user.role == "doctor" and current_user.doctor_profile and appt.doctor_id == current_user.doctor_profile.id
    
    if not (is_patient_owner or is_doctor_owner):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")

    if appt.status == AppointmentStatus.CANCELLED:
         raise HTTPException(status_code=400, detail="Already cancelled")
         
    appt.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appt)
    return appt
