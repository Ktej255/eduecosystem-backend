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

# RAS Syllabus Structure with Topics (Complete from Vijay Sir's Syllabus)
RAS_SYLLABUS = {
    "rajasthan_geography": {
        "name": "Rajasthan Geography",
        "priority": "high",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "rg_1", "name": "Basic Geography: Origin of Rajasthan", "subtopics": ["Formation", "Historical Evolution", "Geographic Setting"], "exam": "pre_mains"},
            {"id": "rg_2", "name": "Location & Extension", "subtopics": ["Latitude & Longitude", "Boundaries", "Area"], "exam": "pre_mains"},
            {"id": "rg_3", "name": "Physical Divisions", "subtopics": ["Aravalli Range", "Eastern Plains", "Western Desert", "Hadoti Plateau"], "exam": "pre_mains"},
            {"id": "rg_4", "name": "Hydro Geography / Drainage System", "subtopics": ["River Systems", "Salt Lakes", "Irrigation Projects"], "exam": "pre_mains"},
            {"id": "rg_5", "name": "Salt Lakes", "subtopics": ["Sambhar", "Didwana", "Pachpadra", "Lunkaransar"], "exam": "mains"},
            {"id": "rg_6", "name": "Irrigation Projects", "subtopics": ["Major Dams", "Canal Systems", "Lift Irrigation"], "exam": "pre"},
            {"id": "rg_7", "name": "Water Conservation Techniques", "subtopics": ["Johad", "Khadin", "Nadi", "Talab"], "exam": "pre_mains"},
            {"id": "rg_8", "name": "IGNP (Indira Gandhi Canal Project)", "subtopics": ["History", "Stages", "Impact", "Challenges"], "exam": "pre_mains"},
            {"id": "rg_9", "name": "Soil", "subtopics": ["Types of Soil", "Distribution", "Soil Erosion"], "exam": "pre"},
            {"id": "rg_10", "name": "Minerals", "subtopics": ["Metallic", "Non-Metallic", "Distribution"], "exam": "pre_mains"},
            {"id": "rg_11", "name": "Vegetation", "subtopics": ["Forest Types", "Flora", "Conservation"], "exam": "pre_mains"},
            {"id": "rg_12", "name": "Wildlife & Biodiversity", "subtopics": ["National Parks", "Wildlife Sanctuaries", "Conservation"], "exam": "pre_mains"},
            {"id": "rg_13", "name": "Agriculture", "subtopics": ["Major Crops", "Cropping Patterns", "Agricultural Problems"], "exam": "pre_mains"},
            {"id": "rg_14", "name": "UNESCO Sites", "subtopics": ["World Heritage Sites", "Tentative List"], "exam": "pre_mains"},
            {"id": "rg_15", "name": "Industry", "subtopics": ["Industrial Areas", "Major Industries", "Industrial Policy"], "exam": "pre_mains"},
            {"id": "rg_16", "name": "Energy", "subtopics": ["Power Plants", "Renewable Energy", "Energy Policy"], "exam": "pre_mains"},
            {"id": "rg_17", "name": "Population", "subtopics": ["Census Data", "Density", "Growth Rate", "Sex Ratio"], "exam": "pre_mains"},
            {"id": "rg_18", "name": "Tourism", "subtopics": ["Tourist Circuits", "Heritage Sites", "Geo-parks", "Forts & Palaces"], "exam": "pre"},
        ]
    },
    "physics": {
        "name": "Physics",
        "priority": "medium",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "phy_1", "name": "General Information (Samanya Jankari)", "subtopics": ["Units", "Measurements", "Basic Concepts"], "exam": "pre_mains"},
            {"id": "phy_2", "name": "Gravitational Force (Gurutvakarshan Bal)", "subtopics": ["Newton's Laws", "Gravity", "Acceleration"], "exam": "pre_mains"},
            {"id": "phy_3", "name": "Heat (Ushma)", "subtopics": ["Temperature", "Thermodynamics", "Heat Transfer"], "exam": "pre_mains"},
            {"id": "phy_4", "name": "Sound & Electromagnetic Waves", "subtopics": ["Sound Properties", "Wave Types", "EM Spectrum"], "exam": "pre_mains"},
            {"id": "phy_5", "name": "Light (Prakash)", "subtopics": ["Reflection", "Refraction", "Optical Instruments"], "exam": "pre_mains"},
            {"id": "phy_6", "name": "Nuclear Fission & Fusion", "subtopics": ["Nuclear Reactions", "Applications", "Nuclear Energy"], "exam": "pre_mains"},
            {"id": "phy_7", "name": "Electrostatics & Current Electricity", "subtopics": ["Electric Charge", "Current", "Circuits"], "exam": "pre_mains"},
            {"id": "phy_8", "name": "Magnetism & Electromagnetism", "subtopics": ["Magnetic Field", "Electromagnetic Induction", "Motors"], "exam": "pre_mains"},
            {"id": "phy_9", "name": "NMR & MRI", "subtopics": ["Principles", "Medical Applications", "Imaging"], "exam": "mains"},
        ]
    },
    "reasoning": {
        "name": "Reasoning",
        "priority": "high",
        "exam_type": "pre",
        "note": "20 Questions total (Maths + Reasoning). 5 questions from CSAT.",
        "topics": [
            {"id": "rsn_1", "name": "Shapes and Sub-sections", "subtopics": ["Figure Analysis", "Pattern Recognition"], "exam": "pre"},
            {"id": "rsn_2", "name": "Problems Based on Relation", "subtopics": ["Blood Relations", "Family Tree"], "exam": "pre"},
            {"id": "rsn_3", "name": "Coding-Decoding", "subtopics": ["Letter Coding", "Number Coding", "Mixed Coding"], "exam": "pre"},
            {"id": "rsn_4", "name": "Mirror Image", "subtopics": ["Letter Mirror", "Figure Mirror"], "exam": "pre"},
            {"id": "rsn_5", "name": "Water Image", "subtopics": ["Letter Water Image", "Figure Water Image"], "exam": "pre"},
            {"id": "rsn_6", "name": "Direction Sense Test", "subtopics": ["Distance", "Direction", "Shadow"], "exam": "pre"},
            {"id": "rsn_7", "name": "Cube, Cuboid, and Dice", "subtopics": ["Cube Cutting", "Dice Problems", "3D Visualization"], "exam": "pre"},
            {"id": "rsn_8", "name": "Logical Venn Diagram", "subtopics": ["Set Theory", "Venn Diagrams"], "exam": "pre"},
            {"id": "rsn_9", "name": "Number/Alphabet Sequence", "subtopics": ["Series Completion", "Pattern Finding"], "exam": "pre"},
            {"id": "rsn_10", "name": "Sitting Arrangement", "subtopics": ["Linear", "Circular", "Complex"], "exam": "pre"},
            {"id": "rsn_11", "name": "Syllogism (Nyay Nigaman)", "subtopics": ["All/Some/No", "Conclusions"], "exam": "pre"},
            {"id": "rsn_12", "name": "Statement & Argument", "subtopics": ["Strong/Weak Arguments", "Evaluation"], "exam": "pre"},
            {"id": "rsn_13", "name": "Statement & Assumptions", "subtopics": ["Implicit Assumptions", "Logic"], "exam": "pre"},
            {"id": "rsn_14", "name": "Cause and Effect", "subtopics": ["Causal Relationships", "Analysis"], "exam": "pre"},
            {"id": "rsn_15", "name": "Statement & Conclusions", "subtopics": ["Logical Inferences", "Deductions"], "exam": "pre"},
            {"id": "rsn_16", "name": "Statement & Courses of Action", "subtopics": ["Appropriate Actions", "Decision Making"], "exam": "pre"},
        ]
    },
    "indian_economy": {
        "name": "Indian Economy",
        "priority": "high",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "eco_1", "name": "Inflation", "subtopics": ["Types", "Causes", "Effects", "Control"], "exam": "pre_mains"},
            {"id": "eco_2", "name": "Banking", "subtopics": ["RBI", "Commercial Banks", "NBFCs", "Monetary Policy"], "exam": "pre_mains"},
            {"id": "eco_3", "name": "Finance Market", "subtopics": ["Money Market", "Capital Market", "SEBI"], "exam": "pre_mains"},
            {"id": "eco_4", "name": "Fiscal Policy", "subtopics": ["Budget", "Taxation", "Deficit", "FRBM"], "exam": "pre_mains"},
            {"id": "eco_5", "name": "Unemployment", "subtopics": ["Types", "Causes", "Remedies", "Employment Schemes"], "exam": "pre_mains"},
            {"id": "eco_6", "name": "Human Development Report", "subtopics": ["HDI", "Indicators", "India's Ranking"], "exam": "pre_mains"},
            {"id": "eco_7", "name": "Trade Policy", "subtopics": ["Export-Import", "Trade Agreements", "WTO"], "exam": "pre_mains"},
            {"id": "eco_8", "name": "Global Financial Organisations", "subtopics": ["IMF", "World Bank", "ADB", "AIIB"], "exam": "pre_mains"},
            {"id": "eco_9", "name": "Agriculture Sector", "subtopics": ["Problems", "Schemes", "Reforms", "MSP"], "exam": "pre_mains"},
            {"id": "eco_10", "name": "Food Management", "subtopics": ["PDS", "Food Security", "Buffer Stock"], "exam": "pre_mains"},
            {"id": "eco_11", "name": "Food Processing", "subtopics": ["Industry", "Policies", "Investment"], "exam": "pre_mains"},
            {"id": "eco_12", "name": "Industrial Sector", "subtopics": ["Industrial Policy", "Make in India", "MSME"], "exam": "pre_mains"},
            {"id": "eco_13", "name": "E-Commerce", "subtopics": ["Growth", "Regulations", "FDI Policy"], "exam": "pre_mains"},
            {"id": "eco_14", "name": "Subsidy", "subtopics": ["Types", "Direct Benefit Transfer", "Reforms"], "exam": "pre_mains"},
            {"id": "eco_15", "name": "Public, Private, and Merit Goods", "subtopics": ["Definitions", "Examples", "Role of State"], "exam": "pre_mains"},
            {"id": "eco_16", "name": "Government Schemes", "subtopics": ["Central Schemes", "State Schemes", "Implementation"], "exam": "pre_mains"},
            {"id": "eco_17", "name": "Regulatory Effectiveness", "subtopics": ["Regulators", "Governance", "Reforms"], "exam": "pre_mains"},
            {"id": "eco_18", "name": "Role of Government in Economic Activities", "subtopics": ["Disinvestment", "PSUs", "Policy"], "exam": "pre_mains"},
        ]
    },
    "rajasthan_history": {
        "name": "Rajasthan History",
        "priority": "high",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "rh_1", "name": "History of Rajasthan - General", "subtopics": ["Overview", "Periodization", "Significance"], "exam": "pre_mains"},
            {"id": "rh_2", "name": "Sources of Ancient History", "subtopics": ["Archaeological", "Literary", "Inscriptions"], "exam": "pre_mains"},
            {"id": "rh_3", "name": "Chauhan Dynasty", "subtopics": ["Ajmer Chauhans", "Prithviraj III", "Battles"], "exam": "pre_mains"},
            {"id": "rh_4", "name": "Parmar Dynasty", "subtopics": ["Rulers", "Achievements", "Art & Architecture"], "exam": "pre_mains"},
            {"id": "rh_5", "name": "Pratihar Dynasty", "subtopics": ["Origin", "Expansion", "Decline"], "exam": "pre_mains"},
            {"id": "rh_6", "name": "Guhil / Sisodia Dynasty", "subtopics": ["Mewar", "Rana Kumbha", "Maharana Pratap"], "exam": "pre_mains"},
            {"id": "rh_7", "name": "Rathore Dynasty", "subtopics": ["Marwar", "Jodhpur", "Rao Jodha"], "exam": "pre_mains"},
            {"id": "rh_8", "name": "Kachhwaha Dynasty", "subtopics": ["Amber", "Jaipur", "Mughal Relations"], "exam": "pre_mains"},
        ]
    },
    "biology": {
        "name": "Biology",
        "priority": "medium",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "bio_1", "name": "Balanced Diet", "subtopics": ["Nutrients", "Vitamins", "Minerals"], "exam": "pre"},
            {"id": "bio_2", "name": "Blood Group", "subtopics": ["ABO System", "Rh Factor", "Blood Transfusion"], "exam": "pre_mains"},
            {"id": "bio_3", "name": "Disease", "subtopics": ["Infectious", "Non-Infectious", "Prevention"], "exam": "pre_mains"},
            {"id": "bio_4", "name": "Endocrine System", "subtopics": ["Glands", "Hormones", "Disorders"], "exam": "pre_mains"},
            {"id": "bio_5", "name": "Eye", "subtopics": ["Structure", "Defects", "Correction"], "exam": "pre_mains"},
            {"id": "bio_6", "name": "Reproductive System", "subtopics": ["Male", "Female", "Reproductive Health"], "exam": "pre_mains"},
            {"id": "bio_7", "name": "Blood", "subtopics": ["Composition", "Functions", "Coagulation"], "exam": "pre_mains"},
            {"id": "bio_8", "name": "Digestive System", "subtopics": ["Organs", "Digestion Process", "Enzymes"], "exam": "pre_mains"},
            {"id": "bio_9", "name": "Blood Circulatory System", "subtopics": ["Heart", "Blood Vessels", "Circulation"], "exam": "pre_mains"},
            {"id": "bio_10", "name": "Excretory System", "subtopics": ["Kidneys", "Nephron", "Urine Formation"], "exam": "mains"},
            {"id": "bio_11", "name": "Reproduction in Plants", "subtopics": ["Sexual", "Asexual", "Pollination"], "exam": "pre_mains"},
            {"id": "bio_12", "name": "Respiratory System", "subtopics": ["Lungs", "Respiration", "Gas Exchange"], "exam": "pre_mains"},
            {"id": "bio_13", "name": "Nervous System", "subtopics": ["Brain", "Spinal Cord", "Nerves"], "exam": "pre_mains"},
        ]
    },
    "hindi": {
        "name": "Hindi",
        "priority": "medium",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "hin_1", "name": "Synonyms (Paryayvachi Shabd)", "subtopics": ["Common Synonyms", "Practice"], "exam": "pre_mains"},
            {"id": "hin_2", "name": "Antonyms (Vilom Shabd)", "subtopics": ["Common Antonyms", "Practice"], "exam": "pre_mains"},
            {"id": "hin_3", "name": "One Word Substitution", "subtopics": ["Vakyansh ke liye ek shabd", "Practice"], "exam": "pre_mains"},
            {"id": "hin_4", "name": "Technical Terminology", "subtopics": ["Paribhashik Shabdavali", "Official Terms"], "exam": "pre_mains"},
            {"id": "hin_5", "name": "Idioms (Muhavare)", "subtopics": ["Common Idioms", "Usage", "Practice"], "exam": "pre_mains"},
            {"id": "hin_6", "name": "Proverbs (Lokoktiyan)", "subtopics": ["Kahavate", "Meanings", "Usage"], "exam": "pre_mains"},
            {"id": "hin_7", "name": "Word Purification (Shabd Shuddhi)", "subtopics": ["Spelling Errors", "Correction"], "exam": "pre_mains"},
            {"id": "hin_8", "name": "Sentence Purification (Vakya Shuddhi)", "subtopics": ["Grammar Errors", "Correction"], "exam": "pre_mains"},
            {"id": "hin_9", "name": "Word Pairs (Shabd Yugm)", "subtopics": ["Similar Words", "Differences"], "exam": "pre_mains"},
            {"id": "hin_10", "name": "Prefix (Upsarg)", "subtopics": ["Common Prefixes", "Usage"], "exam": "pre_mains"},
            {"id": "hin_11", "name": "Suffix (Pratyay)", "subtopics": ["Common Suffixes", "Usage"], "exam": "pre_mains"},
        ]
    },
    "indian_polity": {
        "name": "Indian Polity",
        "priority": "high",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "pol_1", "name": "Making of the Constitution", "subtopics": ["Constituent Assembly", "Drafting", "Adoption"], "exam": "pre_mains"},
            {"id": "pol_2", "name": "Features of the Constitution", "subtopics": ["Federal", "Parliamentary", "Written"], "exam": "pre_mains"},
            {"id": "pol_3", "name": "Amendment of the Constitution", "subtopics": ["Procedure", "Types", "Key Amendments"], "exam": "pre_mains"},
            {"id": "pol_4", "name": "Basic Structure Doctrine", "subtopics": ["Kesavananda Case", "Elements", "Significance"], "exam": "pre_mains"},
            {"id": "pol_5", "name": "Fundamental Rights", "subtopics": ["Art 14-32", "Recent Cases", "Restrictions"], "exam": "pre_mains"},
            {"id": "pol_6", "name": "Fundamental Duties", "subtopics": ["Art 51A", "11 Duties", "Importance"], "exam": "pre_mains"},
            {"id": "pol_7", "name": "Federal System", "subtopics": ["Features", "Distribution of Powers", "Cooperative Federalism"], "exam": "pre_mains"},
            {"id": "pol_8", "name": "Parliamentary System", "subtopics": ["Features", "Executive-Legislature", "Responsibility"], "exam": "pre_mains"},
            {"id": "pol_9", "name": "President", "subtopics": ["Election", "Powers", "Ordinances"], "exam": "pre_mains"},
            {"id": "pol_10", "name": "Prime Minister", "subtopics": ["Appointment", "Powers", "Cabinet"], "exam": "pre_mains"},
            {"id": "pol_11", "name": "Central Council of Ministers", "subtopics": ["Categories", "Collective Responsibility"], "exam": "pre_mains"},
            {"id": "pol_12", "name": "Centre-State Relations", "subtopics": ["Legislative", "Administrative", "Financial"], "exam": "pre_mains"},
            {"id": "pol_13", "name": "Supreme Court", "subtopics": ["Composition", "Jurisdiction", "Powers"], "exam": "pre_mains"},
            {"id": "pol_14", "name": "Judicial Review", "subtopics": ["Meaning", "Scope", "Cases"], "exam": "pre_mains"},
            {"id": "pol_15", "name": "Judicial Activism", "subtopics": ["PIL", "Suo Moto", "Cases"], "exam": "pre_mains"},
            {"id": "pol_16", "name": "Election Commission of India", "subtopics": ["Composition", "Powers", "Model Code"], "exam": "pre_mains"},
            {"id": "pol_17", "name": "CAG", "subtopics": ["Appointment", "Functions", "Reports"], "exam": "pre_mains"},
            {"id": "pol_18", "name": "UPSC", "subtopics": ["Composition", "Functions", "Independence"], "exam": "pre_mains"},
            {"id": "pol_19", "name": "NITI Aayog", "subtopics": ["Structure", "Functions", "Initiatives"], "exam": "pre_mains"},
            {"id": "pol_20", "name": "CVC", "subtopics": ["Central Vigilance Commission", "Functions", "Powers"], "exam": "pre_mains"},
            {"id": "pol_21", "name": "CIC", "subtopics": ["Central Information Commission", "RTI Act", "Appeals"], "exam": "pre_mains"},
            {"id": "pol_22", "name": "NHRC", "subtopics": ["National Human Rights Commission", "Functions", "Powers"], "exam": "pre_mains"},
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


