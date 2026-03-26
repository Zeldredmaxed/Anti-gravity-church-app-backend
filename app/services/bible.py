"""Bible service for serving bundled KJV data."""

import json
import os
from pathlib import Path
from fastapi import HTTPException

DATA_DIR = Path(__file__).parent.parent / "data"
KJV_FILE = DATA_DIR / "kjv.json"

_bible_data = None


def get_bible_data() -> dict:
    global _bible_data
    if _bible_data is None:
        if not os.path.exists(KJV_FILE):
            raise HTTPException(status_code=503, detail="Bible data not yet initialized. Please run the download script.")
        with open(KJV_FILE, "r", encoding="utf-8") as f:
            _bible_data = json.load(f)
    return _bible_data


def get_verse(book: str, chapter: int, verse: int) -> str:
    bible = get_bible_data()
    try:
        # Title case matching (e.g., "john" -> "John", "1 john" -> "1 John")
        book_clean = book.title() if not book[0].isdigit() else f"{book[0]} {book[2:].title()}"
        return bible[book_clean][str(chapter)][str(verse)]
    except KeyError:
        return None


def get_chapter(book: str, chapter: int) -> dict[str, str]:
    bible = get_bible_data()
    try:
        book_clean = book.title() if not book[0].isdigit() else f"{book[0]} {book[2:].title()}"
        return bible[book_clean][str(chapter)]
    except KeyError:
        return None
