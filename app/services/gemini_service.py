import os
import httpx
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings

class GeminiService:
    """
    FRESH 2025 AI SERVICE IMPLEMENTATION
    
    Features:
    1. Tiered Access: Free vs Premium students.
    2. Model Cascading: Gemini 3 -> Gemma 3 -> Llama 3.3 (Ensures 100% availability).
    3. Smart Routing: High-precision tasks (OCR/Graphology) use Gemini 3 Pro for Premium.
    """

    def __init__(self):
        # Primary Keys
        self.free_key = settings.FREE_GEMINI_API_KEY
        self.paid_key = settings.PAID_GEMINI_API_KEY
        
        # Fallback Keys (OpenRouter)
        self.gemma_key = settings.GEMMA_API_KEY
        self.llama_key = settings.LLAMA_API_KEY
        
        self.base_url = settings.OPENROUTER_BASE_URL
        self.default_model = settings.DEFAULT_AI_MODEL or "google/gemini-3-flash-preview"

    def _get_execution_plan(self, user: Any = None, is_complex: bool = False) -> List[Tuple[str, str]]:
        """
        Determines the plan of (API_KEY, MODEL) pairs to try in order.
        """
        is_premium = getattr(user, "is_premium", False) or getattr(user, "subscription_status", "free") == "active"
        
        plan = []
        
        if is_premium:
            if is_complex:
                # Premium Complex Plan: Paid Pro -> Fallback to Flash
                plan.append((self.paid_key or self.free_key, "google/gemini-3-pro-preview"))
                plan.append((self.free_key, "google/gemini-3-flash-preview"))
            else:
                # Premium Simple Plan: Free Flash -> Paid Pro (as fallback)
                plan.append((self.free_key, "google/gemini-3-flash-preview"))
                plan.append((self.paid_key, "google/gemini-3-pro-preview"))
        else:
            # Free Plan: Flash -> Gemma -> Llama
            plan.append((self.free_key, "google/gemini-3-flash-preview"))
            
        # Global Fallbacks (Available to all if primary fails)
        if self.gemma_key:
            plan.append((self.gemma_key, "google/gemma-3-27b-it:free"))
        if self.llama_key:
            plan.append((self.llama_key, "meta-llama/llama-3.3-70b-instruct:free"))
            
        return plan

    async def _call_api(self, api_key: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Low-level API caller"""
        if not api_key:
            raise ValueError("Missing API Key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://eduecosystem.com",
            "X-Title": "Eduecosystem - Mastery Learning",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")

    def _call_api_sync(self, api_key: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Sync version of the API caller for backward compatibility"""
        if not api_key:
            raise ValueError("Missing API Key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://eduecosystem.com",
            "X-Title": "Eduecosystem - Mastery Learning",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")

    def generate_text(self, prompt: str, user: Any = None, is_complex: bool = False, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generates text with cascading fallback mechanism"""
        messages = [{"role": "user", "content": prompt}]
        plan = self._get_execution_plan(user, is_complex)
        
        last_error = "No API keys configured"
        for api_key, model in plan:
            try:
                return self._call_api_sync(api_key, model, messages, temperature, max_tokens)
            except Exception as e:
                last_error = str(e)
                print(f"Fallback: {model} failed, trying next... Error: {e}")
                continue
        
        return f"AI Service Unavailable. Last error: {last_error}"

    def analyze_image(self, image_path: str, prompt: str, user: Any = None, temperature: float = 0.4) -> str:
        """Analyze image with cascading vision support"""
        import base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = image_path.lower().split(".")[-1]
        mime_type = f"image/{ext}" if ext in ["png", "jpg", "jpeg", "gif", "webp"] else "image/jpeg"
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
            ],
        }]
        
        # For vision, we strictly try Gemini models first as they are best at it
        plan = self._get_execution_plan(user, is_complex=True)
        
        last_error = ""
        for api_key, model in plan:
            # Skip non-vision models if necessary (Gemma/Llama might not support multi-modal on all endpoints)
            if "gemma" in model or "llama" in model:
                continue 
            try:
                return self._call_api_sync(api_key, model, messages, temperature, 2000)
            except Exception as e:
                last_error = str(e)
                continue
                
        return f"Image Analysis Error: {last_error}"

    def chat(self, messages: List[Dict[str, str]], user: Any = None, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """Multi-turn chat with cascading fallback"""
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            role = "assistant" if msg.get("role", "").lower() in ["assistant", "ai", "bot"] else "user"
            api_messages.append({"role": role, "content": msg["content"]})

        plan = self._get_execution_plan(user, is_complex=False)
        
        last_error = ""
        for api_key, model in plan:
            try:
                return self._call_api_sync(api_key, model, api_messages, temperature, 1000)
            except Exception as e:
                last_error = str(e)
                continue
        
        return f"Chat Error: {last_error}"

    def analyze_comprehension(
        self, 
        student_summary: str, 
        key_concepts: List[str], 
        user: Any = None
    ) -> Dict[str, Any]:
        """
        Analyze student's Feynman explanation for comprehension scoring.
        Used by the Retention System for FSRS calculations.
        
        Returns:
            {
                "score": float (0.0-1.0),
                "grade": int (1-4 FSRS grade),
                "missing_concepts": List[str],
                "feedback": str
            }
        """
        prompt = f"""You are an educational assessment AI. Analyze how well the student explained these concepts.

KEY CONCEPTS TO CHECK:
{chr(10).join([f"- {c}" for c in key_concepts])}

STUDENT'S EXPLANATION:
{student_summary}

SCORING:
- 0.0-0.4 = Failed to cover most concepts
- 0.5-0.6 = Partial understanding, key gaps
- 0.7-0.8 = Good understanding, minor gaps
- 0.9-1.0 = Excellent, comprehensive understanding

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "score": 0.XX,
    "grade": X,
    "missing_concepts": ["concept1", "concept2"],
    "feedback": "Brief feedback message"
}}

Only respond with the JSON, no other text."""

        try:
            response = self.generate_text(prompt, user=user, is_complex=False, temperature=0.3, max_tokens=500)
            
            # Parse JSON response
            import json
            # Clean response in case of markdown
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            result = json.loads(response.strip())
            
            # Ensure valid values
            score = max(0.0, min(1.0, float(result.get("score", 0.5))))
            grade = max(1, min(4, int(result.get("grade", 2))))
            
            return {
                "score": score,
                "grade": grade,
                "missing_concepts": result.get("missing_concepts", []),
                "feedback": result.get("feedback", "Review complete.")
            }
            
        except Exception as e:
            print(f"Comprehension analysis error: {e}")
            # Fallback: simple word-based scoring
            words = len(student_summary.split())
            basic_score = min(1.0, words / 100)
            return {
                "score": basic_score,
                "grade": 2 if basic_score < 0.5 else 3,
                "missing_concepts": [],
                "feedback": "Unable to perform AI analysis, using basic scoring."
            }


# Global instance
gemini_service = GeminiService()
