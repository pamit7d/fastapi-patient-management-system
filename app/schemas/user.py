from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    username: str
    full_name: str
    email: str
    phone: str

class UserCreate(UserBase):
    password: str
    role: str = "patient"
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None

class User(UserBase):
    id: int
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
