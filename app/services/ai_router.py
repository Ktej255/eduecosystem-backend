"""
AI Task Router Service
Implements smart routing to select the most cost-effective model for each task.

Architecture:
    User Request → Task Classifier → Model Selector → AI API

Models:
    - Gemini Flash: MCQs, short answers (cheapest)
    - Llama 3: Teaching, explanations (free tier)
    - Gemini Pro: Essays, complex reasoning (premium)
"""

import re
import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import openai
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of educational tasks"""
    MCQ = "mcq"                    # Multiple choice questions
    SHORT_ANSWER = "short_answer"  # Brief factual responses
    EXPLANATION = "explanation"    # Teaching/explaining concepts
    ESSAY = "essay"                # Essay grading/evaluation
    RECALL = "recall"              # Recall analysis (like prelims)
    DOCUMENT = "document"          # Large document analysis
    GENERAL = "general"            # General queries


class ModelConfig(BaseModel):
    """Configuration for an AI model"""
    name: str                      # Model ID for API
    provider: str                  # openrouter, openai, etc.
    api_key: str
    base_url: str
    cost_per_1k_input: float      # Cost in USD
    cost_per_1k_output: float
    max_context: int              # Max tokens


# Model registry with costs (approximate for OpenRouter)
MODEL_REGISTRY = {
    "gemini-flash": ModelConfig(
        name="google/gemini-2.0-flash-exp:free",
        provider="openrouter",
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        cost_per_1k_input=0.0,    # Free tier
        cost_per_1k_output=0.0,
        max_context=32000
    ),
    "llama-3": ModelConfig(
        name="meta-llama/llama-3.3-70b-instruct:free",
        provider="openrouter",
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        cost_per_1k_input=0.0,    # Free tier
        cost_per_1k_output=0.0,
        max_context=131072
    ),
    "gemma-3": ModelConfig(
        name="google/gemma-3-27b-it",
        provider="openrouter",
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0002,
        max_context=128000
    ),
}

# Task type to model mapping (cost optimization)
TASK_MODEL_MAP = {
    TaskType.MCQ: "gemini-flash",           # Cheapest for simple tasks
    TaskType.SHORT_ANSWER: "gemini-flash",  # Enough for brief responses
    TaskType.EXPLANATION: "llama-3",        # Good for teaching
    TaskType.ESSAY: "gemma-3",              # Strong reasoning
    TaskType.RECALL: "llama-3",             # Llama 3 for recall (larger context, free)
    TaskType.DOCUMENT: "llama-3",           # Long context
    TaskType.GENERAL: "llama-3",            # Default to Llama 3 (more stable free tier)
}


class TokenUsage(BaseModel):
    """Token usage tracking"""
    model: str
    task_type: TaskType
    input_tokens: int
    output_tokens: int
    total_cost: float
    timestamp: datetime


class AIRouter:
    """
    Smart AI task router that:
    1. Classifies incoming tasks
    2. Selects optimal model based on task type
    3. Routes to appropriate model
    4. Tracks token usage
    """
    
    def __init__(self):
        self.usage_log: list[TokenUsage] = []
    
    def classify_task(self, prompt: str, system_message: Optional[str] = None) -> TaskType:
        """
        Rule-based task classification (fast & free)
        Uses hybrid approach: rules first, then LLM fallback if uncertain
        """
        text = f"{system_message or ''} {prompt}".lower()
        input_length = len(prompt)
        
        # Rule 1: MCQ detection
        mcq_patterns = [
            r'\b(a\)|b\)|c\)|d\))',
            r'\boption\s*[a-d]\b',
            r'\bchoose\s*(the\s*)?(correct|right|best)\b',
            r'\bmultiple\s*choice\b',
            r'\bwhich\s*(of\s*the\s*following|one)\b',
        ]
        for pattern in mcq_patterns:
            if re.search(pattern, text):
                logger.info("Task classified as MCQ via rules")
                return TaskType.MCQ
        
        # Rule 2: Short answer detection
        if input_length < 500 and any(word in text for word in ['define', 'what is', 'name ', 'list ']):
            logger.info("Task classified as SHORT_ANSWER via rules")
            return TaskType.SHORT_ANSWER
        
        # Rule 3: Recall/evaluation detection
        recall_patterns = [
            r'\brecall\b',
            r'\bevaluate\b',
            r'\banalyz[es]\b',
            r'\bkey\s*points\b',
            r'\bsegment\b',
            r'\bvideo\b',
        ]
        matches = sum(1 for p in recall_patterns if re.search(p, text))
        if matches >= 2:
            logger.info("Task classified as RECALL via rules")
            return TaskType.RECALL
        
        # Rule 4: Essay/long-form detection
        if input_length > 2000 or any(word in text for word in ['essay', 'critically analyze', 'discuss in detail']):
            logger.info("Task classified as ESSAY via rules")
            return TaskType.ESSAY
        
        # Rule 5: Teaching/explanation detection
        if any(word in text for word in ['explain', 'teach', 'help understand', 'concept']):
            logger.info("Task classified as EXPLANATION via rules")
            return TaskType.EXPLANATION
        
        # Rule 6: Document analysis
        if input_length > 5000:
            logger.info("Task classified as DOCUMENT via rules")
            return TaskType.DOCUMENT
        
        # Default: general task
        logger.info("Task classified as GENERAL (default)")
        return TaskType.GENERAL
    
    def select_model(self, task_type: TaskType, force_model: Optional[str] = None) -> ModelConfig:
        """Select the optimal model for the task type"""
        if force_model and force_model in MODEL_REGISTRY:
            return MODEL_REGISTRY[force_model]
        
        model_key = TASK_MODEL_MAP.get(task_type, "gemini-flash")
        return MODEL_REGISTRY[model_key]
    
    async def route(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
        force_model: Optional[str] = None,
        task_type_override: Optional[TaskType] = None
    ) -> Dict[str, Any]:
        """
        Main routing function with fallback:
        1. Classify the task
        2. Try primary model
        3. If fails, try all other models as fallback
        4. Track usage
        5. Return response with metadata
        """
        # Step 1: Classify task
        task_type = task_type_override or self.classify_task(prompt, system_message)
        
        # Get primary model and create fallback order
        primary_model_key = force_model if force_model in MODEL_REGISTRY else TASK_MODEL_MAP.get(task_type, "llama-3")
        
        # Fallback order: primary model first, then others
        fallback_order = [primary_model_key] + [k for k in ["llama-3", "gemini-flash", "gemma-3"] if k != primary_model_key]
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        
        # Try each model in order
        for model_key in fallback_order:
            model_config = MODEL_REGISTRY[model_key]
            
            print(f"[AI Router] Trying model: {model_config.name}")
            print(f"[AI Router] Provider: {model_config.provider}, URL: {model_config.base_url}")
            
            try:
                client = openai.AsyncOpenAI(
                    api_key=model_config.api_key,
                    base_url=model_config.base_url,
                )
                
                response = await client.chat.completions.create(
                    model=model_config.name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    extra_headers={
                        "HTTP-Referer": "https://eduecosystem.com",
                        "X-Title": "Holistic Learning Ecosystem",
                    }
                )
                
                print(f"[AI Router] SUCCESS with {model_config.name}")
                
                # Calculate and track usage
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                total_cost = (
                    (input_tokens / 1000) * model_config.cost_per_1k_input +
                    (output_tokens / 1000) * model_config.cost_per_1k_output
                )
                
                usage = TokenUsage(
                    model=model_config.name,
                    task_type=task_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_cost=total_cost,
                    timestamp=datetime.utcnow()
                )
                self.usage_log.append(usage)
                
                logger.info(f"Request complete: model={model_key}, tokens={input_tokens}+{output_tokens}")
                
                return {
                    "content": response.choices[0].message.content,
                    "model": model_config.name,
                    "provider": model_config.provider,
                    "task_type": task_type.value,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": total_cost,
                }
                
            except Exception as e:
                print(f"[AI Router] FAILED {model_config.name}: {type(e).__name__}: {str(e)[:200]}")
                last_error = e
                continue  # Try next model
        
        # All models failed
        print(f"[AI Router] ALL MODELS FAILED! Last error: {last_error}")
        raise last_error or Exception("All AI models failed")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of token usage and costs"""
        if not self.usage_log:
            return {"total_requests": 0, "total_cost": 0}
        
        by_model: Dict[str, Dict] = {}
        for usage in self.usage_log:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0
                }
            by_model[usage.model]["requests"] += 1
            by_model[usage.model]["input_tokens"] += usage.input_tokens
            by_model[usage.model]["output_tokens"] += usage.output_tokens
            by_model[usage.model]["cost"] += usage.total_cost
        
        return {
            "total_requests": len(self.usage_log),
            "total_cost": sum(u.total_cost for u in self.usage_log),
            "by_model": by_model,
            "by_task_type": self._group_by_task_type()
        }
    
    def _group_by_task_type(self) -> Dict[str, Dict]:
        """Group usage by task type"""
        by_type: Dict[str, Dict] = {}
        for usage in self.usage_log:
            key = usage.task_type.value
            if key not in by_type:
                by_type[key] = {"requests": 0, "cost": 0}
            by_type[key]["requests"] += 1
            by_type[key]["cost"] += usage.total_cost
        return by_type


# Global router instance
ai_router = AIRouter()
