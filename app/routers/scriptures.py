"""Pastor's service scripture API endpoints."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.scripture import ServiceScripture
from app.schemas.scripture import ServiceScriptureCreate, ServiceScriptureUpdate, ServiceScriptureResponse
from app.routers.auth import get_current_user
from app.services.bible import get_verse

router = APIRouter(prefix="/scriptures", tags=["Scriptures"])


def _resolve_verses(book: str, chapter: int, verse_start: int, verse_end: Optional[int]) -> str:
    """Helper to fetch the actual text from the KJV JSON data."""
    end = verse_end or verse_start
    text_parts = []
    
    for v in range(verse_start, end + 1):
        verse_text = get_verse(book, chapter, v)
        if verse_text:
            text_parts.append(f"[{v}] {verse_text}")
            
    if not text_parts:
        return "Verse text not found."
    return " ".join(text_parts)


@router.get("/active", response_model=ServiceScriptureResponse)
async def get_active_scripture(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current active scripture for the user's church, including resolved text."""
    scripture = db.query(ServiceScripture).filter(
        ServiceScripture.church_id == current_user.church_id,
        ServiceScripture.is_active == True
    ).first()
    
    if not scripture:
        raise HTTPException(status_code=404, detail="No active scripture set")
        
    # Build response dictionary
    resp = {
        "id": scripture.id,
        "church_id": scripture.church_id,
        "title": scripture.title,
        "book": scripture.book,
        "chapter": scripture.chapter,
        "verse_start": scripture.verse_start,
        "verse_end": scripture.verse_end,
        "pastor_notes": scripture.pastor_notes,
        "is_active": scripture.is_active,
        "service_date": scripture.service_date,
        "created_at": scripture.created_at,
        "updated_at": scripture.updated_at,
        "set_by_name": scripture.set_by.full_name if scripture.set_by else None,
        "verse_text": _resolve_verses(scripture.book, scripture.chapter, scripture.verse_start, scripture.verse_end)
    }
    return resp


@router.get("", response_model=list[ServiceScriptureResponse])
async def list_scriptures(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List pastoral scripture history."""
    scriptures = db.query(ServiceScripture).filter(
        ServiceScripture.church_id == current_user.church_id
    ).order_by(desc(ServiceScripture.created_at)).offset(offset).limit(limit).all()
    
    results = []
    for s in scriptures:
        results.append({
            **s.__dict__,
            "set_by_name": s.set_by.full_name if s.set_by else None,
            "verse_text": _resolve_verses(s.book, s.chapter, s.verse_start, s.verse_end)
        })
    return results


@router.post("", response_model=ServiceScriptureResponse, status_code=201)
async def create_scripture(
    data: ServiceScriptureCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a new active scripture (Pastor/Admin only)."""
    if current_user.role not in ["pastor", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Deactivate any currently active scripture
    db.query(ServiceScripture).filter(
        ServiceScripture.church_id == current_user.church_id,
        ServiceScripture.is_active == True
    ).update({"is_active": False})
    
    new_scripture = ServiceScripture(
        **data.model_dump(),
        church_id=current_user.church_id,
        set_by_user_id=current_user.id,
        is_active=True
    )
    
    db.add(new_scripture)
    db.commit()
    db.refresh(new_scripture)
    
    return {
        **new_scripture.__dict__,
        "set_by_name": current_user.full_name,
        "verse_text": _resolve_verses(new_scripture.book, new_scripture.chapter, new_scripture.verse_start, new_scripture.verse_end)
    }


@router.put("/{scripture_id}", response_model=ServiceScriptureResponse)
async def update_scripture(
    scripture_id: int,
    data: ServiceScriptureUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing scripture (Pastor/Admin only)."""
    if current_user.role not in ["pastor", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    scripture = db.query(ServiceScripture).filter(
        ServiceScripture.id == scripture_id,
        ServiceScripture.church_id == current_user.church_id
    ).first()
    
    if not scripture:
        raise HTTPException(status_code=404, detail="Scripture not found")
        
    # If they are marking this active, deactivate others
    if data.is_active is True:
        db.query(ServiceScripture).filter(
            ServiceScripture.church_id == current_user.church_id,
            ServiceScripture.is_active == True,
            ServiceScripture.id != scripture_id
        ).update({"is_active": False})
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scripture, key, value)
        
    db.commit()
    db.refresh(scripture)
    
    return {
        **scripture.__dict__,
        "set_by_name": scripture.set_by.full_name if scripture.set_by else None,
        "verse_text": _resolve_verses(scripture.book, scripture.chapter, scripture.verse_start, scripture.verse_end)
    }


@router.delete("/{scripture_id}", status_code=204)
async def delete_scripture(
    scripture_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["pastor", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    scripture = db.query(ServiceScripture).filter(
        ServiceScripture.id == scripture_id,
        ServiceScripture.church_id == current_user.church_id
    ).first()
    
    if scripture:
        db.delete(scripture)
        db.commit()
