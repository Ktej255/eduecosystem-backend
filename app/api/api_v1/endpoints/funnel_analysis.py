"""
Funnel Analysis Endpoint
Analyzes handwriting samples using Gemini Vision
"""

import shutil
import os
import uuid
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from app.services.gemini_service import gemini_service
from app.api import deps

router = APIRouter()

TEMP_UPLOAD_DIR = Path("temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

ANALYSIS_PROMPT = """
You are an expert Graphologist & Sales Psychologist.

1. CORE INSTRUCTIONS
Objective: Analyze the handwriting sample to generate a "Free Preliminary Personality Snapshot" (Teaser Report).
The Rules:
- The "Tip of the Iceberg": Provide value but do not connect all dots. Leave the "why" for the paid report.
- The 95% Consistency: Analysis must be accurate to the traits, but vary metaphors (Architect, Ocean, Mountain Climber) to feel human.
- The Curiosity Gap: End sections with open loops/questions.
- Tone: Professional, encouraging, intriguing, mysterious.

2. DATA INPUT (Scan for these Gateway Traits)
- Slant (Emotional Expressiveness)
- Size (Concentration/Extroversion)
- Baseline (Mood Stability)
- T-Bars (Goals/Self-Esteem)
*Select ONLY 3 of these to discuss.*

3. OUTPUT FORMAT (Strict JSON)
Return the analysis in this JSON structure:
{
    "hook": "Dynamic opening sentence (e.g. 'Your handwriting is a whisper from your subconscious...')",
    "insights": [
        {
            "title": "Insight 1: The Mind (or Heart/Drive)",
            "analysis": "Analysis using a metaphor (Laser focus vs Floodlight).",
            "shadow_hint": "Shadow Hint regarding a potential leak or barrier..."
        },
        {
            "title": "Insight 2: The Heart",
            "analysis": "Analysis of slant/connection. Heart-led vs Head-led.",
            "shadow_hint": "Hint about protecting this sensitivity..."
        },
        {
            "title": "Insight 3: The Drive",
            "analysis": "Analysis of T-bars/pressure.",
            "shadow_hint": "Hint about sustained energy vs burnout..."
        }
    ],
    "blind_spot": {
        "title": "The Blind Spot",
        "description": "Identify one contradictory/hidden trait (The Unfinished Symphony)."
    },
    "verdict": {
        "title": "The Verdict",
        "description": "Based on this snapshot, you are a [Adjective 1], [Adjective 2], and [Adjective 3] individual with untapped potential."
    },
    "upsell": {
        "problem": "However, this scratches the surface. We haven't analyzed your Success Barriers or Defense Mechanisms.",
        "solution": "Your full 45-Page 'Blueprint of You' is ready to be unlocked."
    },
    "overall_score": 85  // Generate a 'Potential Score' (0-100) based on positive indicators
}
"""

@router.post("/analyze")
async def analyze_handwriting(
    files: List[UploadFile] = File(...)
):
    """
    Analyze uploaded handwriting samples using Gemini Vision.
    Returns structured JSON analysis.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Save first file temporarily (Gemini Vision usually needs one good sample or we can collage them)
    # For now, analyze the first image
    file = files[0]
    file_ext = file.filename.split(".")[-1]
    temp_filename = f"{uuid.uuid4()}.{file_ext}"
    temp_path = TEMP_UPLOAD_DIR / temp_filename

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Call Gemini Service
        # Note: analyze_image in gemini_service expects a path string
        # We need to parse the JSON response
        
        response_text = await gemini_service.analyze_image(
            image_path=str(temp_path),
            prompt=ANALYSIS_PROMPT,
            temperature=0.2
        )
        
        # Cleanup json markdown if present
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        analysis_data = json.loads(cleaned_response)
        
        return analysis_data

    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "error": "Failed to parse AI response",
            "raw_response": response_text
        }
    except Exception as e:
        print(f"Analysis Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
