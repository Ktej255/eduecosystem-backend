from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from datetime import datetime
import uuid
import logging

from app.api import deps
from app.models.user import User
from app.core.file_validation import (
    validate_image_file,
    validate_video_file,
    validate_document_file,
)
from app.core.virus_scanner import scan_file
from app.core.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter()

# Max file sizes
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    ext = Path(original_filename).suffix.lower()
    # Sanitize the filename
    safe_name = "".join(
        c for c in Path(original_filename).stem if c.isalnum() or c in ("-", "_")
    )
    safe_name = safe_name[:50]  # Limit length
    return f"{safe_name}_{timestamp}_{unique_id}{ext}"


from pydantic import BaseModel

class VideoLinkCreate(BaseModel):
    url: str
    title: str = "YouTube Video"

@router.post("/video/link")
async def save_video_link(
    *,
    video_in: VideoLinkCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Save a YouTube video link as an asset.
    """
    # Simply store the URL in the Asset table
    from app import crud, schemas
    asset_in = schemas.AssetCreate(
        filename=video_in.title,  # Use title as filename
        original_name=video_in.url,
        file_type="video",
        url=video_in.url,
        size=0,  # No file size
        user_id=current_user.id,
        mime_type="video/youtube"
    )
    asset = crud.asset.create(db=deps.get_db(), obj_in=asset_in)

    return {
        "url": asset.url,
        "filename": asset.filename,
        "type": asset.mime_type,
        "user_id": asset.user_id,
        "id": asset.id
    }

@router.post("/video")
async def upload_video(
    *,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a video file with enhanced security validation.

    - Validates file size
    - Validates file content (magic number check)
    - Scans for viruses (if enabled)
    - Stores in configured backend (local or S3)
    """
    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_VIDEO_SIZE / (1024 * 1024):.0f}MB",
        )

    # Validate file content
    is_valid, error_msg = validate_video_file(content[:64], file.filename or "video")
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid video file: {error_msg}")

    # Virus scan (if enabled)
    is_safe, virus_name = scan_file(content, file.filename or "video")
    if not is_safe:
        logger.warning(
            f"Virus detected in upload from user {current_user.id}: {virus_name}"
        )
        raise HTTPException(
            status_code=400, detail="File rejected: Security threat detected"
        )

    # Generate unique filename
    filename = generate_unique_filename(file.filename or "video.mp4")

    # Upload to storage backend
    storage = get_storage()
    success, file_url, error = storage.upload(
        content, filename, file.content_type or "video/mp4"
    )

    if not success:
        logger.error(f"Failed to upload video: {error}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Save to Asset database
    from app import crud, schemas
    asset_in = schemas.AssetCreate(
        filename=filename,
        original_name=file.filename or "video.mp4",
        file_type="video",
        url=file_url,
        size=len(content),
        user_id=current_user.id,
        mime_type=file.content_type or "video/mp4"
    )
    crud.asset.create(db=deps.get_db(), obj_in=asset_in)

    return {
        "url": file_url,
        "filename": filename,
        "size": len(content),
        "type": file.content_type,
        "user_id": current_user.id,
    }


@router.post("/file")
async def upload_file(
    *,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a document or file with enhanced security validation.

    - Validates file size
    - Validates file content (magic number check)
    - Scans for viruses (if enabled)
    - Stores in configured backend (local or S3)
    """
    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.0f}MB",
        )

    # Validate file content
    is_valid, error_msg = validate_document_file(content[:64], file.filename or "file")
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid file: {error_msg}")

    # Virus scan (if enabled)
    is_safe, virus_name = scan_file(content, file.filename or "file")
    if not is_safe:
        logger.warning(
            f"Virus detected in upload from user {current_user.id}: {virus_name}"
        )
        raise HTTPException(
            status_code=400, detail="File rejected: Security threat detected"
        )

    # Generate unique filename
    filename = generate_unique_filename(file.filename or "file.pdf")

    # Upload to storage backend
    storage = get_storage()
    success, file_url, error = storage.upload(
        content, filename, file.content_type or "application/octet-stream"
    )

    if not success:
        logger.error(f"Failed to upload file: {error}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Save to Asset database
    from app import crud, schemas
    asset_in = schemas.AssetCreate(
        filename=filename,
        original_name=file.filename or "file",
        file_type="document",
        url=file_url,
        size=len(content),
        user_id=current_user.id,
        mime_type=file.content_type or "application/octet-stream"
    )
    crud.asset.create(db=deps.get_db(), obj_in=asset_in)

    return {
        "url": file_url,
        "filename": filename,
        "original_name": file.filename,
        "size": len(content),
        "type": file.content_type,
        "user_id": current_user.id,
    }


@router.post("/image")
async def upload_image(
    *,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload an image file with enhanced security validation.

    - Validates file size
    - Validates file content (magic number check)
    - Scans for viruses (if enabled)
    - Stores in configured backend (local or S3)
    """
    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE / (1024 * 1024):.0f}MB",
        )

    # Validate file content (check magic numbers)
    is_valid, error_msg = validate_image_file(content[:64], file.filename or "image")
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {error_msg}")

    # Virus scan (if enabled)
    is_safe, virus_name = scan_file(content, file.filename or "image")
    if not is_safe:
        logger.warning(
            f"Virus detected in upload from user {current_user.id}: {virus_name}"
        )
        raise HTTPException(
            status_code=400, detail="File rejected: Security threat detected"
        )

    # Generate unique filename
    filename = generate_unique_filename(file.filename or "image.jpg")

    # Upload to storage backend
    storage = get_storage()
    success, file_url, error = storage.upload(
        content, filename, file.content_type or "image/jpeg"
    )

    if not success:
        logger.error(f"Failed to upload image: {error}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Save to Asset database
    from app import crud, schemas
    asset_in = schemas.AssetCreate(
        filename=filename,
        original_name=file.filename or "image.jpg",
        file_type="image",
        url=file_url,
        size=len(content),
        user_id=current_user.id,
        mime_type=file.content_type or "image/jpeg"
    )
    crud.asset.create(db=deps.get_db(), obj_in=asset_in)

    return {
        "url": file_url,
        "filename": filename,
        "size": len(content),
        "type": file.content_type,
        "user_id": current_user.id,
    }


@router.delete("/{file_type}/{filename}")
async def delete_file(
    file_type: str,
    filename: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an uploaded file.

    Note: In production, you should verify that the user owns the file
    or has permission to delete it.
    """
    if file_type not in ["videos", "files", "images"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    storage = get_storage()

    if not storage.exists(filename):
        raise HTTPException(status_code=404, detail="File not found")

    success, error = storage.delete(filename)

    if not success:
        logger.error(f"Failed to delete file {filename}: {error}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

    return {"message": "File deleted successfully", "filename": filename}
