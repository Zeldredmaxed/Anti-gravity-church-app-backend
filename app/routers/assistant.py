"""AI Assistant router for congregation Q&A and pastor administrative commands."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.sermon import Sermon
from app.models.scripture import ServiceScripture
from app.routers.auth import get_current_user
from app.config import settings
from app.services.bible import get_bible_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])

# ── Schemas ───────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    
class AskResponse(BaseModel):
    answer: str
    scripture_references: list[dict] = []  # e.g., [{"book": "John", "chapter": 3, "verse": 16}]
    sermon_references: list[dict] = []     # e.g., [{"sermon_id": 1, "title": "...", "timestamp": 120}]

class CommandRequest(BaseModel):
    command: str
    
class CommandResponse(BaseModel):
    success: bool
    summary: str
    action_type: str  # "event_created", "announcement_sent", "scripture_set", "unknown"
    action_data: dict = {}


# ── Internal AI Helper ────────────────────────────

def _query_openai(system_prompt: str, user_prompt: str) -> str:
    """Wrapper to query OpenAI if key is present."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI Assistant not configured (Missing OPENAI_API_KEY).")
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=502, detail="Failed to connect to AI service.")


# ── Endpoints ─────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
async def ask_assistant(
    req: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Congregation-facing Q&A for Bible and Sermon questions."""
    
    # 1. Fetch some recent sermon context to grounding the AI
    recent_sermons = db.query(Sermon).filter(
        Sermon.church_id == current_user.church_id,
        Sermon.is_published == True,
        Sermon.transcript.isnot(None)
    ).order_by(desc(Sermon.recorded_date)).limit(3).all()
    
    sermon_context = ""
    for s in recent_sermons:
        # truncate transcript to avoid token limits
        transcript_preview = s.transcript[:1000] if s.transcript else ""
        sermon_context += f"- Title: {s.title} (Speaker: {s.speaker})\n  Excerpt: {transcript_preview}...\n"
        
    system_prompt = (
        "You are a helpful, respectful, and theologically sound Christian church assistant. "
        "Your goal is to answer questions about the Bible, faith matters, and recent church sermons. "
        "When referencing the Bible, always provide the exact Book, Chapter, and Verse so the app can link to it. "
        "Below is context from recent sermon transcripts. Use this if the user asks what the pastor preached about.\n\n"
        f"RECENT SERMON CONTEXT:\n{sermon_context if sermon_context else 'None available.'}"
    )
    
    ai_response = _query_openai(system_prompt, req.query)
    
    # Simple heuristic to extract references (could be improved with function calling)
    # The frontend will display the text answer. If the AI provides references, the frontend can linkification them.
    
    return AskResponse(
        answer=ai_response,
        scripture_references=[], 
        sermon_references=[]
    )


@router.post("/pastor-command", response_model=CommandResponse)
async def pastor_command(
    req: CommandRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin-facing natural language command processor."""
    if current_user.role not in ["pastor", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized for AI admin commands.")
        
    system_prompt = (
        "You are an administrative AI for a church management backend. "
        "The pastor has provided a natural language command. "
        "You must classify the requested action and extract relevant parameters into a JSON object. "
        "Return ONLY raw, valid JSON with no markdown block formatting. "
        "JSON Schema:\n"
        "{\n"
        '  "action": "event_create" | "notification_send" | "scripture_set" | "unknown",\n'
        '  "summary": "A friendly summary of what you are doing (e.g., \'Setting Sunday verse to John 3:16\')",\n'
        '  "parameters": {\n'
        '       // For event_create: "title", "date" (ISO8601), "location", "description"\n'
        '       // For notification_send: "title", "message"\n'
        '       // For scripture_set: "book", "chapter" (int), "verse_start" (int), "verse_end" (int)\n'
        "  }\n"
        "}"
    )
    
    ai_json_str = _query_openai(system_prompt, req.command)
    
    import json
    try:
        ai_data = json.loads(ai_json_str)
    except json.JSONDecodeError:
        return CommandResponse(
            success=False,
            summary="Failed to understand the command format.",
            action_type="error"
        )
        
    action = ai_data.get("action", "unknown")
    params = ai_data.get("parameters", {})
    summary = ai_data.get("summary", "Processed command.")
    
    # Act on the parsed intent
    if action == "scripture_set":
        # Deactivate current
        db.query(ServiceScripture).filter(
            ServiceScripture.church_id == current_user.church_id,
            ServiceScripture.is_active == True
        ).update({"is_active": False})
        
        # Create new
        new_scripture = ServiceScripture(
            church_id=current_user.church_id,
            title=f"Highlighted Scripture",
            book=params.get("book", "Genesis"),
            chapter=params.get("chapter", 1),
            verse_start=params.get("verse_start", 1),
            verse_end=params.get("verse_end", 1),
            set_by_user_id=current_user.id,
            is_active=True
        )
        db.add(new_scripture)
        db.commit()
        
    elif action == "notification_send":
        # (Assuming you use the alerts router for push)
        pass # In a real implementation this would trigger your push notification logic
        
    elif action == "event_create":
        # (Creates a church event)
        pass

    elif action == "unknown":
        return CommandResponse(
            success=False,
            summary="I'm sorry, I don't know how to execute that administrative command.",
            action_type="unknown"
        )
    
    return CommandResponse(
        success=True,
        summary=summary,
        action_type=action,
        action_data=params
    )
