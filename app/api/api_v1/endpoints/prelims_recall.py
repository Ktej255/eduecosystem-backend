"""
Prelims Recall Analysis API Endpoints
Uses AI Router for smart model selection and cost optimization
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import json
from datetime import datetime

from app.db.session import get_db
from app.services.ai_router import ai_router
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


class RecallAnalysisRequest(BaseModel):
    """Request for recall analysis"""
    cycle_id: int
    day_number: int
    part_number: int
    segment_number: int
    segment_title: str
    key_points: str
    response_type: str  # "audio" or "image"
    response_text: Optional[str] = None  # Transcribed audio or OCR text from image


class RecallAnalysisResponse(BaseModel):
    """Response from recall analysis - Enhanced with strict content matching"""
    # Topic Relevance
    is_relevant: bool = True
    relevance_message: str = ""
    
    # Core Metrics
    recall_score: int
    understanding_level: str = "Satisfactory"  # Excellent/Good/Satisfactory/Needs Work/Insufficient
    coverage_percentage: int = 0  # What percentage of key points were covered
    
    # Detailed Analysis
    feedback: str
    detailed_analysis: str = ""  # In-depth paragraph analysis
    
    # Strengths & Improvements
    strengths: list[str]
    areas_to_improve: list[str]
    key_takeaways: list[str] = []  # What student understood best
    
    # Concept Coverage - STRICT MATCHING
    concepts_covered: list[str] = []  # Concepts that MATCH the video key points
    concepts_missed: list[str] = []  # Key points from video NOT covered by student
    
    # Content Matching Analysis
    matched_content: list[str] = []  # Student content that matches video topics
    unmatched_content: list[str] = []  # Student content NOT related to video topic
    irrelevant_content: list[str] = []  # Off-topic or incorrect content with explanation
    
    # Penalty & Scoring
    penalty_applied: int = 0  # Points deducted for irrelevant content
    base_score: int = 0  # Score before penalty
    
    # Personalized Recommendations
    revision_priority: str = "medium"  # high/medium/low
    memory_retention_tips: list[str] = []  # Personalized study tips
    suggested_next_steps: list[str] = []  # What to do next
    
    # AI Metadata
    ai_source: str = "template"
    ai_model: Optional[str] = None
    analysis_timestamp: Optional[str] = None
    confidence_score: int = 80  # AI's confidence in assessment (0-100)


# System message for AI analysis - STRICT and UNIQUE responses required
SYSTEM_MESSAGE = """You are a STRICT educational assessor for UPSC exam preparation.

⚠️ CRITICAL: EVERY RESPONSE MUST BE UNIQUE AND DYNAMIC!
- DO NOT use template or generic responses
- Analyze the ACTUAL content provided
- Generate SPECIFIC scores based on what you analyze
- Each analysis must be different based on the actual submission
- NEVER give the same score or feedback twice

YOUR PRIMARY JOB:
1. Read the KEY POINTS from the video that students should know
2. Read the STUDENT'S ACTUAL RESPONSE
3. COMPARE them point-by-point
4. Generate a UNIQUE score and analysis based on actual matching

STRICT SCORING RULES:
- Count how many key points the student mentioned correctly
- coverage_percentage = (points covered / total key points) × 100
- If student covers 50% of key points → base_score around 50
- If student covers 100% of key points → base_score around 95-100
- If student covers 25% of key points → base_score around 25-30
- Deduct 5 points for each irrelevant/wrong item (max -20)
- Final recall_score = base_score - penalty_applied

IMPORTANT - SCORING EXAMPLES:
- Student mentions 2 of 4 key points → coverage 50%, base_score ~50
- Student mentions 4 of 4 key points → coverage 100%, base_score ~95
- Student mentions 1 of 4 key points + 2 irrelevant → coverage 25%, penalty 10, final ~15

