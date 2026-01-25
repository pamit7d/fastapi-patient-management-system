from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class AppointmentStatus(str, enum.Enum):
    BOOKED = "Booked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    
    date = Column(String) # YYYY-MM-DD
    time = Column(String) # HH:MM
    
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.BOOKED)
    
    diagnosis = Column(String, nullable=True) # Medical outcome
    notes = Column(String, nullable=True)    # Doctor's private notes
    prescription = Column(String, nullable=True) # Medicines
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
