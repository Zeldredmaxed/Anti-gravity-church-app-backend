"""WebSocket endpoint for real-time chat."""

import json
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session
from app.models.chat import Conversation, ConversationParticipant, Message
from app.models.user import User
from app.utils.security import decode_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections per conversation."""

    def __init__(self):
        # {conversation_id: {user_id: WebSocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int, user_id: int):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}
        self.active_connections[conversation_id][user_id] = websocket

    def disconnect(self, conversation_id: int, user_id: int):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].pop(user_id, None)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: int, message: dict, exclude_user: int = None):
        """Broadcast a message to all connected users in a conversation."""
        if conversation_id not in self.active_connections:
            return
        for user_id, ws in list(self.active_connections[conversation_id].items()):
            if user_id == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(conversation_id, user_id)

    def get_online_users(self, conversation_id: int) -> Set[int]:
        return set(self.active_connections.get(conversation_id, {}).keys())


manager = ConnectionManager()


async def _authenticate_ws(token: str) -> User | None:
    """Authenticate a WebSocket connection via JWT token."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == int(user_id)))
            return result.scalar_one_or_none()
    except Exception:
        return None


@router.websocket("/ws/fellowship-chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: int):
    """
    WebSocket for real-time chat.
    Connect with: ws://host/ws/fellowship-chat/{id}?token=JWT_TOKEN
    
    Client sends:
      {"type": "message", "content": "Hello", "message_type": "text"}
      {"type": "typing", "is_typing": true}
      {"type": "read"}
    
    Server broadcasts:
      {"type": "message", "data": {...message...}}
      {"type": "typing", "user_id": 1, "user_name": "...", "is_typing": true}
      {"type": "read", "user_id": 1, "timestamp": "..."}
      {"type": "online", "user_ids": [1,2,3]}
    """
    # Authenticate via query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user = await _authenticate_ws(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verify user is a participant
    async with async_session() as db:
        participant = (await db.execute(select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user.id,
        ))).scalar_one_or_none()
        if not participant:
            await websocket.close(code=4003, reason="Not a participant")
            return

    await manager.connect(websocket, conversation_id, user.id)

    # Notify others that user came online
    await manager.broadcast(conversation_id, {
        "type": "online",
        "user_ids": list(manager.get_online_users(conversation_id)),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "message":
                # Persist and broadcast
                async with async_session() as db:
                    msg = Message(
                        conversation_id=conversation_id,
                        sender_id=user.id,
                        content=data.get("content"),
                        message_type=data.get("message_type", "text"),
                        media_url=data.get("media_url"),
                        reply_to=data.get("reply_to"),
                    )
                    db.add(msg)
                    # Update conversation timestamp
                    convo = (await db.execute(select(Conversation).where(
                        Conversation.id == conversation_id))).scalar_one_or_none()
                    if convo:
                        convo.last_message_at = datetime.now(timezone.utc)
                        db.add(convo)
                    await db.commit()
                    await db.refresh(msg)

                    await manager.broadcast(conversation_id, {
                        "type": "message",
                        "data": {
                            "id": msg.id,
                            "conversation_id": conversation_id,
                            "sender_id": user.id,
                            "sender_name": user.full_name,
                            "content": msg.content,
                            "message_type": msg.message_type,
                            "media_url": msg.media_url,
                            "reply_to": msg.reply_to,
                            "created_at": msg.created_at.isoformat(),
                        },
                    })

            elif msg_type == "typing":
                await manager.broadcast(conversation_id, {
                    "type": "typing",
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "is_typing": data.get("is_typing", True),
                }, exclude_user=user.id)

            elif msg_type == "read":
                now = datetime.now(timezone.utc)
                async with async_session() as db:
                    p = (await db.execute(select(ConversationParticipant).where(
                        ConversationParticipant.conversation_id == conversation_id,
                        ConversationParticipant.user_id == user.id,
                    ))).scalar_one_or_none()
                    if p:
                        p.last_read_at = now
                        db.add(p)
                        await db.commit()
                await manager.broadcast(conversation_id, {
                    "type": "read",
                    "user_id": user.id,
                    "timestamp": now.isoformat(),
                }, exclude_user=user.id)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, user.id)
        await manager.broadcast(conversation_id, {
            "type": "online",
            "user_ids": list(manager.get_online_users(conversation_id)),
        })
