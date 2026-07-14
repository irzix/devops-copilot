from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ChatSessionCreate(BaseModel):
    """Payload to instantiate a new chat session."""
    title: str = Field(..., min_length=1, max_length=100)

class ChatSessionResponse(BaseModel):
    """Metadata response representing a chat session."""
    id: int
    title: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    """Metadata response representing a single message in a session thread."""
    id: int
    session_id: int
    sender: str
    content: str
    feedback_rating: Optional[str] = None
    feedback_comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageFeedbackRequest(BaseModel):
    """Request payload to submit message feedback."""
    feedback_rating: str = Field(..., min_length=1, max_length=50)
    feedback_comment: Optional[str] = Field(default=None, max_length=1000)

class AgentActionResponse(BaseModel):
    """Metadata response representing a queued server command approval."""
    id: str
    session_id: int
    server_id: int
    command: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
