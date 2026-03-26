"""Chat router — aliases /chat/* to fellowship-chat logic for frontend compatibility."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone

from app.database import get_db
from app.models.chat import Conversation, ConversationParticipant, Message
from app.models.user import User
from app.schemas.chat import ConversationCreate, MessageSend
from app.utils.security import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat (Fellowship)"])


async def _build_conversation(db, conv, current_user):
    participants = []
    for p in conv.participants:
        u = (await db.execute(select(User).where(User.id == p.user_id))).scalar_one_or_none()
        participants.append({
            "id": p.user_id,
            "name": u.full_name if u else None,
            "avatar_url": getattr(u, "avatar_url", None) if u else None,
        })

    # Last message
    last_msg = (await db.execute(
        select(Message).where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc()).limit(1)
    )).scalar_one_or_none()

    # Unread count
    my_part = None
    for p in conv.participants:
        if p.user_id == current_user.id:
            my_part = p
            break
    unread = 0
    if my_part and my_part.last_read_at:
        unread = (await db.execute(
            select(func.count()).where(
                Message.conversation_id == conv.id,
                Message.created_at > my_part.last_read_at,
                Message.sender_id != current_user.id,
            )
        )).scalar() or 0

    return {
        "id": conv.id,
        "name": conv.name,
        "type": conv.conversation_type or "direct",
        "last_message": last_msg.content if last_msg else None,
        "last_message_at": last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None,
        "unread_count": unread,
        "participants": participants,
    }


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    my_convos = (await db.execute(
        select(ConversationParticipant.conversation_id)
        .where(ConversationParticipant.user_id == current_user.id)
    )).scalars().all()

    if not my_convos:
        return {"data": []}

    convos = (await db.execute(
        select(Conversation)
        .where(Conversation.id.in_(my_convos), Conversation.is_active == True)
        .order_by(Conversation.last_message_at.desc())
    )).scalars().all()

    items = [await _build_conversation(db, c, current_user) for c in convos]
    return {"data": items}


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = (await db.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"data": await _build_conversation(db, conv, current_user)}


@router.get("/conversations/{conv_id}/messages")
async def get_messages(
    conv_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = (await db.execute(
        select(Message).where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .offset(offset).limit(limit)
    )).scalars().all()

    items = []
    for m in messages:
        sender = (await db.execute(select(User).where(User.id == m.sender_id))).scalar_one_or_none()
        items.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": sender.full_name if sender else None,
            "sender_avatar": getattr(sender, "avatar_url", None) if sender else None,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "is_read": True,
        })
    items.reverse()  # Oldest first
    return {"data": items}


@router.post("/conversations", status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation with participant_ids + first message."""
    conv = Conversation(
        conversation_type="direct" if len(data.participant_user_ids or data.participant_ids or []) == 1 else "group",
        created_by=current_user.id,
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)

    # Add participants
    all_ids = set(data.participant_user_ids or data.participant_ids or []) | {current_user.id}
    for uid in all_ids:
        db.add(ConversationParticipant(
            conversation_id=conv.id, user_id=uid, role="member",
            joined_at=datetime.now(timezone.utc),
            last_read_at=datetime.now(timezone.utc),
        ))

    # First message
    msg = Message(
        conversation_id=conv.id, sender_id=current_user.id,
        content=data.message or "",
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    await db.commit()

    return {"data": {
        "conversation_id": conv.id,
        "message": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
    }}