RESPOND WITH ONLY A JSON OBJECT:
{
  "is_relevant": true,
  "relevance_message": "",
  "coverage_percentage": [CALCULATE THIS - must match actual content coverage],
  "base_score": [CALCULATE THIS - must match coverage],
  "penalty_applied": [CALCULATE THIS - 5 per irrelevant item],
  "recall_score": [UNIQUE SCORE based on actual analysis],
  "understanding_level": "[Based on final score: Excellent/Good/Satisfactory/Needs Work/Insufficient]",
  "feedback": "[UNIQUE 2-3 sentence summary specific to THIS submission]",
  "detailed_analysis": "[UNIQUE detailed paragraph analyzing THIS specific response]",
  "strengths": ["[SPECIFIC to what THIS student did well]"],
  "areas_to_improve": ["[SPECIFIC to what THIS student missed]"],
  "key_takeaways": ["[What THIS student understood correctly]"],
  "concepts_covered": ["[ACTUAL key points from video that student mentioned]"],
  "concepts_missed": ["[ACTUAL key points from video that student did NOT mention]"],
  "matched_content": ["[SPECIFIC content from student that matches video]"],
  "unmatched_content": ["[SPECIFIC student content not in video but possibly correct]"],
  "irrelevant_content": ["[SPECIFIC incorrect or off-topic content with reason]"],
  "revision_priority": "[high if <50%, medium if 50-70%, low if >70%]",
  "memory_retention_tips": ["[SPECIFIC tips for THIS topic]"],
  "suggested_next_steps": ["[SPECIFIC actions based on what was missed]"],
  "confidence_score": [Your confidence in this assessment 0-100]
}"""


def build_prompt(request: RecallAnalysisRequest) -> str:
    """Build the prompt for AI analysis with unique identifiers"""
    import uuid
    
    # Generate unique submission ID for this analysis
    submission_id = uuid.uuid4().hex[:8]
    submission_time = datetime.utcnow().isoformat()
    
    # Try to load transcription document for actual video content
    segment_key = f"{request.cycle_id}_{request.day_number}_{request.part_number}_{request.segment_number}"
    
    transcription_key_points = None
    try:
        from app.services.transcription_service import get_key_points_from_document, get_video_document
        
        # First try to get the structured document
        document = get_video_document(segment_key)
        if document:
            # Build comprehensive key points from transcription
            transcription_key_points = get_key_points_from_document(segment_key)
            print(f"[Prelims Recall] Using transcription document for {segment_key}")
    except Exception as e:
        print(f"[Prelims Recall] Could not load transcription: {e}")
    
    # Determine key points to use (priority: transcription > provided > placeholder)
    if transcription_key_points and len(transcription_key_points) > 20:
        key_points = transcription_key_points
        source = "VIDEO TRANSCRIPTION"
    elif request.key_points and len(request.key_points.strip()) > 10:
        # Check if it's not a placeholder
        placeholder_texts = [
            "key points will load",
            "key points will appear",
            "not uploaded",
            "not provided"
        ]
        if not any(p in request.key_points.lower() for p in placeholder_texts):
            key_points = request.key_points
            source = "ADMIN PROVIDED"
        else:
            key_points = None
            source = None
    else:
        key_points = None
        source = None
    
    # Build key points section
    if key_points:
        # Number the key points for clear reference
        key_point_lines = [kp.strip() for kp in key_points.split('\n') if kp.strip() and kp.strip().startswith('-')]
        if not key_point_lines:
            key_point_lines = [kp.strip() for kp in key_points.replace(';', ',').split(',') if kp.strip()]
        
        if len(key_point_lines) <= 1 and '\n' in key_points:
            key_point_lines = [kp.strip() for kp in key_points.split('\n') if kp.strip()]
        
        num_key_points = len(key_point_lines)
        numbered_points = "\n".join([f"  {i+1}. {kp.lstrip('- ')}" for i, kp in enumerate(key_point_lines)])
        key_points_section = f"""VIDEO KEY POINTS ({num_key_points} total from {source} - student should cover ALL):
{numbered_points}"""
    else:
        # Fallback to topic-based evaluation
        num_key_points = 4
        key_points_section = f"""VIDEO KEY POINTS (Based on topic: "{request.segment_title}"):
The student should have covered the main concepts related to {request.segment_title}. 
Evaluate their understanding of this topic based on what they mentioned.
NOTE: No transcription available - using topic-based evaluation."""
    
    return f"""== UNIQUE SUBMISSION #{submission_id} at {submission_time} ==

VIDEO TOPIC: {request.segment_title}

{key_points_section}

STUDENT'S RESPONSE ({request.response_type}):
---
{request.response_text or "No specific text captured - evaluate based on what student submitted."}
---

ANALYSIS INSTRUCTIONS:
1. Go through EACH of the {num_key_points} key points above
2. Check which ones the student mentioned (add to concepts_covered)
3. Check which ones the student missed (add to concepts_missed)
4. Calculate: coverage_percentage = (covered / {num_key_points}) × 100
5. Identify any irrelevant or wrong content in student response
6. Generate a UNIQUE score for this specific submission #{submission_id}