@router.get("/syllabus/{subject_id}")
async def get_subject_details(subject_id: str):
    """Get details for a specific subject including all topics."""
    if subject_id not in RAS_SYLLABUS:
        raise HTTPException(status_code=404, detail=f"Subject '{subject_id}' not found")
    
    subject = RAS_SYLLABUS[subject_id]
    return {
        "subject_id": subject_id,
        "name": subject["name"],
        "priority": subject["priority"],
        "exam_type": subject.get("exam_type", "pre_mains"),
        "note": subject.get("note", ""),
        "topics": subject["topics"],
        "total_topics": len(subject["topics"])
    }


@router.get("/topic/{topic_id}")
async def get_topic_details(topic_id: str):
    """Get details for a specific topic including subtopics and PYQs."""
    # Find the topic in all subjects
    for subject_id, subject in RAS_SYLLABUS.items():
        for topic in subject["topics"]:
            if topic["id"] == topic_id:
                return {
                    "topic_id": topic_id,
                    "subject_id": subject_id,
                    "subject_name": subject["name"],
                    "name": topic["name"],
                    "subtopics": topic["subtopics"],
                    "exam": topic.get("exam", "pre_mains"),
                    "pyqs": SAMPLE_PYQS.get(topic_id, [])
                }
    
    raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")


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
