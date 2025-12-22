"""
Video Transcription Service
Transcribes uploaded videos and generates structured reference documents
Uses: Local Whisper for transcription + OpenRouter LLM for document generation
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import tempfile

# Paths
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRANSCRIPTS_DIR = os.path.join(BACKEND_ROOT, "data", "transcripts")
DOCUMENTS_DIR = os.path.join(BACKEND_ROOT, "data", "video_documents")

# Ensure directories exist
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

print(f"[TranscriptionService] Transcripts dir: {TRANSCRIPTS_DIR}")
print(f"[TranscriptionService] Documents dir: {DOCUMENTS_DIR}")


async def extract_audio(video_path: str, output_audio_path: str) -> bool:
    """Extract audio from video using ffmpeg"""
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM format
            "-ar", "16000",  # 16kHz sample rate (Whisper optimal)
            "-ac", "1",  # Mono
            "-y",  # Overwrite
            output_audio_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        return os.path.exists(output_audio_path)
    except Exception as e:
        print(f"[TranscriptionService] Audio extraction error: {e}")
        return False


async def transcribe_with_whisper(audio_path: str) -> Optional[str]:
    """Transcribe audio using OpenAI Whisper (requires whisper installed)"""
    try:
        # Try using whisper CLI if installed
        cmd = [
            "whisper", audio_path,
            "--model", "base",  # Use base model for speed
            "--language", "en",
            "--output_format", "txt",
            "--output_dir", tempfile.gettempdir()
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        # Read the output file
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        txt_file = os.path.join(tempfile.gettempdir(), f"{base_name}.txt")
        
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                transcript = f.read()
            os.remove(txt_file)  # Cleanup
            return transcript
        else:
            print(f"[TranscriptionService] Whisper output not found")
            return None
            
    except FileNotFoundError:
        print("[TranscriptionService] Whisper not installed. Using fallback method.")
        return None
    except Exception as e:
        print(f"[TranscriptionService] Whisper error: {e}")
        return None


async def generate_document_from_transcript(
    transcript: str,
    segment_title: str,
    ai_router
) -> Dict[str, Any]:
    """Use OpenRouter LLM to generate structured document from transcript"""
    
    system_message = """You are a content analyzer for educational videos.
Convert the video transcript into a structured document.

RESPOND WITH ONLY JSON - NO OTHER TEXT.

Extract and organize:
1. Main topics covered (with timestamps if visible)
2. Key facts and dates mentioned
3. Examples and case studies used
4. Stories or anecdotes told
5. Important definitions
6. Key concepts to remember

JSON FORMAT:
{
  "title": "Video segment title",
  "duration_covered": "approximate duration",
  "main_topics": [
    {"topic": "Topic name", "summary": "Brief summary", "importance": "high/medium/low"}
  ],
  "key_facts": [
    {"fact": "Specific fact", "context": "When/why mentioned"}
  ],
  "dates_and_events": [
    {"date": "Date/year", "event": "What happened"}
  ],
  "examples_used": [
    {"example": "Description", "purpose": "Why it was used"}
  ],
  "definitions": [
    {"term": "Term", "definition": "Definition given"}
  ],
  "key_concepts": ["Concept 1", "Concept 2"],
  "summary": "A comprehensive 3-4 sentence summary of the entire segment",
  "key_points_for_recall": [
    "Point 1 student should remember",
    "Point 2 student should remember",
    "Point 3 student should remember"
  ]
}"""

    prompt = f"""Analyze this video transcript and create a structured document.

VIDEO TITLE: {segment_title}

TRANSCRIPT:
---
{transcript}
---

