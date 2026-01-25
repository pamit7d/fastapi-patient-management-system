from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..models import Patient, User
from ..schemas import patient as patient_schema
from .deps import get_current_active_user, get_admin, get_doctor

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("/", response_model=patient_schema.Patient)
def create_patient_profile(
    patient: patient_schema.PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "patient":
        raise HTTPException(status_code=400, detail="Only patients can have patient profiles")
        
    if current_user.patient_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # Create patient linked to user
    db_patient = Patient(
        user_id=current_user.id,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        phone=patient.phone,
        city=patient.city 
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.get("/me", response_model=patient_schema.Patient)
def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.patient_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = current_user.patient_profile
    return {
        **profile.__dict__,
        "patient_id": profile.id, # Explicitly map id to patient_id
        "email": current_user.email,
        "phone": current_user.phone 
    }

@router.get("/{id}", response_model=patient_schema.Patient)
def get_patient_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Authorization: Admin, Doctor, or Self
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    is_self = (current_user.patient_profile and current_user.patient_profile.id == id)
    is_authorized = (current_user.role in ["admin", "doctor"]) or is_self
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return {
        **patient.__dict__,
        "patient_id": patient.id,
        "email": patient.user.email,
        "phone": patient.user.phone
    }

@router.put("/{id}", response_model=patient_schema.Patient)
def update_patient_detail(
    id: int,
    patient_in: patient_schema.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Auth: Admin, Doctor, or Self
    is_self = (current_user.patient_profile and current_user.patient_profile.id == id)
    is_authorized = (current_user.role in ["admin", "doctor"]) or is_self
    
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update fields if provided
    if patient_in.name is not None: 
        patient.name = patient_in.name
        if is_self: current_user.full_name = patient_in.name
        else: patient.user.full_name = patient_in.name

    if patient_in.age is not None: patient.age = patient_in.age
    if patient_in.gender is not None: patient.gender = patient_in.gender
    
    if patient_in.phone is not None: 
        patient.phone = patient_in.phone
        if is_self: current_user.phone = patient_in.phone
        else: patient.user.phone = patient_in.phone

    if patient_in.email is not None:
        if is_self: current_user.email = patient_in.email
        else: patient.user.email = patient_in.email

    if patient_in.city is not None: patient.city = patient_in.city
    if patient_in.status is not None: patient.status = patient_in.status
    
    db.commit()
    db.refresh(patient)
    return {
        **patient.__dict__,
        "patient_id": patient.id,
        "email": patient.user.email,
        "phone": patient.user.phone
    }

@router.get("/", response_model=List[patient_schema.Patient])
def read_all_patients(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) 
):
    # Allow doctors to see list too
    if current_user.role not in ["admin", "doctor"]:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    query = db.query(Patient)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Patient.name.ilike(search_fmt)) |
            (Patient.phone.ilike(search_fmt))
        )
    patients = query.all()
    results = []
    for p in patients:
        results.append({
            "id": p.id,
            "patient_id": p.id,
            "user_id": p.user_id,
            "name": p.name,
            "age": p.age or 0,
            "gender": p.gender or "Unknown",
            "phone": p.phone,
            "city": p.city or "Unknown",
            "email": p.user.email if p.user else None
        })
    return results
