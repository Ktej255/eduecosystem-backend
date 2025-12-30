import os
import httpx
import google.generativeai as genai
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    """
    FRESH 2025 AI SERVICE IMPLEMENTATION - DIRECT GOOGLE API
    
    Features:
    1. Direct Google Access: Uses `google-generativeai` for 15 RPM Free Tier.
    2. Fallback Support: Keeps OpenRouter for specific models if needed.
    3. Multi-modal: Native image support via Gemini.
    """

    def __init__(self):
        # Primary Keys
        self.free_key = settings.FREE_GEMINI_API_KEY
        self.paid_key = settings.PAID_GEMINI_API_KEY
        
        # Configure Google GenAI
        if self.free_key:
            genai.configure(api_key=self.free_key)
        
        # Fallback Keys (OpenRouter)
        self.gemma_key = settings.GEMMA_API_KEY
        self.llama_key = settings.LLAMA_API_KEY
        
        self.base_url = settings.OPENROUTER_BASE_URL
        self.default_model = "gemini-1.5-flash" # Safe default for Google

    def _get_execution_plan(self, user: Any = None, is_complex: bool = False) -> List[Tuple[str, str, str]]:
        """
        Determines the plan of (PROVIDER, API_KEY, MODEL) triples to try.
        Now detects if keys are Google (AIza...) or OpenRouter (sk-or-...).
        """
        is_premium = getattr(user, "is_premium", False) or getattr(user, "subscription_status", "free") == "active"
        
        plan = []

        def get_provider(key: str) -> str:
            if key.startswith("AIza"):
                return "google"
            return "openrouter"

        # 1. Primary: FREE_GEMINI_API_KEY
        if self.free_key:
            provider = get_provider(self.free_key)
            model = "gemini-1.5-flash" if provider == "google" else "google/gemini-2.0-flash-exp:free"
            plan.append((provider, self.free_key, model))
            
            # If it's openrouter, add a backup model
            if provider == "openrouter":
                plan.append((provider, self.free_key, "google/gemini-1.5-flash:free"))
                plan.append((provider, self.free_key, "google/gemini-flash-1.5-8b:free"))

        # 2. Premium: PAID_GEMINI_API_KEY
        if self.paid_key:
            provider = get_provider(self.paid_key)
            model = "gemini-1.5-pro" if provider == "google" else "google/gemini-pro-1.5"
            plan.append((provider, self.paid_key, model))

        # 3. Specific Fallbacks
        if self.gemma_key:
            plan.append(("openrouter", self.gemma_key, "google/gemma-2-9b-it:free"))
        if self.llama_key:
            plan.append(("openrouter", self.llama_key, "meta-llama/llama-3.3-70b-instruct:free"))
            
        return plan

    def _call_google(self, api_key: str, model_name: str, messages: List[Dict[str, str]], temperature: float) -> str:
        """Call Google Generic AI SDK"""
        # Configure specifically for this call (in case of multiple keys)
        genai.configure(api_key=api_key)
        
        # Convert OpenAI format messages to Gemini format
        # User -> user, Assistant -> model
        history = []
        system_instruction = None
        current_user_message = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                current_user_message = content # Last message is the prompt
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
            else: # previous user messages
                 history.append({"role": "user", "parts": [content]})

        # Instantiate Model
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        
        # Generate
        # Note: Gemini python lib chat history is stateful, but here we just want generation
        # passing history as 'contents' if needed, generally usually just text generation for simple usage
        # or chat.
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            candidate_count=1,
        )
        
        if history:
             chat = model.start_chat(history=history)
             response = chat.send_message(current_user_message, generation_config=generation_config)
             return response.text
        else:
             response = model.generate_content(current_user_message, generation_config=generation_config)
             return response.text


    def _call_openrouter_sync(self, api_key: str, model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Sync version of the OpenRouter API caller"""
        if not api_key:
            raise ValueError("Missing OpenRouter API Key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://eduecosystem.com",
            "X-Title": "Eduecosystem",
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
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                     return data["choices"][0]["message"]["content"]
                return "Empty response from AI"
            else:
                raise Exception(f"OpenRouter Error {response.status_code}: {response.text}")

    def generate_text(self, prompt: str, user: Any = None, is_complex: bool = False, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generates text with cascading fallback mechanism"""
        messages = [{"role": "user", "content": prompt}]
        plan = self._get_execution_plan(user, is_complex)
        
        last_error = "No API keys configured"
        
        for provider, api_key, model in plan:
            try:
                if not api_key: continue
                
                if provider == "google":
                    return self._call_google(api_key, model, messages, temperature)
                else:
                    return self._call_openrouter_sync(api_key, model, messages, temperature, max_tokens)
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Fallback: {provider}/{model} failed. Error: {e}")
                continue
        
        return f"AI Service Unavailable. Last error: {last_error}"

    def analyze_image(self, image_path: str, prompt: str, user: Any = None, temperature: float = 0.4) -> str:
        """Analyze image using Gemini Vision"""
        import PIL.Image
        
        plan = self._get_execution_plan(user, is_complex=True)
        # Filter for Google only
        google_plan = [p for p in plan if p[0] == "google"]
        
        last_error = ""
        
        # Load Image once
        try:
             img = PIL.Image.open(image_path)
        except Exception as e:
             return f"Error loading image: {e}"

        for provider, api_key, model in google_plan:
            try:
                if not api_key: continue
                genai.configure(api_key=api_key)
                m = genai.GenerativeModel(model)
                response = m.generate_content([prompt, img])
                return response.text
            except Exception as e:
                last_error = str(e)
                continue
                
        return f"Image Analysis Error: {last_error}"

    def chat(self, messages: List[Dict[str, str]], user: Any = None, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """Multi-turn chat"""
        # Inject system prompt into messages if needed for consistent format
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        plan = self._get_execution_plan(user, is_complex=False)
        
        last_error = ""
        for provider, api_key, model in plan:
            try:
                if not api_key: continue
                if provider == "google":
                    return self._call_google(api_key, model, api_messages, temperature)
                else:
                    return self._call_openrouter_sync(api_key, model, api_messages, temperature, 1000)
            except Exception as e:
                last_error = str(e)
                continue
        
        return f"Chat Error: {last_error}"

    def analyze_comprehension(self, student_summary: str, key_concepts: List[str], user: Any = None) -> Dict[str, Any]:
        """FSRS Retention Analysis"""
        prompt = f"""You are an educational assessment AI. Analyze score/1.0 and grade(1-4).
JSON ONLY:
{{
    "score": 0.XX,
    "grade": X,
    "missing_concepts": [],
    "feedback": "string"
}}
Concepts: {key_concepts}
Student: {student_summary}"""

        try:
            response = self.generate_text(prompt, user=user, is_complex=False, temperature=0.3)
            
            # Simple cleanup for markdown json
            import json
            clean = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
            return result
        except Exception as e:
             print(f"Analysis error: {e}")
             return {"score": 0.5, "grade": 2, "feedback": "AI Error", "missing_concepts": []}

# Global instance
gemini_service = GeminiService()
