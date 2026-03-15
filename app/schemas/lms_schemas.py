from typing import List, Optional
from pydantic import BaseModel, Field

class OptionCreate(BaseModel):
    text: str
    is_correct: bool = False

class QuestionCreate(BaseModel):
    text: str
    explanation: Optional[str] = None
    options: List[OptionCreate]
    subject_tag: Optional[str] = None
    difficulty: Optional[str] = "medium"

class BulkQuestionUpload(BaseModel):
    questions: List[QuestionCreate]

class QuestionResponse(BaseModel):
    id: str
    text: str
    explanation: Optional[str] = None
    subject_tag: Optional[str] = None
    difficulty: str
    
    class Config:
        from_attributes = True
