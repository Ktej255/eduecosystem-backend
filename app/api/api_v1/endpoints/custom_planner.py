"""
Custom Study Planner API - Dynamic RAS Study Planner
Personalized for specific email IDs with adaptive daily scheduling
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

router = APIRouter()

# Authorized email for custom planner
AUTHORIZED_EMAILS = ["chitrakumawat33@gmail.com"]

# RAS Syllabus Structure with Topics
RAS_SYLLABUS = {
    "math": {
        "name": "Mathematics",
        "priority": "high",
        "topics": [
            {"id": "math_1", "name": "Number System", "subtopics": ["Types of Numbers", "Divisibility", "Remainders"]},
            {"id": "math_2", "name": "LCM & HCF", "subtopics": ["Finding LCM/HCF", "Word Problems"]},
            {"id": "math_3", "name": "Percentages", "subtopics": ["Basic Concepts", "Successive Change", "Applications"]},
            {"id": "math_4", "name": "Ratio & Proportion", "subtopics": ["Ratios", "Proportions", "Mixtures"]},
            {"id": "math_5", "name": "Profit & Loss", "subtopics": ["Basic P&L", "Discount", "Marked Price"]},
            {"id": "math_6", "name": "Simple & Compound Interest", "subtopics": ["SI", "CI", "Difference formulae"]},
            {"id": "math_7", "name": "Time & Work", "subtopics": ["Work Efficiency", "Pipes & Cisterns"]},
            {"id": "math_8", "name": "Time, Speed & Distance", "subtopics": ["Basics", "Relative Speed", "Trains"]},
            {"id": "math_9", "name": "Averages", "subtopics": ["Weighted Average", "Age Problems"]},
            {"id": "math_10", "name": "Data Interpretation", "subtopics": ["Tables", "Charts", "Graphs"]},
        ]
    },
    "medieval_history": {
        "name": "Medieval History",
        "priority": "high",
        "topics": [
            {"id": "med_1", "name": "Delhi Sultanate", "subtopics": ["Slave Dynasty", "Khilji Dynasty", "Tughlaq Dynasty"]},
            {"id": "med_2", "name": "Vijayanagara Empire", "subtopics": ["Founders", "Administration", "Culture"]},
            {"id": "med_3", "name": "Mughal Empire", "subtopics": ["Babur", "Akbar", "Aurangzeb"]},
            {"id": "med_4", "name": "Bhakti Movement", "subtopics": ["Saints", "Philosophy", "Impact"]},
            {"id": "med_5", "name": "Sufi Movement", "subtopics": ["Orders", "Teachings", "Influence"]},
            {"id": "med_6", "name": "Regional Kingdoms", "subtopics": ["Rajputs", "Marathas", "Sikhs"]},
            {"id": "med_7", "name": "Art & Architecture", "subtopics": ["Indo-Islamic", "Mughal Art", "Temples"]},
            {"id": "med_8", "name": "Economy & Trade", "subtopics": ["Trade Routes", "Currency", "Agriculture"]},
        ]
    },
    "polity": {
        "name": "Indian Polity",
        "priority": "medium",
        "topics": [
            {"id": "pol_1", "name": "Historical Background", "subtopics": ["Acts before 1947", "Constituent Assembly"]},
            {"id": "pol_2", "name": "Preamble", "subtopics": ["Keywords", "Amendments", "Cases"]},
            {"id": "pol_3", "name": "Fundamental Rights", "subtopics": ["Art 14-18", "Art 19-22", "Art 23-35"]},
            {"id": "pol_4", "name": "DPSP", "subtopics": ["Classification", "Amendments", "Implementation"]},
            {"id": "pol_5", "name": "Fundamental Duties", "subtopics": ["Art 51A", "Importance"]},
            {"id": "pol_6", "name": "Union Executive", "subtopics": ["President", "PM & Council", "CAG"]},
            {"id": "pol_7", "name": "Parliament", "subtopics": ["Lok Sabha", "Rajya Sabha", "Sessions"]},
            {"id": "pol_8", "name": "Judiciary", "subtopics": ["Supreme Court", "High Courts", "PIL"]},
            {"id": "pol_9", "name": "State Government", "subtopics": ["Governor", "CM", "State Legislature"]},
            {"id": "pol_10", "name": "Local Government", "subtopics": ["73rd Amendment", "74th Amendment"]},
        ]
    },
    "modern_history": {
        "name": "Modern History",
        "priority": "medium",
        "topics": [
            {"id": "mod_1", "name": "British Expansion", "subtopics": ["Battles", "Policies", "Annexations"]},
            {"id": "mod_2", "name": "1857 Revolt", "subtopics": ["Causes", "Leaders", "Aftermath"]},
            {"id": "mod_3", "name": "Social Reform Movements", "subtopics": ["Raja Ram Mohan Roy", "Dayanand Saraswati"]},
            {"id": "mod_4", "name": "Early Nationalism", "subtopics": ["INC Formation", "Moderates", "Extremists"]},
            {"id": "mod_5", "name": "Gandhi Era", "subtopics": ["NCM", "CDM", "QIM"]},
            {"id": "mod_6", "name": "Revolutionary Movement", "subtopics": ["Bhagat Singh", "Subhas Bose"]},
            {"id": "mod_7", "name": "Partition & Independence", "subtopics": ["Mountbatten Plan", "Integration"]},
        ]
    },
    "geography": {
        "name": "Geography",
        "priority": "medium",
        "topics": [
            {"id": "geo_1", "name": "Physical Geography", "subtopics": ["Geomorphology", "Climatology"]},
            {"id": "geo_2", "name": "Indian Geography", "subtopics": ["Physiographic Divisions", "Rivers"]},
            {"id": "geo_3", "name": "Climate of India", "subtopics": ["Monsoon", "Seasons"]},
            {"id": "geo_4", "name": "Natural Resources", "subtopics": ["Minerals", "Energy"]},
            {"id": "geo_5", "name": "Agriculture", "subtopics": ["Crops", "Irrigation", "Green Revolution"]},
            {"id": "geo_6", "name": "Industries", "subtopics": ["Types", "Industrial Regions"]},
            {"id": "geo_7", "name": "Rajasthan Geography", "subtopics": ["Physical", "Climate", "Resources"]},
        ]
    },
    "economy": {
        "name": "Indian Economy",
        "priority": "medium",
        "topics": [
            {"id": "eco_1", "name": "Economic Planning", "subtopics": ["Five Year Plans", "NITI Aayog"]},
            {"id": "eco_2", "name": "Agriculture Sector", "subtopics": ["Policies", "MSP", "Reforms"]},
            {"id": "eco_3", "name": "Industrial Sector", "subtopics": ["Policies", "Make in India"]},
            {"id": "eco_4", "name": "Banking & Finance", "subtopics": ["RBI", "Banks", "NBFCs"]},
            {"id": "eco_5", "name": "Fiscal Policy", "subtopics": ["Budget", "Taxation", "Deficit"]},
            {"id": "eco_6", "name": "External Sector", "subtopics": ["Trade", "BOP", "FDI/FPI"]},
        ]
    },
    "science_tech": {
        "name": "Science & Technology",
        "priority": "low",
        "topics": [
            {"id": "sci_1", "name": "Space Technology", "subtopics": ["ISRO", "Satellites", "Missions"]},
            {"id": "sci_2", "name": "Defence Technology", "subtopics": ["Missiles", "Aircraft", "Ships"]},
            {"id": "sci_3", "name": "Biotechnology", "subtopics": ["DNA", "Genetic Engineering"]},
            {"id": "sci_4", "name": "IT & Communications", "subtopics": ["Digital India", "5G"]},
            {"id": "sci_5", "name": "Energy Technology", "subtopics": ["Nuclear", "Solar", "Wind"]},
        ]
    },
    "environment": {
        "name": "Environment & Ecology",
        "priority": "low",
        "topics": [
            {"id": "env_1", "name": "Ecology Basics", "subtopics": ["Ecosystems", "Food Chain"]},
            {"id": "env_2", "name": "Biodiversity", "subtopics": ["Types", "Hotspots", "Conservation"]},
            {"id": "env_3", "name": "Pollution", "subtopics": ["Air", "Water", "Soil"]},
            {"id": "env_4", "name": "Climate Change", "subtopics": ["Global Warming", "Agreements"]},
            {"id": "env_5", "name": "Environmental Laws", "subtopics": ["Acts", "Tribunals"]},
        ]
    },
    "rajasthan_gk": {
        "name": "Rajasthan GK",
        "priority": "high",
        "topics": [
            {"id": "raj_1", "name": "Rajasthan History", "subtopics": ["Ancient", "Medieval", "Modern"]},
            {"id": "raj_2", "name": "Geography of Rajasthan", "subtopics": ["Physical", "Climate", "Rivers"]},
            {"id": "raj_3", "name": "Art & Culture", "subtopics": ["Fairs", "Festivals", "Folk Art"]},
            {"id": "raj_4", "name": "Economy of Rajasthan", "subtopics": ["Agriculture", "Industries", "Schemes"]},
            {"id": "raj_5", "name": "Current Affairs Rajasthan", "subtopics": ["Government Schemes", "Events"]},
        ]
    }
}

# Sample PYQs for topics
SAMPLE_PYQS = {
    "math_1": [
        {"year": 2023, "type": "prelims", "question": "The sum of two numbers is 45 and their difference is 9. Find the numbers.", "answer": "27 and 18"},
        {"year": 2022, "type": "prelims", "question": "If a number is divisible by both 3 and 5, it is also divisible by:", "answer": "15"},
    ],
    "pol_2": [
        {"year": 2023, "type": "prelims", "question": "The word 'Socialist' was added to the Preamble by which amendment?", "answer": "42nd Amendment (1976)"},
        {"year": 2022, "type": "mains", "question": "Discuss the significance of the Preamble in interpreting the Constitution.", "answer": "Essay type"},
    ],
    "med_1": [
        {"year": 2021, "type": "prelims", "question": "Who founded the Delhi Sultanate?", "answer": "Qutub-ud-din Aibak"},
        {"year": 2020, "type": "prelims", "question": "The Tughlaq dynasty was founded by:", "answer": "Ghiyasuddin Tughlaq"},
    ],
}

# In-memory storage for plans (replace with database in production)
_user_plans: Dict[str, Dict] = {}
_topic_progress: Dict[str, Dict[str, Any]] = {}


class TopicUpdate(BaseModel):
    email: str
    topic_id: str
    completed: bool


class PlanRequest(BaseModel):
    email: str


@router.get("/check-access/{email}")
async def check_access(email: str):
    """Check if email has access to custom planner."""
    return {
        "has_access": email.lower() in [e.lower() for e in AUTHORIZED_EMAILS],
        "email": email
    }


@router.get("/syllabus")
async def get_syllabus():
    """Get complete RAS syllabus structure."""
    return {
        "subjects": RAS_SYLLABUS,
        "total_subjects": len(RAS_SYLLABUS),
        "total_topics": sum(len(s["topics"]) for s in RAS_SYLLABUS.values())
    }


@router.get("/dashboard/{email}")
async def get_dashboard(email: str):
    """Get complete dashboard data for the email."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate progress per subject
    subject_progress = {}
    total_topics = 0
    completed_topics = 0
    
    for subject_key, subject_data in RAS_SYLLABUS.items():
        topics = subject_data["topics"]
        subject_completed = 0
        
        for topic in topics:
            topic_key = f"{email}_{topic['id']}"
            if _topic_progress.get(topic_key, {}).get("completed", False):
                subject_completed += 1
                completed_topics += 1
            total_topics += 1
        
        subject_progress[subject_key] = {
            "name": subject_data["name"],
            "priority": subject_data["priority"],
            "total_topics": len(topics),
            "completed_topics": subject_completed,
            "percentage": round((subject_completed / len(topics)) * 100) if topics else 0
        }
    
    overall_percentage = round((completed_topics / total_topics) * 100) if total_topics else 0
    
    return {
        "email": email,
        "overall_progress": {
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "percentage": overall_percentage
        },
        "subject_progress": subject_progress,
        "schedule": {
            "start_time": "13:30",
            "end_time": "20:30",
            "daily_hours": 7
        }
    }


