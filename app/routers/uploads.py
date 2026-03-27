"""File upload router — uploads media to Cloudinary for persistent cloud storage."""

import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional

from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

# ── Cloudinary Configuration ─────────────────────────────────────
# Set these in Railway environment variables:
#   CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure=True,
)

# Allowed MIME types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/mpeg"}
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/ogg",
    "audio/aac", "audio/x-m4a", "audio/m4a", "audio/flac",
    "audio/x-wav", "audio/webm", "audio/mp3", "audio/x-aac",
}
ALL_ALLOWED = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES

# Max file sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 300 * 1024 * 1024  # 300 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024   # 20 MB


def _get_max_size(content_type: str) -> int:
    if content_type in ALLOWED_VIDEO_TYPES:
        return MAX_VIDEO_SIZE
    if content_type in ALLOWED_AUDIO_TYPES:
        return MAX_AUDIO_SIZE
    return MAX_IMAGE_SIZE


def _resource_type(content_type: str) -> str:
    """Map MIME type to Cloudinary resource_type."""
    if content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    if content_type in ALLOWED_AUDIO_TYPES:
        return "video"  # Cloudinary treats audio as "video" resource_type
    return "image"


def _media_category(content_type: str) -> str:
    if content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    if content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    return "image"


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    folder: Optional[str] = Form("church-media"),
    current_user: User = Depends(get_current_user),
):
    """Upload an image, video, or audio file to Cloudinary.

    Accepts multipart/form-data with a `file` field.
    Optional fields:
      - category: image, video, audio (auto-detected if omitted)
      - folder: Cloudinary folder name (default: "church-media")

    Returns: { data: { url, public_id, content_type, size, category, width, height } }
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
                   f"Maximum for this type is {max_mb}MB."
        )

    # Upload to Cloudinary
    resource = _resource_type(content_type)
    try:
        if resource == "video":
            result = cloudinary.uploader.upload_large(
                content,
                resource_type=resource,
                folder=folder or "church-media",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        else:
            result = cloudinary.uploader.upload(
                content,
                resource_type=resource,
                folder=folder or "church-media",
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    detected_category = category or _media_category(content_type)

    return {"data": {
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "original_name": file.filename,
        "content_type": content_type,
        "size": file_size,
        "category": detected_category,
        "width": result.get("width"),
        "height": result.get("height"),
        "duration": result.get("duration"),
        "format": result.get("format"),
    }}


@router.post("/multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    folder: Optional[str] = Form("church-media"),
    current_user: User = Depends(get_current_user),
):
    """Upload multiple files at once to Cloudinary.

    Accepts multipart/form-data with multiple `files` fields.
    Maximum 10 files per request.

    Returns: { data: [ { url, public_id, content_type, size, category }, ... ] }
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

        resource = _resource_type(content_type)
        try:
            if resource == "video":
                result = cloudinary.uploader.upload_large(
                    content,
                    resource_type=resource,
                    folder=folder or "church-media",
                    use_filename=True,
                    unique_filename=True,
                    overwrite=False,
                )
            else:
                result = cloudinary.uploader.upload(
                    content,
                    resource_type=resource,
                    folder=folder or "church-media",
                    use_filename=True,
                    unique_filename=True,
                    overwrite=False,
                )
            results.append({
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "original_name": file.filename,
                "content_type": content_type,
                "size": file_size,
                "category": _media_category(content_type),
                "width": result.get("width"),
                "height": result.get("height"),
                "duration": result.get("duration"),
            })
        except Exception as e:
            results.append({"error": f"Failed '{file.filename}': {str(e)}"})

    return {"data": results}
