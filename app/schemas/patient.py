from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    city: str

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None 
    
class Patient(PatientBase):
    id: int
    patient_id: int 
    user_id: int
    email: Optional[str] = None
    
    class Config:
        from_attributes = True
        # If model `id` maps to `patient_id` in schema, we might need alias.
        # Let's check model again. Model: id (PK). Router returns db_patient. Schema Patient has id. 
        # But frontend uses p.patient_id. 
        # Let's add patient_id property to model or schema Alias.
        # Actually Model 'Patient' doesn't seem to have 'patient_id' column, just 'id'. 
        # Frontend likely expects 'patient_id' because I used it in JS. 
        # Let's add a validator or just field alias.
        

