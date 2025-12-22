"""
AI Service using OpenRouter
Replaces Google Gemini with OpenRouter models (Gemini 2.0 Flash, Gemma, Llama, Mistral)
"""

import os
from typing import Optional, List, Dict
import httpx


class GeminiService:
    """
    Service for AI operations using OpenRouter API.
    Named GeminiService for backward compatibility, but uses OpenRouter models.
    """

    def __init__(self, model_name: str = None):
        """
        Initialize OpenRouter AI service

        Args:
            model_name: OpenRouter model name (default: google/gemini-2.0-flash-exp:free)
        """
        from app.core.config import settings
        
        self.api_key = settings.OPENROUTER_API_KEY or settings.GROK_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model_name = model_name or settings.DEFAULT_AI_MODEL or "google/gemini-2.0-flash-exp:free"
        
        # Fallback API keys
        self.fallback_keys = [
            settings.GROK_API_KEY,  # Gemma 3 27B
            settings.LLAMA_API_KEY,  # Llama 3
            settings.MISTRAL_API_KEY,  # Mistral
        ]
        
        if self.api_key:
            print(f"✅ OpenRouter AI configured with model: {self.model_name}")
        else:
            print("WARNING: No OpenRouter API key found in environment variables")

    def generate_text(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000
    ) -> str:
        """
        Generate text using OpenRouter API

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        if not self.api_key:
            return "AI is not configured. Please set OPENROUTER_API_KEY."

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://eduecosystem.com",
                        "X-Title": "Sarit Classes - Holistic Learning",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    # Try fallback
                    return self._try_fallback(prompt, temperature, max_tokens, response.text)
                    
        except Exception as e:
            print(f"Error generating text: {e}")
            return f"Error: {str(e)}"

    def _try_fallback(
        self, prompt: str, temperature: float, max_tokens: int, original_error: str
    ) -> str:
        """Try fallback API keys if primary fails"""
        for fallback_key in self.fallback_keys:
            if not fallback_key or fallback_key == self.api_key:
                continue
            
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {fallback_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://eduecosystem.com",
                            "X-Title": "Sarit Classes",
                        },
                        json={
                            "model": "google/gemma-3-27b-it",  # Use Gemma as fallback model
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
            except:
                continue
        
        return f"Error with all AI models. Primary error: {original_error}"

    def analyze_image(
        self, image_path: str, prompt: str, temperature: float = 0.4
    ) -> str:
        """
        Analyze image using OpenRouter Vision model
        Note: Image analysis requires base64 encoding

        Args:
            image_path: Path to image file
            prompt: Analysis prompt/question
            temperature: Sampling temperature

        Returns:
            Analysis result
        """
        if not self.api_key:
            return "AI Vision is not configured. Please set OPENROUTER_API_KEY."

        try:
            import base64
            
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Determine image type
            ext = image_path.lower().split(".")[-1]
            mime_type = f"image/{ext}" if ext in ["png", "jpg", "jpeg", "gif", "webp"] else "image/jpeg"
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://eduecosystem.com",
                        "X-Title": "Sarit Classes",
                    },
                    json={
                        "model": "google/gemini-2.0-flash-exp:free",  # Use Gemini for vision
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                        ],
                        "temperature": temperature,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error analyzing image: {response.text}"
                    
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return f"Error: {str(e)}"

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Multi-turn chat conversation

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system instruction
            temperature: Sampling temperature

        Returns:
            AI response
        """
        if not self.api_key:
            return "AI is not configured. Please set OPENROUTER_API_KEY."

        try:
            # Build messages list
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            
            # Convert message format
            for msg in messages:
                role = "assistant" if msg.get("role", "").lower() in ["assistant", "ai", "bot"] else "user"
                api_messages.append({"role": role, "content": msg["content"]})
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://eduecosystem.com",
                        "X-Title": "Sarit Classes",
                    },
                    json={
                        "model": self.model_name,
                        "messages": api_messages,
                        "temperature": temperature,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error in chat: {response.text}"
                    
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"Error: {str(e)}"


# Global instance
gemini_service = GeminiService()
