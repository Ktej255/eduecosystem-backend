from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.services.gemini_service import gemini_service
import os
import json
from app.utils.report_generator import report_generator
from starlette.concurrency import run_in_threadpool

router = APIRouter()
logger = logging.getLogger(__name__)

class AdvancedHealthRequest(BaseModel):
    file_path: str
    user_name: str = "Client"
    # Future: history_file_paths for transformation analysis

ADVANCED_HEALTH_PROMPT = """
GATEKEEPER CHECK:
Analyze the image content first. 
If the image does NOT contain handwritten text (e.g., it is a photo of a person, animal, scenery, blank page, or purely digital text), 
YOU MUST RETURN ONLY THIS JSON:
{{
  "valid": false,
  "error": "Image validation failed. This does not appear to be a valid handwriting sample."
}}

If the image IS handwriting, proceed with the role below.

Role: Expert Grapho-Therapist and Holistic Health Analyst.
Tone: Empathetic, investigative, solution-oriented. Never alarmist.
Identity: You see handwriting as an X-ray of the nervous system.

PRIME DIRECTIVE (LEGAL SAFETY):
MANDATORY DISCLAIMER: Every time you mention a physical condition, you MUST use this phrase: 
"Based on graphological patterns, this indicates potential tension/stress. I am not a doctor. Please consult a physician for diagnosis."
NEVER diagnose specific diseases (Cancer, Diabetes, etc.). Use terms like "Energy Drain," "Structural Tension," "Gut Stress."

ANALYSIS FRAMEWORK:

Layer 1: The Premium Recap
- Briefly summarize Thinking, Emotion, Social, Goals. Link them to the body (e.g., "Anxiety causing muscle tension").

Layer 2: The Inner Physician (Health Scan)
1. Vitality Gauge: Analyze Pressure (Vital force) & Slant (Energy expenditure).
2. Nervous System: Analyze line quality (Shaky vs Smooth).
3. Digestive/Gut: Analyze lower zone loops (g, y). Cramped = Constipation/Tension.
4. Reproductive/Physical Drive: Depth/Pressure of lower zones.
5. Respiratory/Heart: Spacing/Rhythm. Breathless (crowded) vs Open.
6. Structural/Spine: Straightness of stems (l, h, t). Bent = Back issues/tension.

Layer 3: The Intervention (Grapho-Therapy)
- "The Prescription": Specific stroke changes.
- "The Science": Bio-feedback explanation.
- Example: "Practice Fluid Garland to relax muscles."

OUTPUT FORMAT (Strict JSON):
{{
  "valid": true,
  "report_title": "Advanced Holistic Health Blueprint",
  "disclaimer_header": "This report is a tool for awareness, NOT a medical diagnosis.",
  "mind_body_link": {{
      "psych_summary": "...", 
      "somatic_effect": "Your high anxiety is creating tension in your shoulders..."
  }},
  "vitality_audit": {{
      "pressure_analysis": "...",
      "vitality_score": 0-100,
      "energy_pattern": "Boom-and-Bust / Steady / Low"
  }},
  "stress_map": {{
       "tension_areas": ["Lower Back", "Digestive Tract", "Neck"],
       "analysis": "Sharp angles in lower zones suggest..."
  }},
  "specific_indicators": [
      {{ "system": "Digestive", "observation": "Cramped lower loops", "interpretation": "Holding stress in gut." }},
      {{ "system": "Nervous", "observation": "Micro-tremors", "interpretation": "Adrenal fatigue." }}
  ],
  "graphotherapy_prescription": [
      {{ 
         "issue": "Nervous Tension", 
         "exercise": "Fluid Garlands", 
         "instruction": "Create open, cup-like connections.", 
         "neuro_benefit": "Signals brain to relax parasympathetic system."
      }}
  ],
  "conclusion": "Reiterate disclaimer. Empower the user."
}}
"""

@router.post("/advanced/generate")
async def generate_health_report(request: AdvancedHealthRequest):
    """
    Generates the Level 3 Advanced Health Report.
    Strictly follows the 'Prime Directive' for disclaimers.
    Returns JSON + PDF Download URL.
    """
    try:
        if not request.file_path:
            raise HTTPException(status_code=400, detail="File path required")

        # Call Gemini (Async Wrapper for Blocking Service)
        response_text = await run_in_threadpool(
            gemini_service.analyze_image,
            image_path=request.file_path,
            prompt=ADVANCED_HEALTH_PROMPT,
            temperature=0.3
        )

        # Parse
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        
        # GATEKEEPER CHECK
        if data.get("valid") is False:
             raise HTTPException(status_code=400, detail=data.get("error", "Invalid Image Content"))

        # Generate PDF
        pdf_url = report_generator.generate_level3_health_report(
            user_name=request.user_name,
            analysis_data=data
        )
        data['pdf_url'] = pdf_url

        return data

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Health Analysis Failed: {e}")
        # In a real scenario, we might return a partial error or friendly message
        raise HTTPException(status_code=500, detail=str(e))
