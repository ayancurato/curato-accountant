from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "FINANCE"
    company_name: str
    country: str
    currency: str
    tax_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: UUID | None = None

class UserOut(UserBase):
    id: UUID
    company_id: UUID
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
