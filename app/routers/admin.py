from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..models import User, Doctor, Patient, Appointment
from ..schemas import user as user_schema
from ..crud import user as crud_user
from .deps import get_admin, get_db, get_current_active_user

router = APIRouter(prefix="/admin", tags=["Admin"])

class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    specialization: Optional[str] = None

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db), current_user: User = Depends(get_admin)):
    return {
        "doctors": db.query(Doctor).count(),
        "patients": db.query(Patient).count(),
        "appointments": db.query(Appointment).count()
    }

@router.post("/doctors", response_model=user_schema.User)
def create_doctor(
    user: user_schema.UserCreate, 
    full_name: str, 
    specialization: str,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin)
):
    # 1. Create User
    user.role = "doctor"
    db_user = crud_user.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = crud_user.create_user(db=db, user=user)
    
    # 2. Create Doctor Profile
    db_doctor = Doctor(
        user_id=new_user.id,
        full_name=full_name,
        specialization=specialization,
        availability={"weekly": {}, "specific_dates": {}}
    )
    db.add(db_doctor)
    db.commit()
    
    return new_user

@router.get("/doctors")
def get_all_doctors(
    name: Optional[str] = None,
    specialization: Optional[str] = None,
    search: Optional[str] = None, # Keep for backward compat/admin generic
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Doctor)
    
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Doctor.full_name.ilike(search_fmt)) | 
            (Doctor.specialization.ilike(search_fmt))
        )
    
    if name:
        query = query.filter(Doctor.full_name.ilike(f"%{name}%"))
    
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
        
    return query.all()

# --- NEW Admin Endpoints ---

@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Cascade handles profiles + appointments
    db.delete(user)
    db.commit()
    return

@router.put("/doctors/{id}")
def update_doctor(
    id: int,
    doctor_in: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin)
):
    doctor = db.query(Doctor).filter(Doctor.id == id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if doctor_in.full_name: doctor.full_name = doctor_in.full_name
    if doctor_in.specialization: doctor.specialization = doctor_in.specialization
    
    db.commit()
    return {"message": "Doctor updated"}
