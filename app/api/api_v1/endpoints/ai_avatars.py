"""
AI Avatar Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.crud.ai_avatar import crud_ai_avatar
from app.schemas.ai_avatar import AIAvatarCreate, AIAvatarUpdate, AIAvatarResponse
import logging

import os
import uuid

UPLOAD_DIR = "uploads/ai_avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=AIAvatarResponse, status_code=201)
async def create_ai_avatar(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    purpose: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    personality: str = Form(None),
    tone: str = Form("professional"),
    response_style: str = Form("concise"),
    urls: str = Form(None),
    instructions: str = Form(None),
    documents: List[UploadFile] = File(None),
):
    """
    Create a new AI avatar with knowledge base
    """
    try:
        # Process uploaded documents
        knowledge_base = {
            "urls": urls.split("\n") if urls else [],
            "instructions": instructions or "",
            "documents": []
        }

        if documents:
            for doc in documents:
                file_content = await doc.read()
                file_size = len(file_content)

                # Generate unique filename and save to storage
                unique_filename = f"{uuid.uuid4()}_{doc.filename}"
                file_path = os.path.join(UPLOAD_DIR, unique_filename)

                with open(file_path, "wb") as f:
                    f.write(file_content)

                # Extract text based on file type
                extracted_text = ""
                try:
                    if doc.filename.lower().endswith('.pdf'):
                        import fitz  # PyMuPDF
                        pdf_doc = fitz.open(stream=file_content, filetype="pdf")
                        for page in pdf_doc:
                            extracted_text += page.get_text() + "\n"
                        pdf_doc.close()
                    else:
                        # Attempt to decode as text for standard text/markdown files
                        extracted_text = file_content.decode('utf-8', errors='ignore')
                except Exception as ex:
                    logger.warning(f"Failed to extract text from {doc.filename}: {ex}")

                knowledge_base["documents"].append({
                    "filename": doc.filename,
                    "saved_path": file_path,
                    "size": file_size,
                    "extracted_text": extracted_text.strip()
                })

        avatar_in = AIAvatarCreate(
            user_id=current_user.id,
            purpose=purpose,
            name=name,
            description=description,
            personality=personality,
            tone=tone,
            response_style=response_style,
            knowledge_base=knowledge_base,
            is_active=True
        )

        avatar = crud_ai_avatar.create(db=db, obj_in=avatar_in)
        return avatar

    except Exception as e:
        logger.error(f"Error creating AI avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to create AI avatar")


@router.get("/", response_model=List[AIAvatarResponse])
def get_user_avatars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    """
    Get all AI avatars for the current user
    """
    avatars = crud_ai_avatar.get_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return avatars


@router.get("/{avatar_id}", response_model=AIAvatarResponse)
def get_avatar(
    avatar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific AI avatar
    """
    avatar = crud_ai_avatar.get(db=db, id=avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if avatar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return avatar


@router.put("/{avatar_id}", response_model=AIAvatarResponse)
def update_avatar(
    avatar_id: int,
    avatar_in: AIAvatarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an AI avatar
    """
    avatar = crud_ai_avatar.get(db=db, id=avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if avatar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    avatar = crud_ai_avatar.update(db=db, db_obj=avatar, obj_in=avatar_in)
    return avatar


@router.delete("/{avatar_id}")
def delete_avatar(
    avatar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an AI avatar
    """
    avatar = crud_ai_avatar.get(db=db, id=avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if avatar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud_ai_avatar.remove(db=db, id=avatar_id)
    return {"message": "Avatar deleted successfully"}


@router.post("/{avatar_id}/chat")
async def chat_with_avatar(
    avatar_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chat with an AI avatar using Gemini
    """
    from app.services.gemini_service import gemini_service
    
    avatar = crud_ai_avatar.get(db=db, id=avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if avatar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Build system message from avatar configuration
    system_message = f"""You are {avatar.name}, an AI assistant.
Purpose: {avatar.purpose}
Personality: {avatar.personality}
Tone: {avatar.tone}
Response Style: {avatar.response_style}

{avatar.knowledge_base.get('instructions', '')}

Always be helpful and aligned with the purpose defined above."""

    try:
        response = gemini_service.generate_text(
            prompt=message,
            system_prompt=system_message,
            user=current_user,
            temperature=0.7,
            max_tokens=500
        )
        
        return {"response": response}
    
    except Exception as e:
        logger.error(f"Error in avatar chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")
