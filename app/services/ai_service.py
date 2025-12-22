"""
AI Service Integration
Provides unified interface for OpenAI and Claude APIs
"""

import os
from typing import Optional, List, Dict
import openai
from anthropic import Anthropic
import asyncio


class AIService:
    """Unified AI service for OpenAI, Claude, and Grok"""

    def __init__(self):
        from app.core.config import settings
        
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.openrouter_key = settings.OPENROUTER_API_KEY or settings.GROK_API_KEY
        self.grok_key = settings.GROK_API_KEY  # Legacy, for backward compatibility
        
        # Default to OpenRouter/Gemini if key is present, otherwise fallback
        self.default_provider = os.getenv("AI_PROVIDER", "grok" if self.openrouter_key else "openai")

        if self.openai_key:
            openai.api_key = self.openai_key

        if self.claude_key:
            self.claude_client = Anthropic(api_key=self.claude_key)

    async def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ) -> str:
        """
        Generate text using AI
        """
        provider = provider or self.default_provider

        try:
            if provider == "grok" and self.grok_key:
                return await self._generate_grok(
                    prompt, system_message, max_tokens, temperature
                )
            elif provider == "openai" and self.openai_key:
                return await self._generate_openai(
                    prompt, system_message, max_tokens, temperature
                )
            elif provider == "claude" and self.claude_key:
                return await self._generate_claude(
                    prompt, system_message, max_tokens, temperature
                )
            else:
                # Fallback logic
                if self.grok_key:
                    return await self._generate_grok(prompt, system_message, max_tokens, temperature)
                elif self.openai_key:
                    return await self._generate_openai(prompt, system_message, max_tokens, temperature)
                else:
                    raise ValueError(f"No API key configured for provider: {provider}")
        except Exception as e:
            # Fallback to other provider if available
            if provider != "grok" and self.grok_key:
                return await self._generate_grok(prompt, system_message, max_tokens, temperature)
            elif provider != "openai" and self.openai_key:
                return await self._generate_openai(prompt, system_message, max_tokens, temperature)
            raise e

    async def _generate_grok(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Grok (via OpenRouter)"""
        from app.core.config import settings
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Create a specialized client for OpenRouter (Gemini 2.0 Flash)
        # We use the openai library but point it to OpenRouter
        client = openai.AsyncOpenAI(
            api_key=self.openrouter_key,
            base_url=settings.OPENROUTER_BASE_URL,
        )

        response = await client.chat.completions.create(
            model=settings.DEFAULT_AI_MODEL,  # google/gemini-2.0-flash-exp:free
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://eduecosystem.com", # Optional, for OpenRouter rankings
                "X-Title": "Holistic Learning Ecosystem",
            }
        )

        return response.choices[0].message.content

    async def _generate_openai(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using OpenAI GPT-4"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    async def _generate_claude(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Claude"""
        message = await asyncio.to_thread(
            self.claude_client.messages.create,
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    async def generate_quiz_questions(
        self, content: str, num_questions: int = 5, difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate quiz questions from content

        Args:
            content: Learning content
            num_questions: Number of questions to generate
            difficulty: easy, medium, or hard
        """
        system_message = """You are an expert educator. Generate multiple choice quiz questions from the given content.
Return a JSON array of questions with this structure:
[
  {
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Why this is correct"
  }
]
"""

        prompt = f"""Generate {num_questions} {difficulty} difficulty multiple choice questions from this content:

{content}

Return only the JSON array, no additional text."""

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=2000
        )

        import json

        return json.loads(response)

    async def generate_discussion_topics(
        self, course_title: str, lesson_title: str, content_summary: str
    ) -> List[str]:
        """Generate discussion topics for a lesson"""
        prompt = f"""Based on this lesson, suggest 3-5 interesting discussion topics that would engage students:

Course: {course_title}
Lesson: {lesson_title}
Summary: {content_summary}

Return topics as a JSON array of strings."""

        response = await self.generate_text(prompt=prompt, max_tokens=500)

        import json

        return json.loads(response)

    async def generate_course_summary(self, course_content: str) -> str:
        """Generate a concise course summary"""
        prompt = f"""Create a concise, engaging 2-3 paragraph summary of this course:

{course_content}"""

        return await self.generate_text(prompt=prompt, max_tokens=300)

    async def check_content_quality(self, content: str) -> Dict:
        """Analyze content quality and provide suggestions"""
        system_message = """You are an educational content quality analyst. Analyze the content and provide:
1. Quality score (1-10)
2. Strengths (bullet points)
3. Areas for improvement (bullet points)
4. Suggestions

Return as JSON."""

        prompt = f"""Analyze this educational content:

{content}"""

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=1000
        )

        import json

        return json.loads(response)

    async def grade_essay(self, essay: str, rubric: str, max_score: int = 100) -> Dict:
        """
        Grade an essay using AI

        Returns:
            {
                "score": int,
                "feedback": str,
                "strengths": [str],
                "improvements": [str]
            }
        """
        system_message = f"""You are an expert essay grader. Grade the essay based on the rubric.
Maximum score: {max_score}
Return JSON with: score, feedback, strengths (array), improvements (array)"""

        prompt = f"""Rubric:
{rubric}

Essay to grade:
{essay}"""

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=1500
        )

        import json

        return json.loads(response)

    async def chat_with_tutor(
        self, message: str, history: List[Dict[str, str]], context: Optional[str] = None
    ) -> str:
        """
        Interactive chat with AI tutor

        Args:
            message: Current user message
            history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            context: Optional context (current course, lesson, etc.)
        """
        system_message = """You are an encouraging and knowledgeable AI tutor. 
        Help the student understand concepts by guiding them rather than just giving answers.
        Use Socratic questioning when appropriate.
        Keep responses concise and easy to understand.
        """

        if context:
            system_message += f"\nContext: {context}"

        messages = [{"role": "system", "content": system_message}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # Use _generate_openai directly to handle full message history
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def explain_concept(
        self, concept: str, level: str = "beginner", context: Optional[str] = None
    ) -> Dict:
        """
        Explain a concept with examples
        """
        system_message = f"""You are an expert teacher. Explain the concept for a {level} level student.
        Return JSON with:
        - explanation: Clear explanation
        - analogy: A helpful analogy
        - examples: List of 2-3 examples
        - key_points: List of key takeaways
        """

        prompt = f"Explain this concept: {concept}"
        if context:
            prompt += f"\nContext: {context}"

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=1500
        )

        import json

        return json.loads(response)

    async def generate_practice_problems(
        self, topic: str, difficulty: str = "medium", count: int = 3
    ) -> List[Dict]:
        """
        Generate practice problems with solutions
        """
        system_message = """Generate practice problems. Return JSON array where each item has:
        - problem: The problem text
        - type: 'multiple_choice' or 'code' or 'open'
        - options: Array of options (if multiple_choice)
        - solution: The correct answer/code
        - explanation: Step-by-step explanation
        """

        prompt = f"Generate {count} {difficulty} practice problems for: {topic}"

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=2000
        )

        import json

        return json.loads(response)

    async def review_code(self, code: str, language: str = "python") -> Dict:
        """
        Review code and provide feedback
        """
        system_message = """You are a senior software engineer. Review the code for:
        1. Bugs/Errors
        2. Best practices
        3. Performance improvements
        4. Readability
        
        Return JSON with:
        - summary: Overall feedback
        - issues: List of specific issues found
        - suggestions: List of improvement suggestions
        - refactored_code: The improved code snippet
        """

        prompt = f"Review this {language} code:\n\n{code}"

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=2000
        )

        import json

        return json.loads(response)

    async def create_study_plan(
        self, goal: str, duration: str, hours_per_week: int, current_knowledge: str
    ) -> Dict:
        """
        Create a personalized study plan
        """
        system_message = """Create a detailed study plan. Return JSON with:
        - overview: Plan summary
        - schedule: Array of weeks/modules, each containing topics and activities
        - resources: Recommended resources
        - tips: Study tips
        """

        prompt = f"""Create a study plan for:
        Goal: {goal}
        Duration: {duration}
        Time available: {hours_per_week} hours/week
        Current level: {current_knowledge}"""

        response = await self.generate_text(
            prompt=prompt, system_message=system_message, max_tokens=2000
        )

        import json

        return json.loads(response)


# Global AI service instance
ai_service = AIService()
