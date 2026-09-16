from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.db.models.responder import UserRole

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    responder_id: str
    display_name: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ResponderRead(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ResponderCreate(BaseModel):
    username: str
    email: str
    password: str
    display_name: str
    role: UserRole = UserRole.PEOPLE
