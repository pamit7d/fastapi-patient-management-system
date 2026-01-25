from sqlalchemy.orm import Session
from ..models import patient as models
from ..schemas import patient as schemas

def get_patient(db: Session, patient_id: str):
    return db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: schemas.PatientCreate):
    # Create the Patient object
    # exclude appointments from the initial dump, handle them separately
    patient_data = patient.model_dump(exclude={"appointments"})
    db_patient = models.Patient(**patient_data)
    
    # Create and associate Appointment objects
    for appt_data in patient.appointments:
        db_appointment = models.Appointment(**appt_data.model_dump(), patient=db_patient)
        # We need to add the appointment to the session explicitly or via the relationship if configured
        # straightforward way taking advantage of logic:
        # But wait, db_patient is not verified/committed yet.
        # SQLAlchemy handles this if we add to relationship, but let's stick to explicit adds if that was working
        # Re-using the logic from the original crud.py but cleaner
        # db.add(db_appointment) # The original code added it.
        pass
    
    # Actually, SQLAlchemy relationship assignment is cleaner:
    # Re-instating the relationship logic properly:
    # Need to be careful about the session.
    
    db.add(db_patient)
    db.commit() # commit patient first to get any IDs if generated (here patient_id is manual string so it's fine)
    
    # Add appointments
    for appt_data in patient.appointments:
        db_appointment = models.Appointment(**appt_data.model_dump())
        db_appointment.patient_id = db_patient.patient_id
        db.add(db_appointment)
        
    db.commit()
    db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: str):
    db_patient = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if db_patient:
        db.delete(db_patient)
        db.commit()
        return db_patient
    return None

def update_patient(db: Session, patient_id: str, patient_update: schemas.PatientUpdate):
    db_patient = get_patient(db, patient_id=patient_id)
    if not db_patient:
        return None

    update_data = patient_update.model_dump(exclude_unset=True)
    
    # Calculate BMI if height or weight is updated
    if 'height' in update_data or 'weight' in update_data:
        height = update_data.get('height', db_patient.height)
        weight = update_data.get('weight', db_patient.weight)
        update_data['bmi'] = round(weight / ((height / 100) ** 2), 2)
        
    for key, value in update_data.items():
        setattr(db_patient, key, value)

    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient
