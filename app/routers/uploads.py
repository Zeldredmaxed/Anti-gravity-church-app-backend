"""File upload router — direct media upload for feed posts and shorts."""

import os
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

# Upload directory — persists on Railway with a volume mount at /app/uploads
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")

# Allowed MIME types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/mpeg"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/wav", "audio/ogg"}
ALL_ALLOWED = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES

# Max file sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024   # 20 MB


def _get_max_size(content_type: str) -> int:
    if content_type in ALLOWED_VIDEO_TYPES:
        return MAX_VIDEO_SIZE
    if content_type in ALLOWED_AUDIO_TYPES:
        return MAX_AUDIO_SIZE
    return MAX_IMAGE_SIZE


def _media_category(content_type: str) -> str:
    if content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    if content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    return "image"


@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """Upload an image, video, or audio file. Returns the public URL.

    Accepts multipart/form-data with a `file` field.
    Optional `category` field: image, video, audio (auto-detected if omitted).

    Returns: { data: { url, filename, content_type, size, category } }
    """
    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALL_ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' not allowed. "
                   f"Allowed: JPEG, PNG, GIF, WebP, MP4, MOV, WebM, MP3, WAV"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    max_size = _get_max_size(content_type)
    if file_size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size // (1024 * 1024)}MB). "
                   f"Maximum size for this file type is {max_mb}MB."
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    if not ext.startswith("."):
        ext = "." + ext
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # Organize by date and user
    date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    upload_subdir = os.path.join(UPLOAD_DIR, date_prefix)
    os.makedirs(upload_subdir, exist_ok=True)

    # Write file
    file_path = os.path.join(upload_subdir, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Build public URL
    # On Railway, this will be like: https://your-app.up.railway.app/uploads/2026/03/26/abc123.jpg
    relative_path = f"/uploads/{date_prefix}/{unique_name}"
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}{relative_path}"

    detected_category = category or _media_category(content_type)

    return {"data": {
        "url": public_url,
        "filename": unique_name,
        "original_name": file.filename,
        "content_type": content_type,
        "size": file_size,
        "category": detected_category,
    }}


@router.post("/multiple")
async def upload_multiple_files(
    request: Request,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload multiple files at once. Returns an array of URLs.

    Accepts multipart/form-data with multiple `files` fields.
    Maximum 10 files per request.

    Returns: { data: [ { url, filename, content_type, size, category }, ... ] }
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per upload")

    results = []
    for file in files:
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALL_ALLOWED:
            results.append({"error": f"Skipped '{file.filename}': type '{content_type}' not allowed"})
            continue

        content = await file.read()
        file_size = len(content)
        max_size = _get_max_size(content_type)

        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            results.append({"error": f"Skipped '{file.filename}': too large ({file_size // (1024*1024)}MB > {max_mb}MB)"})
            continue

        ext = os.path.splitext(file.filename or "file")[1] or ".bin"
        if not ext.startswith("."):
            ext = "." + ext
        unique_name = f"{uuid.uuid4().hex}{ext}"

        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        upload_subdir = os.path.join(UPLOAD_DIR, date_prefix)
        os.makedirs(upload_subdir, exist_ok=True)

        file_path = os.path.join(upload_subdir, unique_name)
        with open(file_path, "wb") as f:
            f.write(content)

        relative_path = f"/uploads/{date_prefix}/{unique_name}"
        base_url = str(request.base_url).rstrip("/")
        public_url = f"{base_url}{relative_path}"

        results.append({
            "url": public_url,
            "filename": unique_name,
            "original_name": file.filename,
            "content_type": content_type,
            "size": file_size,
            "category": _media_category(content_type),
        })

    return {"data": results}
