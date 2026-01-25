from pydantic import BaseModel, Field
from typing import Optional
import enum

class AppointmentStatus(str, enum.Enum):
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class AppointmentBase(BaseModel):
    doctor_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$") # YYYY-MM-DD
    time: str = Field(pattern=r"^([01]\d|2[0-3]):([0-5]\d)$") # HH:MM

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    prescription: Optional[str] = None

from .doctor import Doctor

class Appointment(AppointmentBase):
    id: int
    patient_id: int
    status: AppointmentStatus
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    prescription: Optional[str] = None
    
    # Nested Info
    doctor: Optional[Doctor] = None

    class Config:
        from_attributes = True