PROVIDE YOUR ANALYSIS AS JSON NOW:"""


def parse_ai_response(response_text: str) -> dict:
    """Parse AI response JSON, handling markdown code blocks and extra text"""
    import re
    
    clean_response = response_text.strip()
    
    # Remove markdown code blocks
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.startswith("```"):
        clean_response = clean_response[3:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
    clean_response = clean_response.strip()
    
    # Try direct parsing first
    try:
        return json.loads(clean_response)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in the text
    json_match = re.search(r'\{[^{}]*"is_relevant"[^{}]*\}', clean_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON object
    json_match = re.search(r'\{[^{}]*"recall_score"[^{}]*\}', clean_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Last resort: try to extract between first { and last }
    first_brace = clean_response.find('{')
    last_brace = clean_response.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(clean_response[first_brace:last_brace+1])
        except json.JSONDecodeError:
            pass
    
    # If nothing works, raise the JSON error
    raise json.JSONDecodeError("Could not extract JSON from response", clean_response, 0)


def get_fallback_response(is_ai_failure: bool = False) -> RecallAnalysisResponse:
    """Return template response when AI fails or is unavailable"""
    return RecallAnalysisResponse(
        # Topic Relevance
        is_relevant=True,
        relevance_message="",
        
        # Core Metrics
        recall_score=72,
        understanding_level="Satisfactory",
        
        # Detailed Analysis
        feedback="Good effort on your recall. Consider covering all key points mentioned in the video." if not is_ai_failure else "Analysis completed using template - AI service temporarily unavailable.",
        detailed_analysis="Your response shows basic understanding of the topic. To improve your recall, try to structure your response around the main themes covered in the video segment. Focus on key definitions, dates, and relationships between concepts." if not is_ai_failure else "AI analysis was not available for this response. Please try again or continue with the learning material.",
        
        # Strengths & Improvements
        strengths=["Completed the segment", "Submitted response on time"],
        areas_to_improve=["Cover all key concepts mentioned", "Add more specific details and examples"],
        key_takeaways=["Topic awareness demonstrated"],
        
        # Concept Coverage
        concepts_covered=["General topic understanding"],
        concepts_missed=["Specific details pending AI analysis"],
        
        # Personalized Recommendations
        revision_priority="medium",
        memory_retention_tips=["Review the video segment one more time", "Make notes of key points", "Try explaining the concept in your own words"],
        suggested_next_steps=["Continue to the next segment", "Review this topic during revision"],
        
        # AI Metadata
        ai_source="template",
        ai_model=None,
        analysis_timestamp=datetime.utcnow().isoformat(),
        confidence_score=50
    )


@router.post("/analyze-recall", response_model=RecallAnalysisResponse)
async def analyze_recall(
    request: RecallAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze student's recall response using AI Router
    
    Compares the student's response against the key points from the video segment
    and provides a recall score with feedback. Includes topic relevance checking.
    """
    prompt = build_prompt(request)
    
    try:
        # Call AI Router - automatically selects optimal model
        result = await ai_router.route(
            prompt=prompt,
            system_message=SYSTEM_MESSAGE,
            max_tokens=600,
            temperature=0.3,
            is_complex=True  # Recall analysis is complex
        )
        
        response_text = result["content"]
        model_used = result.get("model", "unknown")
        provider = result.get("provider", "ai")
        
        try:
            parsed = parse_ai_response(response_text)
            
            is_relevant = parsed.get("is_relevant", True)
            relevance_message = parsed.get("relevance_message", "")
            
            return RecallAnalysisResponse(
                is_relevant=is_relevant,
                relevance_message=relevance_message,
                recall_score=min(100, max(0, int(parsed.get("recall_score", 0 if not is_relevant else 70)))),
                feedback=parsed.get("feedback", "Please submit a response about the video topic." if not is_relevant else "Analysis completed."),
                strengths=parsed.get("strengths", []) if is_relevant else [],
                areas_to_improve=parsed.get("areas_to_improve", ["Submit response about the correct topic"]) if not is_relevant else parsed.get("areas_to_improve", []),
                ai_source=f"ai_{provider}",
                ai_model=model_used,
                analysis_timestamp=datetime.utcnow().isoformat()
            )
        except json.JSONDecodeError:
            # AI response wasn't valid JSON, return template with warning
            return get_fallback_response(is_ai_failure=True)
            
    except Exception as e:
        print(f"AI analysis failed: {str(e)}")
        # Return template response instead of throwing error
        return get_fallback_response(is_ai_failure=True)


