"""AI Assistant router for congregation Q&A and pastor administrative commands, including Smart Segmentation."""

import logging
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.sermon import Sermon
from app.models.scripture import ServiceScripture
from app.utils.security import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])

# ── Schemas ───────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    
class AskResponse(BaseModel):
    answer: str
    scripture_references: list[dict] = []
    sermon_references: list[dict] = []

class CommandRequest(BaseModel):
    command: str
    
class CommandResponse(BaseModel):
    success: bool
    summary: str
    action_type: str  # e.g. "segment_audience", "scripture_set"
    action_data: dict = {}


# ── Internal AI Helper ────────────────────────────

def _query_openai(system_prompt: str, user_prompt: str, json_format: bool = False) -> str:
    """Wrapper to query OpenAI if key is present."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI Assistant not configured (Missing OPENAI_API_KEY).")
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"} if json_format else None,
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
    db: AsyncSession = Depends(get_db)
):
    """Congregation-facing Q&A for Bible and Sermon questions."""
    
    # Fetch recent sermon context
    query = select(Sermon).where(
        Sermon.church_id == current_user.church_id,
        Sermon.is_published == True,
        Sermon.transcript.isnot(None)
    ).order_by(desc(Sermon.recorded_date)).limit(3)
    
    result = await db.execute(query)
    recent_sermons = result.scalars().all()
    
    sermon_context = ""
    for s in recent_sermons:
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
    
    return AskResponse(
        answer=ai_response,
        scripture_references=[], 
        sermon_references=[]
    )


@router.post("/pastor-command", response_model=CommandResponse)
async def pastor_command(
    req: CommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin-facing AI assistant: Translates natural language to Smart Segment Filters or executes admin commands."""
    if current_user.role not in ["pastor", "admin", "staff", "ministry_leader"]:
        raise HTTPException(status_code=403, detail="Not authorized for AI admin commands.")
        
    system_prompt = (
        "You are an administrative AI for a Church Management System (ChMS). "
        "The pastor or ministry leader has provided a natural language command. "
        "You must classify the requested action and extract relevant parameters into a JSON object. "
        "Return ONLY raw, valid JSON with no markdown block formatting.\n\n"
        "Supported Actions and their JSON Schemas:\n\n"
        "1. segment_audience: translates natural language into a Smart Segmentation query.\n"
        '   Format: { "action": "segment_audience", "summary": "...", "parameters": { \n'
        '       "membership_status": (optional string - "active", "visitor", "member"),\n'
        '       "min_age": (optional int),\n'
        '       "max_age": (optional int),\n'
        '       "gender": (optional string - "Male", "Female"),\n'
        '       "is_serving": (optional boolean),\n'
        '       "not_attended_days": (optional int - days since last attendance),\n'
        '       "has_children": (optional boolean)\n'
        '   }}\n\n'
        "2. scripture_set: sets the active scripture for the sanctuary/app.\n"
        '   Format: { "action": "scripture_set", "summary": "...", "parameters": { \n'
        '       "book": "Genesis", "chapter": 1, "verse_start": 1, "verse_end": 1\n'
        '   }}\n\n'
        "3. unknown: if you cannot fulfill the request.\n"
        '   Format: { "action": "unknown", "summary": "I cannot do that.", "parameters": {} }\n'
    )
    
    ai_json_str = _query_openai(system_prompt, req.command, json_format=True)
    
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
    
    if action == "scripture_set":
        # Deactivate current
        deactivate_query = select(ServiceScripture).where(
            ServiceScripture.church_id == current_user.church_id,
            ServiceScripture.is_active == True
        )
        result = await db.execute(deactivate_query)
        active_scripts = result.scalars().all()
        for sc in active_scripts:
            sc.is_active = False
            
        # Create new
        new_scripture = ServiceScripture(
            church_id=current_user.church_id,
            title="Highlighted Scripture",
            book=params.get("book", "Genesis"),
            chapter=params.get("chapter", 1),
            verse_start=params.get("verse_start", 1),
            verse_end=params.get("verse_end", 1),
            set_by_user_id=current_user.id,
            is_active=True
        )
        db.add(new_scripture)
        await db.commit()
    
    # If action == "segment_audience", the frontend will use the returned parameters
    # to hit POST /communications/segment directly with the generated filters.
        
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
