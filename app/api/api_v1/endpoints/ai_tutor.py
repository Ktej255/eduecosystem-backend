from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.rag_service import rag_service
from app.api import deps
from app.models.user import User

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context_context: Optional[str] = None # e.g., "lesson_id:123"

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

class IngestRequest(BaseModel):
    text: str
    source: str

@router.post("/chat", response_model=ChatResponse)
def chat_with_guru(
    request: ChatRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Chat with the AI Tutor (Guru) using RAG context.
    """
    try:
        response = rag_service.chat_with_guru(request.message, request.context_context)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
def ingest_content(
    request: IngestRequest,
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Ingest content into the vector store (Admin only).
    """
    try:
        rag_service.ingest(request.text, request.source)
        return {"status": "success", "message": "Content ingested"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
