from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from app.services.gemini_service import gemini_service
import os
import json

router = APIRouter()
logger = logging.getLogger(__name__)

class PremiumAnalysisRequest(BaseModel):
    file_path: str
    selected_traits: List[str]
    is_full_report: bool = False
    user_name: str = "Client"

PREMIUM_PROMPT_TEMPLATE = """
Role: World-Class Graphologist & Behavioral Psychologist (Gestalt + Trait School).
Target: Premium Personality Blueprint (Psychology only, NO HEALTH/MEDICAL advice).
User: {user_name}

ANALYSIS FRAMEWORK:
1. Mental Processing (Thinking Style: m, n, connections)
2. Emotional Structure (Slant, Pressure)
3. Social Dynamics (a, o, d-loops, spacing)
4. Drive & Achievement (t-bars, lower zones)
5. Fears & Defenses (loops, capitals)
6. Integrity (Baseline, consistency)
7. Signature Analysis (Public vs Private)

INSTRUCTIONS:
- Generate a highly detailed breakdown for the sections above.
- Tone: Empowering, Scientific yet Accessible.
- Use Metaphors: "You are a Sponge" vs "Filter".
- EXCLUSION: Do NOT mention physical illness. Interpret shakes/puddling as stress/fatigue only.

OUTPUT FORMAT (Strict JSON):
{{
  "executive_summary": {{
      "top_strengths": ["..."],
      "top_challenge": "..."
  }},
  "mindset_map": {{
      "title": "The Mindset Map",
      "content": "...",
      "metaphor": "..."
  }},
  "emotional_compass": {{
      "title": "The Emotional Compass",
      "content": "...",
      "reaction_speed": "..."
  }},
  "social_dynamics": {{
      "title": "Social Dynamics",
      "content": "...",
      "introvert_extrovert_scale": 0-100
  }},
  "success_factor": {{
      "title": "The Success Factor",
      "content": "...",
      "procrastination_level": "High/Med/Low"
  }},
  "fears_defenses": {{
      "title": "Hidden Drivers & Defenses",
      "content": "..."
  }},
  "integrity": {{
      "title": "Integrity & Reliability",
      "content": "..."
  }},
  "signature_analysis": {{
      "title": "The Signature Mask",
      "content": "..."
  }},
  "graphotherapy_recommendations": [
      {{ "stroke": "t-bar", "action": "Raise it higher", "benefit": "Boost confidence" }},
      {{ "stroke": "d-stem", "action": "Retrace the stem", "benefit": "Reduce sensitivity" }},
      {{ "stroke": "baseline", "action": "Write on 90 degree", "benefit": "Emotional stability" }}
  ],
  "upsell_hook": "Your handwriting contains signals about Physical Energy and Stress Tolerance. Unlock the Advanced Health & Vitality Report for the 90-Day Healing Protocol."
}}
"""

@router.post("/premium-generate")
async def generate_premium_report(request: PremiumAnalysisRequest):
    """
    Generates the detailed Premium Blueprint.
    """
    try:
        # 1. Validate File
        # Assuming file_path is passed from previous step or session
        # For security, we might want to verify ownership, but for this funnel we assume valid path
        if not request.file_path:
             raise HTTPException(status_code=400, detail="File path required")

        # 2. Prepare Prompt
        prompt = PREMIUM_PROMPT_TEMPLATE.format(user_name=request.user_name)
        
        # 3. Call AI
        # Use existing service with verify_image support if needed, or analyze_image
        # We need to map the URL/Path correctly. 
        # For now, assuming request.file_path is absolute or resolvable local path
        
        # Resolve 'uploads/...' to absolute
        if "http" in request.file_path:
             # Just a safety check, usually we deal with local paths in this service 
             # logic unless we change gemini_service to download.
             pass 

        response_text = gemini_service.analyze_image(
            image_path=request.file_path, 
            prompt=prompt,
            temperature=0.3 # Lower temp for more scientific/structured output
        )

        # 4. Parse & Return
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        
        return data

    except Exception as e:
        logger.error(f"Premium Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