@router.get("/today/{email}")
async def get_today_plan(email: str):
    """Get today's dynamic study plan."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = date.today().isoformat()
    
    # Get or generate today's plan
    plan_key = f"{email}_{today}"
    
    if plan_key in _user_plans:
        return _user_plans[plan_key]
    
    # Generate new plan - prioritize incomplete topics from high priority subjects
    plan_topics = []
    slots = [
        {"time": "13:30 - 15:00", "type": "new_topic", "duration": 90},
        {"time": "15:00 - 16:30", "type": "new_topic", "duration": 90},
        {"time": "17:00 - 18:00", "type": "revision", "duration": 60},
        {"time": "18:00 - 19:00", "type": "pyq_practice", "duration": 60},
        {"time": "19:00 - 20:00", "type": "weak_areas", "duration": 60},
        {"time": "20:00 - 20:30", "type": "summary", "duration": 30},
    ]
    
    # Collect incomplete topics ordered by priority
    incomplete_topics = []
    for subject_key, subject_data in RAS_SYLLABUS.items():
        priority_order = {"high": 0, "medium": 1, "low": 2}
        for topic in subject_data["topics"]:
            topic_key = f"{email}_{topic['id']}"
            if not _topic_progress.get(topic_key, {}).get("completed", False):
                incomplete_topics.append({
                    **topic,
                    "subject": subject_data["name"],
                    "subject_key": subject_key,
                    "priority": subject_data["priority"],
                    "priority_order": priority_order.get(subject_data["priority"], 2)
                })
    
    # Sort by priority
    incomplete_topics.sort(key=lambda x: x["priority_order"])
    
    # Assign topics to slots
    topic_idx = 0
    for slot in slots:
        if slot["type"] == "new_topic" and topic_idx < len(incomplete_topics):
            slot["topic"] = incomplete_topics[topic_idx]
            slot["pyqs"] = SAMPLE_PYQS.get(incomplete_topics[topic_idx]["id"], [])
            topic_idx += 1
        elif slot["type"] == "revision":
            # Get recently completed topics for revision
            slot["description"] = "Revise topics from previous days"
        elif slot["type"] == "pyq_practice":
            slot["description"] = "Practice PYQs related to today's topics"
        elif slot["type"] == "weak_areas":
            slot["description"] = "Focus on subjects with lowest completion"
        elif slot["type"] == "summary":
            slot["description"] = "Daily summary and plan tomorrow"
    
    plan = {
        "email": email,
        "date": today,
        "slots": slots,
        "total_new_topics": min(2, len(incomplete_topics)),
        "remaining_topics": len(incomplete_topics)
    }
    
    _user_plans[plan_key] = plan
    return plan


@router.post("/update-progress")
async def update_topic_progress(update: TopicUpdate):
    """Update topic completion status."""
    if update.email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    topic_key = f"{update.email}_{update.topic_id}"
    _topic_progress[topic_key] = {
        "completed": update.completed,
        "completed_at": datetime.now().isoformat() if update.completed else None
    }
    
    return {
        "success": True,
        "topic_id": update.topic_id,
        "completed": update.completed
    }


@router.get("/pyq/{topic_id}")
async def get_pyqs(topic_id: str):
    """Get PYQs for a specific topic."""
    pyqs = SAMPLE_PYQS.get(topic_id, [])
    return {
        "topic_id": topic_id,
        "pyqs": pyqs,
        "count": len(pyqs)
    }


@router.post("/reset-progress/{email}")
async def reset_progress(email: str):
    """Reset all progress for an email (for testing)."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Clear progress
    keys_to_delete = [k for k in _topic_progress.keys() if k.startswith(email)]
    for key in keys_to_delete:
        del _topic_progress[key]
    
    # Clear plans
    keys_to_delete = [k for k in _user_plans.keys() if k.startswith(email)]
    for key in keys_to_delete:
        del _user_plans[key]
    
    return {"success": True, "message": "Progress reset"}
