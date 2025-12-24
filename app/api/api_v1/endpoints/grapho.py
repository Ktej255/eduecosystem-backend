from typing import Any, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import submission as crud_submission
from app.schemas.submission import Submission, SubmissionCreate
from app.services.ocr import analyze_handwriting
from app.models.user import User
import shutil
import os
import json

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[Submission])
def read_submissions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve handwriting submissions.
    """
    submissions = crud_submission.get_multi_by_owner(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return jsonable_encoder(submissions)


@router.post("/upload")
async def upload_handwriting(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload handwriting sample and get AI analysis.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed."
        )

    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File too large. Maximum size is 10MB."
        )

    # Save file locally
    file_location = f"{UPLOAD_DIR}/{current_user.id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run OCR / Analysis
    ocr_result = analyze_handwriting(file_location, user=current_user)

    # Create Submission Record
    submission_in = SubmissionCreate(
        image_url=file_location,
        quiz_data="{}",  # No quiz needed for now
        report_content=json.dumps(ocr_result),
        report_level=1,
    )
    submission = crud_submission.create_with_owner(
        db=db, obj_in=submission_in, owner_id=current_user.id
    )

    # Award coins for submission
    current_user.coins += 50
    db.commit()

    return {
        "submission_id": submission.id,
        "extracted_text": ocr_result.get("extracted_text", ""),
        "features": ocr_result.get("features", {}),
        "analysis": ocr_result.get("analysis", ""),
        "coins_earned": 50,
        "message": "Handwriting analyzed successfully!",
    }
