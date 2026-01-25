from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class DoctorBase(BaseModel):
    full_name: str
    specialization: str
    availability: Optional[Dict[str, Any]] = {}

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    availability: Optional[Dict[str, Any]] = None

class Doctor(DoctorBase):
    id: int
    user_id: int
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True
