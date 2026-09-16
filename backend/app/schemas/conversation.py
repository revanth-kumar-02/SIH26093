from pydantic import BaseModel, Field
from typing import Optional

class MessageSendRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message text from victim")

class MessageResponse(BaseModel):
    message_id: str
    response: str
    status: str = "received"
    timestamp: Optional[str] = None
