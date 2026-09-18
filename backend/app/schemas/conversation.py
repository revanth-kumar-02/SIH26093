from pydantic import BaseModel, Field
from typing import Optional

class MessageSendRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message text from victim")
    language: Optional[str] = Field(None, description="ISO-639-1 language code e.g. en, ta, hi")
    input_source: Optional[str] = Field(default="TEXT", description="Input source: TEXT, VOICE, SYSTEM, AI")

class MessageResponse(BaseModel):
    message_id: str
    response: str
    status: str = "received"
    timestamp: Optional[str] = None
