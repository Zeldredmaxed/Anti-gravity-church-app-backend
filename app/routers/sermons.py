"""Sermon and Media Library API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.sermon import Sermon, SermonNote
from app.schemas.sermon import (
    SermonCreate, SermonUpdate, SermonResponse,
    SermonNoteCreate, SermonNoteUpdate, SermonNoteResponse
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/sermons", tags=["Sermons"])


# ── Sermons ───────────────────────────────────────

@router.get("", response_model=list[SermonResponse])
async def list_sermons(
    limit: int = 20,
    offset: int = 0,
    series: str = None,
    speaker: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Sermon).filter(
        Sermon.church_id == current_user.church_id,
        Sermon.is_published == True,
        Sermon.is_deleted == False
    )
    
    if series:
        query = query.filter(Sermon.series_name == series)
    if speaker:
        query = query.filter(Sermon.speaker == speaker)
        
    sermons = query.order_by(desc(Sermon.recorded_date), desc(Sermon.created_at)).offset(offset).limit(limit).all()
    
    return [
        {**s.__dict__, "uploader_name": s.uploader.full_name if s.uploader else None}
        for s in sermons
    ]


@router.get("/live", response_model=SermonResponse)
async def get_live_sermon(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sermon = db.query(Sermon).filter(
        Sermon.church_id == current_user.church_id,
        Sermon.is_live == True,
        Sermon.is_deleted == False
    ).first()
    
    if not sermon:
        raise HTTPException(status_code=404, detail="No live stream currently active")
        
    return {**sermon.__dict__, "uploader_name": sermon.uploader.full_name if sermon.uploader else None}


@router.get("/{sermon_id}", response_model=SermonResponse)
async def get_sermon(
    sermon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sermon = db.query(Sermon).filter(
        Sermon.id == sermon_id,
        Sermon.church_id == current_user.church_id,
        Sermon.is_deleted == False
    ).first()
    
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
        
    return {**sermon.__dict__, "uploader_name": sermon.uploader.full_name if sermon.uploader else None}


@router.post("", response_model=SermonResponse, status_code=201)
async def create_sermon(
    data: SermonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_sermon = Sermon(
        **data.model_dump(),
        church_id=current_user.church_id,
        uploaded_by=current_user.id
    )
    
    db.add(new_sermon)
    db.commit()
    db.refresh(new_sermon)
    
    return {**new_sermon.__dict__, "uploader_name": current_user.full_name}


@router.put("/{sermon_id}", response_model=SermonResponse)
async def update_sermon(
    sermon_id: int,
    data: SermonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    sermon = db.query(Sermon).filter(
        Sermon.id == sermon_id,
        Sermon.church_id == current_user.church_id
    ).first()
    
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
        
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sermon, key, value)
        
    db.commit()
    db.refresh(sermon)
    return {**sermon.__dict__, "uploader_name": sermon.uploader.full_name if sermon.uploader else None}


@router.delete("/{sermon_id}", status_code=204)
async def delete_sermon(
    sermon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    sermon = db.query(Sermon).filter(
        Sermon.id == sermon_id,
        Sermon.church_id == current_user.church_id
    ).first()
    
    if sermon:
        sermon.is_deleted = True
        db.commit()


@router.post("/{sermon_id}/view")
async def track_sermon_view(
    sermon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sermon = db.query(Sermon).filter(
        Sermon.id == sermon_id,
        Sermon.church_id == current_user.church_id
    ).first()
    
    if sermon:
        sermon.view_count += 1
        db.commit()
    return {"status": "ok"}


# ── Sermon Notes ─────────────────────────────────

@router.get("/{sermon_id}/notes", response_model=list[SermonNoteResponse])
async def list_sermon_notes(
    sermon_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notes = db.query(SermonNote).filter(
        SermonNote.sermon_id == sermon_id,
        SermonNote.user_id == current_user.id
    ).order_by(SermonNote.timestamp_marker).all()
    
    return [
        {**n.__dict__, "sermon_title": n.sermon.title if n.sermon else None}
        for n in notes
    ]


@router.post("/{sermon_id}/notes", response_model=SermonNoteResponse, status_code=201)
async def create_sermon_note(
    sermon_id: int,
    data: SermonNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sermon = db.query(Sermon).filter(
        Sermon.id == sermon_id,
        Sermon.church_id == current_user.church_id
    ).first()
    
    if not sermon:
        raise HTTPException(status_code=404, detail="Sermon not found")
        
    note = SermonNote(
        sermon_id=sermon_id,
        user_id=current_user.id,
        church_id=current_user.church_id,
        content=data.content,
        timestamp_marker=data.timestamp_marker
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    return {**note.__dict__, "sermon_title": sermon.title}


@router.put("/notes/{note_id}", response_model=SermonNoteResponse)
async def update_sermon_note(
    note_id: int,
    data: SermonNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = db.query(SermonNote).filter(
        SermonNote.id == note_id,
        SermonNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
        
    db.commit()
    db.refresh(note)
    return {**note.__dict__, "sermon_title": note.sermon.title if note.sermon else None}


@router.delete("/notes/{note_id}", status_code=204)
async def delete_sermon_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = db.query(SermonNote).filter(
        SermonNote.id == note_id,
        SermonNote.user_id == current_user.id
    ).first()
    
    if note:
        db.delete(note)
        db.commit()


@router.get("/my-notes/all", response_model=list[SermonNoteResponse])
async def list_all_my_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notes across all sermons for the current user."""
    notes = db.query(SermonNote).filter(
        SermonNote.user_id == current_user.id
    ).order_by(desc(SermonNote.created_at)).all()
    
    return [
        {**n.__dict__, "sermon_title": n.sermon.title if n.sermon else None}
        for n in notes
    ]
