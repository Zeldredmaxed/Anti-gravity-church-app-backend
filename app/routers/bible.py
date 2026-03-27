"""Bible API endpoints — serves the bundled KJV Bible data."""

from fastapi import APIRouter, Depends, HTTPException
from app.services.bible import get_bible_data, get_chapter, get_verse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/bible", tags=["Bible"])


@router.get("/books")
async def list_books(_=Depends(get_current_user)):
    """List all books in the Bible and their chapter counts."""
    bible = get_bible_data()
    books = []

    for idx, (book_name, chapters) in enumerate(bible.items()):
        books.append({
            "id": str(idx + 1),
            "name": book_name,
            "chapters": len(chapters),
        })

    return {"data": books}


@router.get("/search")
async def search_bible(q: str, _=Depends(get_current_user)):
    """Full-text search across the Bible."""
    if len(q) < 3:
        raise HTTPException(status_code=400, detail="Search query must be at least 3 characters")

    bible = get_bible_data()
    results = []
    query_lower = q.lower()

    for book, chapters in bible.items():
        for ch, verses in chapters.items():
            for v_num, text in verses.items():
                if query_lower in text.lower():
                    results.append({
                        "reference": f"{book} {ch}:{v_num}",
                        "book": book,
                        "chapter": int(ch),
                        "verse": int(v_num),
                        "text": text,
                    })
                    if len(results) >= 50:
                        return {"data": {"results": results, "limited": True}}

    return {"data": {"results": results, "limited": False}}


@router.get("/{book}/{chapter}")
async def read_chapter(book: str, chapter: int, _=Depends(get_current_user)):
    """Get all verses for a specific chapter as a sorted array."""
    data = get_chapter(book, chapter)
    if not data:
        raise HTTPException(status_code=404, detail="Book or chapter not found")

    # Convert dict {"1": "text", "2": "text"} to sorted array [{verse, text}]
    verses = sorted(
        [{"verse": int(k), "text": v} for k, v in data.items()],
        key=lambda x: x["verse"],
    )

    return {
        "data": {
            "book": book.title(),
            "chapter": chapter,
            "verses": verses,
        }
    }


@router.get("/{book}/{chapter}/{verse}")
async def read_verse(book: str, chapter: int, verse: int, _=Depends(get_current_user)):
    """Get a specific verse."""
    text = get_verse(book, chapter, verse)
    if not text:
        raise HTTPException(status_code=404, detail="Verse not found")

    return {
        "data": {
            "book": book.title(),
            "chapter": chapter,
            "verse": verse,
            "text": text,
        }
    }
