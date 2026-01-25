from sqlalchemy.orm import Session
from ..models import user as models
from ..models.patient import Patient
from ..schemas import user as schemas
from ..core.security import get_password_hash

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Automatically create Patient profile if role is patient
    if user.role == "patient":
        db_patient = Patient(
            user_id=db_user.id,
            name=user.full_name,
            age=user.age,
            gender=user.gender,
            phone=user.phone,
            city=user.city
        )
        db.add(db_patient)
        db.commit()

    return db_user
