from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SessionCreateRequest(BaseModel):
    language: str = Field(default="en", description="Selected language code (e.g. 'en', 'hi')")

class SessionResponse(BaseModel):
    session_id: str
    language: str
    status: str = "active"
    created_at: Optional[str] = None
