import random
import os
from typing import Any
from app.services.gemini_service import gemini_service

# Initialize reader lazily
reader = None

def get_reader():
    global reader
    if reader is None:
        import easyocr
        # GPU=False to be safe on standard environments
        reader = easyocr.Reader(["en"], gpu=False)
    return reader


def analyze_handwriting(image_path: str, user: Any = None) -> dict:
    """
    Analyze handwriting using EasyOCR for text extraction
    and Gemini AI for personality analysis.
    """
    if not os.path.exists(image_path):
        return {"error": "File not found"}

    try:
        # Extract text using EasyOCR
        r = get_reader()
        result = r.readtext(image_path, detail=0)
        extracted_text = " ".join(result)

        if not extracted_text:
            extracted_text = "[No text detected. Please try a clearer image.]"

    except Exception as e:
        print(f"OCR Error: {e}")
        extracted_text = "[Error processing image]"

    # Use Gemini Vision API for personality analysis
    analysis_prompt = """Analyze this handwriting sample image for graphology/personality insights.

Please analyze the following characteristics:
1. Baseline (straight, ascending, descending, wavy)
2. Slant (vertical, right, left, variable)
3. Pressure (heavy, light, medium)
4. Size (large, small, medium)
5. Spacing (wide, narrow, balanced)

Based on these characteristics, provide:
- Personality traits indicated by the handwriting
- Confidence score (0.0-1.0) for the analysis
- A detailed personality analysis paragraph

Format the response as:
Baseline: [value]
Slant: [value]
Pressure: [value]
Size: [value]
Spacing: [value]
Confidence: [0.0-1.0]

Personality Traits: [list traits]

Analysis: [detailed paragraph about personality based on handwriting]
"""

    try:
        # Use Gemini Vision to analyze the handwriting with tiered logic
        gemini_analysis = gemini_service.analyze_image(
            image_path, analysis_prompt, user=user, temperature=0.4
        )

        # Parse Gemini response
        features = {}
        traits = []
        analysis_text = gemini_analysis

        # Simple parsing of structured response
        lines = gemini_analysis.split("\n")
        for line in lines:
            if ":" in line:
                key_val = line.split(":", 1)
                key = key_val[0].strip().lower()
                val = key_val[1].strip()

                if key == "baseline":
                    features["baseline"] = val
                elif key == "slant":
                    features["slant"] = val
                elif key == "pressure":
                    features["pressure"] = val
                elif key == "size":
                    features["size"] = val
                elif key == "spacing":
                    features["spacing"] = val
                elif key == "confidence":
                    try:
                        features["confidence_score"] = float(val)
                    except:
                        features["confidence_score"] = 0.75
                elif key == "personality traits":
                    traits = [t.strip() for t in val.split(",")]

        if "API_ERROR:" in gemini_analysis:
             features = {
                "confidence_score": 0.0,
                "error": gemini_analysis
            }
             analysis_text = gemini_analysis
        # If parsing failed, use fallback mock features
        elif not features:
            # Return error state instead of mocks
            features = {
                "confidence_score": 0.0,
                "error": "Could not extract features from AI response"
            }
            analysis_text = f"AI Analysis failed to generate structured data. Raw response: {gemini_analysis[:100]}..."

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        features = {
            "confidence_score": 0.0,
            "error": str(e)
        }
        analysis_text = "AI Analysis unavailable."

    return {
        "extracted_text": extracted_text,
        "features": features,
        "analysis": analysis_text,
    }
