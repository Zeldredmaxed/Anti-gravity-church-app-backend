"""Chat router: conversations, messages, read receipts, reactions."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone

from app.database import get_db
from app.models.chat import Conversation, ConversationParticipant, Message
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate, ConversationResponse, ParticipantResponse,
    MessageSend, MessageResponse, MessageReaction,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


def _build_participant(p, user_name=None):
    return ParticipantResponse(
        id=p.id, user_id=p.user_id, user_name=user_name,
        role=p.role, last_read_at=p.last_read_at, joined_at=p.joined_at)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """List all conversations for the current user."""
    my_convos = (await db.execute(
        select(ConversationParticipant.conversation_id)
        .where(ConversationParticipant.user_id == current_user.id)
    )).scalars().all()

    if not my_convos:
        return []

    convos = (await db.execute(
        select(Conversation)
        .where(Conversation.id.in_(my_convos), Conversation.is_active == True)
        .order_by(Conversation.last_message_at.desc())
    )).scalars().all()

    items = []
    for c in convos:
        participants = []
        for p in c.participants:
            u = (await db.execute(select(User).where(User.id == p.user_id))).scalar_one_or_none()
            participants.append(_build_participant(p, u.full_name if u else None))

        # Unread count
        my_p = next((p for p in c.participants if p.user_id == current_user.id), None)
        unread = 0
        if my_p and my_p.last_read_at:
            unread = (await db.execute(
                select(func.count()).where(
                    Message.conversation_id == c.id,
                    Message.created_at > my_p.last_read_at,
                    Message.sender_id != current_user.id,
                    Message.is_deleted == False)
            )).scalar() or 0
        elif my_p:
            unread = (await db.execute(
                select(func.count()).where(
                    Message.conversation_id == c.id,
                    Message.sender_id != current_user.id,
                    Message.is_deleted == False)
            )).scalar() or 0

        items.append(ConversationResponse(
            id=c.id, church_id=c.church_id, type=c.type, name=c.name,
            avatar_url=c.avatar_url, created_by=c.created_by, is_active=c.is_active,
            last_message_at=c.last_message_at, created_at=c.created_at,
            participants=participants, unread_count=unread))
    return items


@router.get("/requests")
async def get_chat_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Return conversations that were initiated by others where the current user hasn't replied yet."""
    # Get all conversation IDs where I'm a participant
    my_convos = (await db.execute(
        select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.user_id == current_user.id
        )
    )).scalars().all()

    pending = []
    for cid in my_convos:
        # Check if I've ever sent a message in this convo
        my_msg_count = (await db.execute(
            select(func.count()).where(
                Message.conversation_id == cid,
                Message.sender_id == current_user.id,
            )
        )).scalar() or 0

        if my_msg_count == 0:
            # I've never replied — this is a pending request
            conv = (await db.execute(
                select(Conversation).where(Conversation.id == cid)
            )).scalar_one_or_none()
            if conv:
                # Get who started it
                first_msg = (await db.execute(
                    select(Message).where(Message.conversation_id == cid)
                    .order_by(Message.created_at.asc()).limit(1)
                )).scalar_one_or_none()

                sender_name = None
                if first_msg:
                    sender = (await db.execute(
                        select(User).where(User.id == first_msg.sender_id)
                    )).scalar_one_or_none()
                    sender_name = sender.full_name if sender else "Unknown"

                pending.append({
                    "id": conv.id,
                    "type": conv.type,
                    "name": conv.name,
                    "sender_name": sender_name,
                    "preview": first_msg.content[:100] if first_msg else None,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                })

    return {"data": pending}


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Create a new conversation (direct or group)."""
    # For direct messages, check if one already exists between these 2 users
    if data.type == "direct" and len(data.participant_user_ids) == 1:
        other_id = data.participant_user_ids[0]
        existing = (await db.execute(
            select(Conversation)
            .join(ConversationParticipant)
            .where(Conversation.church_id == current_user.church_id,
                   Conversation.type == "direct")
        )).scalars().all()
        for c in existing:
            pids = {p.user_id for p in c.participants}
            if pids == {current_user.id, other_id}:
                if data.message:
                    msg = Message(
                        conversation_id=c.id, sender_id=current_user.id,
                        content=data.message, message_type="text")
                    db.add(msg)
                    c.last_message_at = datetime.now(timezone.utc)
                    db.add(c)
                    await db.commit()
                return ConversationResponse(
                    id=c.id, church_id=c.church_id, type=c.type, name=c.name,
                    avatar_url=c.avatar_url, created_by=c.created_by,
                    is_active=c.is_active, last_message_at=c.last_message_at,
                    created_at=c.created_at, participants=[], unread_count=0)

    convo = Conversation(
        church_id=current_user.church_id,
        type=data.type,
        name=data.name,
        created_by=current_user.id,
    )
    db.add(convo)
    await db.commit()

    # Add creator as participant
    all_ids = set(data.participant_user_ids) | {current_user.id}
    for uid in all_ids:
        p = ConversationParticipant(
            conversation_id=convo.id, user_id=uid,
            role="admin" if uid == current_user.id else "member")
        db.add(p)
    await db.commit()

    if data.message:
        msg = Message(
            conversation_id=convo.id, sender_id=current_user.id,
            content=data.message, message_type="text")
        db.add(msg)
        convo.last_message_at = datetime.now(timezone.utc)
        db.add(convo)
        await db.commit()

    await db.refresh(convo)

    return ConversationResponse(
        id=convo.id, church_id=convo.church_id, type=convo.type, name=convo.name,
        avatar_url=convo.avatar_url, created_by=convo.created_by,
        is_active=convo.is_active, last_message_at=convo.last_message_at,
        created_at=convo.created_at, participants=[], unread_count=0)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=200),
    before_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get paginated messages for a conversation (cursor-based)."""
    # Verify membership
    member = (await db.execute(select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id,
    ))).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a participant")

    query = select(Message).where(
        Message.conversation_id == conversation_id,
        Message.is_deleted == False)
    if before_id:
        query = query.where(Message.id < before_id)
    query = query.order_by(Message.created_at.desc()).limit(limit)

    messages = (await db.execute(query)).scalars().all()
    items = []
    for m in messages:
        sender = (await db.execute(select(User).where(User.id == m.sender_id))).scalar_one_or_none()
        items.append(MessageResponse(
            id=m.id, conversation_id=m.conversation_id, sender_id=m.sender_id,
            sender_name=sender.full_name if sender else None,
            content=m.content, text=m.content, message=m.content,
            message_type=m.message_type, media_url=m.media_url,
            reply_to=m.reply_to, reactions=m.reactions,
            is_edited=m.is_edited, is_deleted=m.is_deleted, created_at=m.created_at))
    items.reverse()
    return items


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: int, data: MessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Send a message to a conversation."""
    member = (await db.execute(select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id,
    ))).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a participant")

    parsed_content = data.get_content

    msg = Message(
        conversation_id=conversation_id, sender_id=current_user.id,
        content=parsed_content, message_type=data.message_type,
        media_url=data.media_url, reply_to=data.reply_to,
    )
    db.add(msg)

    # Update conversation last_message_at
    convo = (await db.execute(select(Conversation).where(
        Conversation.id == conversation_id))).scalar_one_or_none()
    if convo:
        convo.last_message_at = datetime.now(timezone.utc)
        db.add(convo)

    await db.commit()
    await db.refresh(msg)

    return MessageResponse(
        id=msg.id, conversation_id=msg.conversation_id, sender_id=msg.sender_id,
        sender_name=current_user.full_name, content=msg.content, text=msg.content, message=msg.content,
        message_type=msg.message_type, media_url=msg.media_url,
        reply_to=msg.reply_to, reactions=msg.reactions,
        is_edited=msg.is_edited, is_deleted=msg.is_deleted,
        created_at=msg.created_at)


@router.post("/{conversation_id}/read")
async def mark_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Mark all messages in a conversation as read."""
    member = (await db.execute(select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id,
    ))).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a participant")
    member.last_read_at = datetime.now(timezone.utc)
    db.add(member)
    return {"message": "Marked as read"}


@router.post("/{conversation_id}/messages/{message_id}/react")
async def react_to_message(
    conversation_id: int, message_id: int, data: MessageReaction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Toggle a reaction on a message."""
    msg = (await db.execute(select(Message).where(
        Message.id == message_id, Message.conversation_id == conversation_id
    ))).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    reactions = dict(msg.reactions or {})
    user_list = reactions.get(data.emoji, [])
    if current_user.id in user_list:
        user_list.remove(current_user.id)
    else:
        user_list.append(current_user.id)
    reactions[data.emoji] = user_list
    if not user_list:
        del reactions[data.emoji]
    msg.reactions = reactions
    db.add(msg)
    return {"reactions": reactions}


@router.delete("/{conversation_id}/messages/{message_id}", status_code=204)
async def delete_message(
    conversation_id: int, message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Soft-delete a message (only sender or admin can delete)."""
    msg = (await db.execute(select(Message).where(
        Message.id == message_id, Message.conversation_id == conversation_id
    ))).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot delete this message")
    msg.is_deleted = True
    msg.content = "[Message deleted]"
    db.add(msg)
