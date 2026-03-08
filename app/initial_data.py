from sqlalchemy.orm import Session
from .crud.user import get_user_by_username, create_user
from .schemas.user import UserCreate
from .core.config import settings
from .core.database import SessionLocal

def init_db():
    db = SessionLocal()
    try:
        admin_user = get_user_by_username(db, "admin")
        if not admin_user:
            print("Creating Admin User...")
            admin_data = UserCreate(
                username="admin",
                password="admin", 
                role="admin",
                full_name="Admin User",
                email="admin@campusx.com",
                phone="0000000000"
            )
            create_user(db, admin_data)
            print("Admin User created.")
        else:
            print("Admin User already exists.")
    finally:
        db.close()
