import google.generativeai as genai
import os
from typing import Dict, Any, Optional
import json
import httpx
from PIL import Image
import io

from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class AIService:
    """
    Service to handle interactions with Google's Gemini Models.
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro-vision')
        self.chat_model = genai.GenerativeModel('gemini-pro')

    async def analyze_handwriting_comparison(self, baseline_url: str, current_url: str) -> Dict[str, Any]:
        """
        Compare two handwriting samples using Gemini Pro Vision.
        Returns a dictionary with scores and feedback.
        """
        if not API_KEY:
            print("Warning: No GEMINI_API_KEY found. Returning mock data.")
            return self._get_mock_response()

        try:
            # Download images to bytes
            baseline_img = await self._download_image(baseline_url)
            current_img = await self._download_image(current_url)

            if not baseline_img or not current_img:
                return self._get_mock_response(error="Image download failed")

            prompt = """
            Act as a master Graphologist. Compare these two handwriting samples.
            Image 1 is the 'Baseline' (Day 1). Image 2 is the 'Current' (Day 21) progress.

            Analyze the neurological transformation based on:
            1. Slant Consistency (Is it more stable?)
            2. Letter Connectedness (Fluidity of thought)
            3. Baseline Adherence (Emotional stability)
            4. Pressure (Energy levels)

            Return ONLY a valid JSON object with this structure:
            {
                "transformation_score": <integer 0-100>,
                "qualitative_feedback": "<string, a short encouraging paragraph about the specific improvements>",
                "metrics": [
                    {"name": "Slant Stability", "baseline_value": <0-100>, "current_value": <0-100>, "status": "Improved/Stable/Needs Work"},
                    {"name": "Letter Connectedness", "baseline_value": <0-100>, "current_value": <0-100>, "status": "Improved/Stable/Needs Work"},
                    {"name": "Baseline Adherence", "baseline_value": <0-100>, "current_value": <0-100>, "status": "Improved/Stable/Needs Work"}
                ]
            }
            """

            response = self.model.generate_content([prompt, baseline_img, current_img])
            
            # Clean response to ensure valid JSON
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text_response)

        except Exception as e:
            print(f"AI Analysis Failed: {str(e)}")
            return self._get_mock_response(error=str(e))

    async def _download_image(self, url: str) -> Optional[Image.Image]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content))
        except Exception as e:
            print(f"Failed to download image {url}: {e}")
            return None

    def _get_mock_response(self, error: str = "") -> Dict[str, Any]:
        """Fallback mock data"""
        msg = f"Analysis simulated (AI Error: {error})" if error else "Analysis simulated (No API Key)"
        return {
            "transformation_score": 75,
            "qualitative_feedback": f"{msg}. You are showing great consistency in your baseline adherence.",
            "metrics": [
                {"name": "Slant Stability", "baseline_value": 60, "current_value": 85, "status": "Improved"},
                {"name": "Letter Connectedness", "baseline_value": 50, "current_value": 78, "status": "Improved"},
                {"name": "Baseline Adherence", "baseline_value": 70, "current_value": 75, "status": "Stable"}
            ]
        }

ai_service = AIService()
