from sqlalchemy.orm import Session
from ..models import patient as models
from ..schemas import patient as schemas

def create_appointment(db: Session, appointment: schemas.AppointmentCreateIndependent):
    # Determine the next ID (simple auto-increment logic for demo)
    # In prod, use UUID or DB sequence. Here we count existing.
    count = db.query(models.Appointment).count()
    new_id = f"A{1000 + count + 1}"
    
    db_appointment = models.Appointment(
        appointment_id=new_id,
        date=appointment.date,
        time=appointment.time,
        doctor=appointment.doctor,
        department=appointment.department,
        patient_id=appointment.patient_id
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def get_appointments_by_patient(db: Session, patient_id: str):
    return db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
