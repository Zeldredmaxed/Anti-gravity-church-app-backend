"""Chat system Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    type: str = "direct"  # direct, group, church_wide
    name: Optional[str] = None
    participant_user_ids: list[int] = Field(default=[], alias="participant_ids")
    participant_ids: Optional[list[int]] = None
    message: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    church_id: int
    type: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_by: int
    is_active: bool
    last_message_at: Optional[datetime] = None
    created_at: datetime
    participants: list["ParticipantResponse"] = []
    unread_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    role: str
    last_read_at: Optional[datetime] = None
    joined_at: datetime

    model_config = {"from_attributes": True}


# --- Message Schemas ---

class MessageSend(BaseModel):
    content: Optional[str] = None
    message_type: str = "text"
    media_url: Optional[str] = None
    reply_to: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: Optional[str] = None
    content: Optional[str] = None
    message_type: str
    media_url: Optional[str] = None
    reply_to: Optional[int] = None
    reactions: Optional[dict] = None
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageReaction(BaseModel):
    emoji: str = Field(..., max_length=10)


class MarkReadRequest(BaseModel):
    pass  # Just needs to be called, timestamp is server-side
