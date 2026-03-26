"""Bible API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from app.services.bible import get_bible_data, get_chapter, get_verse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/bible", tags=["Bible"])


@router.get("/books")
async def list_books(_=Depends(get_current_user)):
    """List all books in the Bible and their chapter counts."""
    bible = get_bible_data()
    books = []
    
    for book_name, chapters in bible.items():
        books.append({
            "name": book_name,
            "chapter_count": len(chapters)
        })
        
    return {
        "translation": "KJV",
        "books": books
    }


@router.get("/{book}/{chapter}")
async def read_chapter(book: str, chapter: int, _=Depends(get_current_user)):
    """Get all verses for a specific chapter."""
    data = get_chapter(book, chapter)
    if not data:
        raise HTTPException(status_code=404, detail="Book or chapter not found")
        
    return {
        "book": book.title(),
        "chapter": chapter,
        "verses": data
    }


@router.get("/{book}/{chapter}/{verse}")
async def read_verse(book: str, chapter: int, verse: int, _=Depends(get_current_user)):
    """Get a specific verse."""
    text = get_verse(book, chapter, verse)
    if not text:
        raise HTTPException(status_code=404, detail="Verse not found")
        
    return {
        "book": book.title(),
        "chapter": chapter,
        "verse": verse,
        "text": text
    }


@router.get("/search")
async def search_bible(q: str, _=Depends(get_current_user)):
    """Full-text search across the Bible."""
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Search query must be at least 3 characters")
        
    bible = get_bible_data()
    results = []
    query_lower = q.lower()
    
    # Cap at 50 results to prevent massive payloads
    for book, chapters in bible.items():
        for ch, verses in chapters.items():
            for v_num, text in verses.items():
                if query_lower in text.lower():
                    results.append({
                        "book": book,
                        "chapter": int(ch),
                        "verse": int(v_num),
                        "text": text
                    })
                    if len(results) >= 50:
                        return {"results": results, "limited": True}
                        
    return {"results": results, "limited": False}