@router.post("/analyze-recall-demo", response_model=RecallAnalysisResponse)
async def analyze_recall_demo(
    request: RecallAnalysisRequest
):
    """
    Demo endpoint for recall analysis (no auth required)
    For testing purposes - includes topic relevance checking
    """
    import traceback
    
    print(f"\n[Prelims Recall] === Starting Analysis ===")
    print(f"[Prelims Recall] Segment: {request.segment_title}")
    print(f"[Prelims Recall] Response type: {request.response_type}")
    print(f"[Prelims Recall] Key points: {request.key_points[:100] if request.key_points else 'EMPTY'}...")
    print(f"[Prelims Recall] Response text: {request.response_text[:100] if request.response_text else 'EMPTY'}...")
    
    prompt = build_prompt(request)
    print(f"[Prelims Recall] Prompt built successfully")
    
    try:
        print(f"[Prelims Recall] Calling AI Router...")
        
        # Call AI Router - automatically selects optimal model
        result = await ai_router.route(
            prompt=prompt,
            system_message=SYSTEM_MESSAGE,
            max_tokens=1500,  # Increased for comprehensive unique analysis
            temperature=0.5,  # Increased for more varied responses
            is_complex=True  # Recall analysis is complex
        )
        
        print(f"[Prelims Recall] AI Router returned successfully!")
        print(f"[Prelims Recall] Model used: {result.get('model', 'unknown')}")
        
        response_text = result["content"]
        model_used = result.get("model", "unknown")
        provider = result.get("provider", "ai")
        
        print(f"[Prelims Recall] Parsing AI response...")
        
        try:
            parsed = parse_ai_response(response_text)
            
            is_relevant = parsed.get("is_relevant", True)
            relevance_message = parsed.get("relevance_message", "")
            recall_score = min(100, max(0, int(parsed.get("recall_score", 0 if not is_relevant else 70))))
            
            print(f"[Prelims Recall] SUCCESS! Score: {recall_score}")
            
            return RecallAnalysisResponse(
                # Topic Relevance
                is_relevant=is_relevant,
                relevance_message=relevance_message,
                
                # Core Metrics
                recall_score=recall_score,
                understanding_level=parsed.get("understanding_level", "Satisfactory"),
                coverage_percentage=parsed.get("coverage_percentage", 0),
                
                # Detailed Analysis
                feedback=parsed.get("feedback", "Analysis completed."),
                detailed_analysis=parsed.get("detailed_analysis", ""),
                
                # Strengths & Improvements
                strengths=parsed.get("strengths", []) if is_relevant else [],
                areas_to_improve=parsed.get("areas_to_improve", []),
                key_takeaways=parsed.get("key_takeaways", []),
                
                # Concept Coverage
                concepts_covered=parsed.get("concepts_covered", []),
                concepts_missed=parsed.get("concepts_missed", []),
                
                # Content Matching Analysis
                matched_content=parsed.get("matched_content", []),
                unmatched_content=parsed.get("unmatched_content", []),
                irrelevant_content=parsed.get("irrelevant_content", []),
                
                # Penalty & Scoring
                penalty_applied=parsed.get("penalty_applied", 0),
                base_score=parsed.get("base_score", recall_score),
                
                # Personalized Recommendations
                revision_priority=parsed.get("revision_priority", "medium"),
                memory_retention_tips=parsed.get("memory_retention_tips", []),
                suggested_next_steps=parsed.get("suggested_next_steps", []),
                
                # AI Metadata
                ai_source=f"ai_{provider}",
                ai_model=model_used,
                analysis_timestamp=datetime.utcnow().isoformat(),
                confidence_score=parsed.get("confidence_score", 80)
            )
        except json.JSONDecodeError as je:
            print(f"[Prelims Recall] JSON Parse Error: {je}")
            print(f"[Prelims Recall] Raw response: {response_text[:500]}")
            return get_fallback_response(is_ai_failure=True)
            
    except Exception as e:
        print(f"[Prelims Recall] ERROR: {type(e).__name__}: {str(e)}")
        print(f"[Prelims Recall] Traceback:\n{traceback.format_exc()}")
        return get_fallback_response(is_ai_failure=True)


@router.get("/usage-stats")
async def get_usage_stats():
    """
    Get AI usage statistics showing:
    - Total requests
    - Token usage by model
    - Cost breakdown by task type
    
    This helps monitor AI costs and optimize model selection.
    """
    return ai_router.get_usage_summary()


@router.get("/test-ai")
async def test_ai():
    """
    Simple test endpoint to verify AI is working.
    Visit: http://localhost:8000/api/v1/prelims/test-ai
    """
    import traceback
    
    print("\n[TEST-AI] === Testing AI Connection ===")
    
    try:
        result = await ai_router.route(
            prompt="Say hello in exactly 5 words.",
            system_message="You are a helpful assistant. Respond concisely.",
            max_tokens=50,
            temperature=0.3
        )
        
        print(f"[TEST-AI] SUCCESS! Model: {result.get('model')}")
        print(f"[TEST-AI] Response: {result.get('content')}")
        
        return {
            "status": "success",
            "message": "AI is working!",
            "model_used": result.get("model"),
            "provider": result.get("provider"),
            "ai_response": result.get("content")
        }
    except Exception as e:
        print(f"[TEST-AI] FAILED: {type(e).__name__}: {str(e)}")
        print(f"[TEST-AI] Traceback:\n{traceback.format_exc()}")
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