Create the structured JSON document now:"""

    try:
        # Import TaskType for the router
        from app.services.ai_router import TaskType
        
        result = await ai_router.route(
            prompt=prompt,
            system_message=system_message,
            max_tokens=2000,
            temperature=0.3,
            task_type_override=TaskType.ANALYSIS
        )
        
        content = result.get("content", "{}")
        
        # Try to parse JSON
        import re
        
        # Clean markdown
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        if clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        
        document = json.loads(clean_content.strip())
        document["generated_at"] = datetime.utcnow().isoformat()
        document["ai_model"] = result.get("model", "unknown")
        
        return document
        
    except Exception as e:
        print(f"[TranscriptionService] Document generation error: {e}")
        return {
            "title": segment_title,
            "error": str(e),
            "key_points_for_recall": [
                f"Content from {segment_title}",
                "Review the video for detailed information"
            ]
        }


async def process_video_transcription(
    video_path: str,
    segment_key: str,
    segment_title: str
) -> Dict[str, Any]:
    """
    Full pipeline: Video -> Audio -> Transcript -> Document
    """
    print(f"[TranscriptionService] Starting transcription for: {segment_key}")
    
    result = {
        "segment_key": segment_key,
        "status": "processing",
        "transcript": None,
        "document": None,
        "error": None
    }
    
    try:
        # Step 1: Extract audio
        audio_path = os.path.join(tempfile.gettempdir(), f"{segment_key}.wav")
        
        print(f"[TranscriptionService] Extracting audio...")
        audio_extracted = await extract_audio(video_path, audio_path)
        
        if not audio_extracted:
            # If ffmpeg fails, try to work with video directly
            print("[TranscriptionService] Audio extraction failed, using video directly")
            audio_path = video_path
        
        # Step 2: Transcribe
        print(f"[TranscriptionService] Transcribing with Whisper...")
        transcript = await transcribe_with_whisper(audio_path)
        
        if not transcript:
            # Fallback: Use placeholder transcript based on title
            print("[TranscriptionService] Whisper not available, using placeholder")
            transcript = f"""[Automatic transcription not available for this video]
Video Topic: {segment_title}

This video covers the topic of {segment_title}. 
The teacher explains the key concepts, provides examples, and discusses relevant facts.
Students should pay attention to the main points and take notes for recall.

[End of placeholder transcript]"""
        
        # Save transcript
        transcript_file = os.path.join(TRANSCRIPTS_DIR, f"{segment_key}.txt")
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        result["transcript"] = transcript
        print(f"[TranscriptionService] Transcript saved: {transcript_file}")
        
        # Step 3: Generate structured document using AI
        print(f"[TranscriptionService] Generating document with AI...")
        
        # Import AI router
        from app.services.ai_router import AIRouter
        ai_router = AIRouter()
        
        document = await generate_document_from_transcript(
            transcript=transcript,
            segment_title=segment_title,
            ai_router=ai_router
        )
        
        # Save document
        document_file = os.path.join(DOCUMENTS_DIR, f"{segment_key}.json")
        with open(document_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
        
        result["document"] = document
        result["status"] = "completed"
        print(f"[TranscriptionService] Document saved: {document_file}")
        
        # Cleanup temp audio
        if os.path.exists(audio_path) and audio_path.endswith('.wav'):
            os.remove(audio_path)
        
        return result
        
    except Exception as e:
        print(f"[TranscriptionService] Error: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        return result


def get_video_document(segment_key: str) -> Optional[Dict[str, Any]]:
    """Get the generated document for a video segment"""
    document_file = os.path.join(DOCUMENTS_DIR, f"{segment_key}.json")
    
    if os.path.exists(document_file):
        try:
            with open(document_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[TranscriptionService] Error loading document: {e}")
    
    return None


def get_key_points_from_document(segment_key: str) -> str:
    """Get formatted key points for recall analysis"""
    document = get_video_document(segment_key)
    
    if not document:
        return ""
    
    key_points = []
    
    # Add key concepts
    if "key_concepts" in document:
        key_points.extend(document["key_concepts"])
    
    # Add key facts
    if "key_facts" in document:
        for fact in document["key_facts"]:
            key_points.append(fact.get("fact", ""))
    
    # Add recall points
    if "key_points_for_recall" in document:
        key_points.extend(document["key_points_for_recall"])
    
    # Add main topics
    if "main_topics" in document:
        for topic in document["main_topics"]:
            key_points.append(f"{topic.get('topic', '')}: {topic.get('summary', '')}")
    
    return "\n".join([f"- {kp}" for kp in key_points if kp])


def get_transcription_status(segment_key: str) -> Dict[str, Any]:
    """Check transcription status for a segment"""
    transcript_file = os.path.join(TRANSCRIPTS_DIR, f"{segment_key}.txt")
    document_file = os.path.join(DOCUMENTS_DIR, f"{segment_key}.json")
    
    return {
        "segment_key": segment_key,
        "has_transcript": os.path.exists(transcript_file),
        "has_document": os.path.exists(document_file),
        "transcript_path": transcript_file if os.path.exists(transcript_file) else None,
        "document_path": document_file if os.path.exists(document_file) else None
    }
