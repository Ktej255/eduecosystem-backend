from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.api import deps
from app.models.ras_planner import RASPlan, RASTopicProgress, RASRecording
from app.services.gemini_service import gemini_service
import json

router = APIRouter()

# Authorized email for custom planner
AUTHORIZED_EMAILS = ["chitrakumawat33@gmail.com"]

# Plan Configuration
PLAN_START_DATE = date(2026, 1, 1)
PLAN_DURATION_DAYS = 40

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
    },
    "rajasthan_science": {
        "name": "Rajasthan Science & Tech (RS)",
        "priority": "high",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "rs_1", "name": "Space Technology in India", "subtopics": ["ISRO", "Satellites", "Recent Missions"], "exam": "pre_mains"},
            {"id": "rs_2", "name": "Defense Technology", "subtopics": ["Missiles", "DRDO", "Modernization"], "exam": "pre_mains"},
        ]
    },
    "vision_ias": {
        "name": "Vision IAS Material",
        "priority": "medium",
        "exam_type": "pre_mains",
        "topics": [
            {"id": "vis_1", "name": "Current Affairs - Part 1", "subtopics": ["Polity", "Economy", "S&T"], "exam": "pre_mains"},
            {"id": "vis_2", "name": "Current Affairs - Part 2", "subtopics": ["Environment", "Social Issues"], "exam": "pre_mains"},
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

SAMPLE_MCQS = {
    "rg_1": [
        {
            "id": "mcq_rg1_1",
            "type": "prelims",
            "question": "Which of the following geographical features of Rajasthan is the oldest?",
            "options": ["Aravalli Range", "Thar Desert", "Eastern Plains", "Hadoti Plateau"],
            "correct_answer": 0,
            "explanation": "The Aravalli Range is one of the oldest fold mountain systems in the world."
        }
    ],
    "rs_1": [
        {
            "id": "mcq_rs1_1",
            "type": "prelims",
            "question": "Which ISRO mission successfully placed a spacecraft in orbit around Mars?",
            "options": ["Mangalyaan", "Chandrayaan-1", "Gaganyaan", "Aditya-L1"],
            "correct_answer": 0,
            "explanation": "Mangalyaan (Mars Orbiter Mission) was launched in 2013."
        }
    ],
    "pol_5": [
        {
            "id": "mcq_pol5_1",
            "type": "mains_mcq",
            "question": "Under Article 21, the right to life includes:",
            "options": ["Right to livelihood", "Right to privacy", "Right to shelter", "All of the above"],
            "correct_answer": 3,
            "explanation": "The Supreme Court has expanded Article 21 to include various rights necessary for a dignified life."
        }
    ]
}

# In-memory storage replaced by RDS database


class TopicUpdate(BaseModel):
    email: str
    topic_id: str
    completed: bool


class PlanRequest(BaseModel):
    email: str


class RecordingSubmit(BaseModel):
    email: str
    topic_id: str
    recording_url: Optional[str] = None
    explanation_text: Optional[str] = None
    duration: int


class AICheckRequest(BaseModel):
    email: str
    topic_id: str


@router.get("/check-access/{email}")
async def check_access(email: str, db: Session = Depends(deps.get_db)):
    """Check if email has access to custom planner."""
    # Also check if user exists in database
    from app.crud import user as crud_user
    user = crud_user.get_by_email(db, email=email)
    
    return {
        "has_access": email.lower() in [e.lower() for e in AUTHORIZED_EMAILS] or (user is not None),
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
async def get_dashboard(email: str, db: Session = Depends(deps.get_db)):
    """Get complete dashboard data for the email."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        # Check if user exists in DB even if not in hardcoded list
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get progress from database
    db_progress = db.query(RASTopicProgress).filter(RASTopicProgress.email == email).all()
    progress_map = {p.topic_id: p.completed for p in db_progress}
    
    # Calculate progress per subject
    subject_progress = {}
    total_topics = 0
    completed_topics = 0
    
    for subject_key, subject_data in RAS_SYLLABUS.items():
        topics = subject_data["topics"]
        subject_completed = 0
        
        for topic in topics:
            if progress_map.get(topic['id'], False):
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
async def get_today_plan(email: str, db: Session = Depends(deps.get_db)):
    """Get today's dynamic study plan based on the 40-day schedule."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    current_date = date.today()
    day_index = (current_date - PLAN_START_DATE).days
    
    # Check if plan has started
    if day_index < 0:
        return {
            "email": email,
            "status": "not_started",
            "message": f"Plan starts on {PLAN_START_DATE.strftime('%B %d, %Y')}. Get ready!",
            "days_until_start": abs(day_index),
            "slots": []
        }
    
    if day_index >= PLAN_DURATION_DAYS:
        return {
            "email": email,
            "status": "completed",
            "message": "Congratulations! You have completed the 40-day revision plan.",
            "slots": []
        }

    # Try to get plan from database
    db_plan = db.query(RASPlan).filter(
        RASPlan.email == email, 
        RASPlan.date == current_date
    ).first()
    
    if db_plan:
        return {
            "email": db_plan.email,
            "date": db_plan.date.isoformat(),
            "day_number": db_plan.day_number,
            "total_days": PLAN_DURATION_DAYS,
            "slots": db_plan.slots,
            "status": db_plan.status
        }
    
    # Flatten all topics to distribute them over 40 days
    all_topics = []
    for subj_key, subj_data in RAS_SYLLABUS.items():
        for topic in subj_data["topics"]:
            all_topics.append({
                **topic,
                "subject": subj_data["name"],
                "subject_key": subj_key,
                "priority": subj_data["priority"]
            })
    
    # Deterministic distribution
    total_topics = len(all_topics)
    topics_per_day = total_topics / PLAN_DURATION_DAYS
    start_idx = int(day_index * topics_per_day)
    end_idx = int((day_index + 1) * topics_per_day)
    
    day_topics = all_topics[start_idx:end_idx]
    
    # Create slots
    slots = [
        {"time": "13:30 - 15:00", "type": "new_topic", "duration": 90},
        {"time": "15:00 - 16:30", "type": "new_topic", "duration": 90},
        {"time": "17:00 - 18:00", "type": "revision", "duration": 60},
        {"time": "18:00 - 19:00", "type": "pyq_practice", "duration": 60},
        {"time": "19:00 - 20:00", "type": "weak_areas", "duration": 60},
        {"time": "20:00 - 20:30", "type": "summary", "duration": 30},
    ]
    
    # Assign topics to new_topic slots
    topic_idx = 0
    for slot in slots:
        if slot["type"] == "new_topic" and topic_idx < len(day_topics):
            slot["topic"] = day_topics[topic_idx]
            slot["pyqs"] = SAMPLE_PYQS.get(day_topics[topic_idx]["id"], [])
            topic_idx += 1
        elif slot["type"] == "revision":
            slot["description"] = "Revise topics from Day " + str(max(1, day_index))
        elif slot["type"] == "pyq_practice":
            slot["description"] = "Practice PYQs for today's topics"
        elif slot["type"] == "weak_areas":
            slot["description"] = "Focus on weak concepts from " + day_topics[0]["subject"] if day_topics else "General revision"
        elif slot["type"] == "summary":
            slot["description"] = "Daily summary and learning check"
    
    # Save plan to database
    new_plan = RASPlan(
        email=email,
        date=current_date,
        day_number=day_index + 1,
        slots=slots,
        status="active"
    )
    db.add(new_plan)
    db.commit()
    
    return {
        "email": email,
        "date": current_date.isoformat(),
        "day_number": day_index + 1,
        "total_days": PLAN_DURATION_DAYS,
        "slots": slots,
        "total_new_topics": len(day_topics),
        "status": "active"
    }


@router.post("/record-and-submit")
async def record_and_submit(submission: RecordingSubmit, db: Session = Depends(deps.get_db)):
    """Submit a recording/explanation for a topic with real AI analysis."""
    if submission.email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=submission.email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # 1. Fetch topic subtopics for AI comparison
    subtopics = []
    topic_name = ""
    for subject in RAS_SYLLABUS.values():
        for topic in subject["topics"]:
            if topic["id"] == submission.topic_id:
                subtopics = topic.get("subtopics", [])
                topic_name = topic["name"]
                break
    
    # 2. Analyze using real AI (Gemini)
    try:
        if submission.explanation_text:
            analysis = gemini_service.analyze_comprehension(
                student_summary=submission.explanation_text,
                key_concepts=subtopics,
                user=None  # Can pass user object if needed for tier-based routing
            )
            recall_score = int(analysis.get("score", 0) * 100)
            feedback = analysis.get("feedback", "Good effort. Keep practicing.")
        else:
            # Fallback for voice-only without transcript (mock for now)
            recall_score = 75
            feedback = "Recording received. Transcribe your explanation for detailed AI feedback."
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        recall_score = 70
        feedback = "AI analysis currently unavailable, but your progress has been recorded."
    
    # 3. Save recording to database
    new_recording = RASRecording(
        email=submission.email,
        topic_id=submission.topic_id,
        recording_url=submission.recording_url,
        explanation_text=submission.explanation_text,
        recall_score=recall_score,
        duration=submission.duration,
        feedback=feedback
    )
    db.add(new_recording)
    
    # 4. Auto-complete topic if score is high (Mastery Threshold: 80%)
    if recall_score >= 80:
        progress = db.query(RASTopicProgress).filter(
            RASTopicProgress.email == submission.email,
            RASTopicProgress.topic_id == submission.topic_id
        ).first()
        
        if progress:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            progress.recall_score = recall_score
            progress.method = "ai_verification"
        else:
            progress = RASTopicProgress(
                email=submission.email,
                topic_id=submission.topic_id,
                completed=True,
                completed_at=datetime.utcnow(),
                recall_score=recall_score,
                method="ai_verification"
            )
            db.add(progress)
            
    db.commit()
    
    return {
        "success": True, 
        "recall_score": recall_score,
        "feedback": feedback
    }


@router.post("/ai-learning-check")
async def ai_learning_check(request: AICheckRequest, db: Session = Depends(deps.get_db)):
    """Generate a personalized learning check question using AI."""
    if request.email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=request.email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # 1. Fetch topic details
    subtopics = []
    topic_name = ""
    for subject in RAS_SYLLABUS.values():
        for topic in subject["topics"]:
            if topic["id"] == request.topic_id:
                subtopics = topic.get("subtopics", [])
                topic_name = topic["name"]
                break
    
    if not topic_name:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Generate question using Gemini
    prompt = f"""You are an RAS (Rajasthan Administrative Services) Exam Coach. 
Generate ONE challenging active recall question for the topic: '{topic_name}'.
Focus on these subtopics: {subtopics}.
The question should test deep understanding, not just rote memorization.
JSON ONLY:
{{
    "question": "Your question here",
    "type": "active_recall",
    "context": "Context from syllabus"
}}"""

    try:
        response = gemini_service.generate_text(prompt, temperature=0.7)
        import json
        clean = response.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        return result
    except Exception as e:
        print(f"AI Quiz Generation Error: {e}")
        return {
            "question": f"Explain the key principles and importance of {topic_name} in the context of the RAS syllabus.",
            "type": "active_recall",
            "context": f"Based on {topic_name}"
        }


@router.post("/update-progress")
async def update_topic_progress(update: TopicUpdate, db: Session = Depends(deps.get_db)):
    """Update topic completion status."""
    if update.email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=update.email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    progress = db.query(RASTopicProgress).filter(
        RASTopicProgress.email == update.email,
        RASTopicProgress.topic_id == update.topic_id
    ).first()
    
    if progress:
        progress.completed = update.completed
        progress.completed_at = datetime.utcnow() if update.completed else None
        progress.last_attempt_at = datetime.utcnow()
    else:
        progress = RASTopicProgress(
            email=update.email,
            topic_id=update.topic_id,
            completed=update.completed,
            completed_at=datetime.utcnow() if update.completed else None
        )
        db.add(progress)
        
    db.commit()
    
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
async def reset_progress(email: str, db: Session = Depends(deps.get_db)):
    """Reset all progress for an email (for testing)."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete progress
    db.query(RASTopicProgress).filter(RASTopicProgress.email == email).delete()
    
    # Delete plans
    db.query(RASPlan).filter(RASPlan.email == email).delete()
    
    # Delete recordings
    db.query(RASRecording).filter(RASRecording.email == email).delete()
    
    db.commit()
    
    return {"success": True, "message": "Progress reset"}


@router.get("/plan-by-date/{email}/{target_date}")
async def get_plan_by_date(email: str, target_date: str, db: Session = Depends(deps.get_db)):
    """Get plan for a specific date (for calendar navigation)."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        selected_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Try to get existing plan from DB
    db_plan = db.query(RASPlan).filter(
        RASPlan.email == email,
        RASPlan.date == selected_date
    ).first()
    
    if db_plan:
        return {
            "email": db_plan.email,
            "date": db_plan.date.isoformat(),
            "day_number": db_plan.day_number,
            "total_days": PLAN_DURATION_DAYS,
            "slots": db_plan.slots,
            "status": db_plan.status
        }
    
    day_index = (selected_date - PLAN_START_DATE).days
    
    if day_index < 0:
        return {
            "email": email,
            "date": target_date,
            "status": "not_started",
            "day_number": 0,
            "message": f"This date is before the plan start (Jan 1, 2026)",
            "slots": []
        }
    
    if day_index >= PLAN_DURATION_DAYS:
        return {
            "email": email,
            "date": target_date,
            "status": "completed",
            "day_number": PLAN_DURATION_DAYS,
            "message": "Plan completed",
            "slots": []
        }
    
    # Generate plan for this specific date
    all_topics = []
    for subj_key, subj_data in RAS_SYLLABUS.items():
        for topic in subj_data["topics"]:
            all_topics.append({
                **topic,
                "subject": subj_data["name"],
                "subject_key": subj_key,
                "priority": subj_data["priority"]
            })
    
    total_topics = len(all_topics)
    topics_per_day = total_topics / PLAN_DURATION_DAYS
    start_idx = int(day_index * topics_per_day)
    end_idx = int((day_index + 1) * topics_per_day)
    day_topics = all_topics[start_idx:end_idx]
    
    # Create and save plan if it doesn't exist
    new_plan = RASPlan(
        email=email,
        date=selected_date,
        day_number=day_index + 1,
        slots=slots,
        status="active"
    )
    db.add(new_plan)
    db.commit()
    
    return {
        "email": email,
        "date": target_date,
        "day_number": day_index + 1,
        "total_days": PLAN_DURATION_DAYS,
        "slots": slots,
        "total_topics_today": len(day_topics),
        "status": "active"
    }


@router.get("/syllabus-topics/{subject_key}")
async def get_syllabus_topics(subject_key: str, email: str, db: Session = Depends(deps.get_db)):
    """Get all topics for a subject with completion status."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    if subject_key not in RAS_SYLLABUS:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Get progress from database
    db_progress = db.query(RASTopicProgress).filter(RASTopicProgress.email == email).all()
    progress_map = {p.topic_id: p for p in db_progress}
    
    subject = RAS_SYLLABUS[subject_key]
    topics_with_status = []
    
    for topic in subject["topics"]:
        progress = progress_map.get(topic["id"])
        topics_with_status.append({
            **topic,
            "completed": progress.completed if progress else False,
            "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
            "marked_by": progress.method if progress else None
        })
    
    return {
        "subject_key": subject_key,
        "subject_name": subject["name"],
        "priority": subject["priority"],
        "total_topics": len(topics_with_status),
        "completed_count": sum(1 for t in topics_with_status if t["completed"]),
        "topics": topics_with_status
    }


@router.get("/reports/{email}")
async def get_reports(email: str, db: Session = Depends(deps.get_db)):
    """Get retention and progress reports."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    user_recordings = db.query(RASRecording).filter(RASRecording.email == email).all()
    
    # Get progress from database
    db_progress = db.query(RASTopicProgress).filter(RASTopicProgress.email == email).all()
    progress_map = {p.topic_id: p.completed for p in db_progress}
    
    # Calculate per-subject completion
    subject_stats = {}
    for subj_key, subj_data in RAS_SYLLABUS.items():
        completed = 0
        for topic in subj_data["topics"]:
            if progress_map.get(topic["id"], False):
                completed += 1
        subject_stats[subj_key] = {
            "name": subj_data["name"],
            "total": len(subj_data["topics"]),
            "completed": completed,
            "percentage": round(completed / len(subj_data["topics"]) * 100) if subj_data["topics"] else 0
        }
    
    # Daily retention (mock data for now)
    retention_data = []
    for i in range(10):
        retention_data.append({
            "day": i + 1,
            "score": 70 + (i * 2) if i < 5 else 90 - (i - 5) * 3
        })
    
    return {
        "overall_retention": 82,
        "total_submissions": len(user_recordings),
        "daily_retention": retention_data,
        "subject_stats": subject_stats,
        "submissions": [
            {
                "timestamp": r.created_at.isoformat(),
                "topic_id": r.topic_id,
                "recording_url": r.recording_url,
                "recall_score": r.recall_score,
                "duration": r.duration
            } for r in user_recordings[-10:]
        ]
    }


@router.get("/calendar-overview/{email}")
async def get_calendar_overview(email: str, db: Session = Depends(deps.get_db)):
    """Get a 40-day calendar overview with completion status for each day."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get progress from database
    db_progress = db.query(RASTopicProgress).filter(RASTopicProgress.email == email).all()
    progress_map = {p.topic_id: p.completed for p in db_progress}
    
    calendar_days = []
    current = date.today()
    
    for day_num in range(PLAN_DURATION_DAYS):
        day_date = PLAN_START_DATE + timedelta(days=day_num)
        
        # Calculate topics for this day
        all_topics = []
        for subj_key, subj_data in RAS_SYLLABUS.items():
            for topic in subj_data["topics"]:
                all_topics.append(topic)
        
        total_topics = len(all_topics)
        topics_per_day = total_topics / PLAN_DURATION_DAYS
        start_idx = int(day_num * topics_per_day)
        end_idx = int((day_num + 1) * topics_per_day)
        day_topics = all_topics[start_idx:end_idx]
        
        # Check completion
        completed_count = 0
        for topic in day_topics:
            if progress_map.get(topic["id"], False):
                completed_count += 1
        
        status = "future"
        if day_date < current:
            status = "completed" if completed_count == len(day_topics) else "partial"
        elif day_date == current:
            status = "today"
        
        calendar_days.append({
            "day_number": day_num + 1,
            "date": day_date.isoformat(),
            "topics_count": len(day_topics),
            "completed_count": completed_count,
            "status": status
        })
    
    return {
        "email": email,
        "plan_start": PLAN_START_DATE.isoformat(),
        "plan_end": (PLAN_START_DATE + timedelta(days=PLAN_DURATION_DAYS - 1)).isoformat(),
        "total_days": PLAN_DURATION_DAYS,
        "days": calendar_days
    }


@router.get("/daily-test/{email}/{target_date}")
async def get_daily_test(email: str, target_date: str, db: Session = Depends(deps.get_db)):
    """Get MCQs for the topics scheduled on a specific date."""
    if email.lower() not in [e.lower() for e in AUTHORIZED_EMAILS]:
        from app.crud import user as crud_user
        if not crud_user.get_by_email(db, email=email):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Reuse logical mapping from get_plan_by_date
    try:
        selected_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    day_index = (selected_date - PLAN_START_DATE).days
    
    if day_index < 0 or day_index >= PLAN_DURATION_DAYS:
        return {"email": email, "date": target_date, "questions": [], "message": "No test available for this date"}

    # Get topics for this day
    all_topics = []
    for subj_key, subj_data in RAS_SYLLABUS.items():
        for topic in subj_data["topics"]:
            all_topics.append(topic)
    
    total_topics = len(all_topics)
    topics_per_day = total_topics / PLAN_DURATION_DAYS
    start_idx = int(day_index * topics_per_day)
    end_idx = int((day_index + 1) * topics_per_day)
    day_topics = all_topics[start_idx:end_idx]
    
    # Collect MCQs for these topics
    test_questions = []
    for topic in day_topics:
        topic_mcqs = SAMPLE_MCQS.get(topic["id"], [])
        for q in topic_mcqs:
            test_questions.append({
                **q,
                "topic_name": topic["name"]
            })
            
    # Add some generic questions if none found for specific topics to ensure a test experience
    if not test_questions:
        test_questions = [
            {
                "id": "gen_1",
                "type": "prelims",
                "question": "Which city of Rajasthan is known as the 'Pink City'?",
                "options": ["Jodhpur", "Jaipur", "Udaipur", "Bikaner"],
                "correct_answer": 1,
                "explanation": "Jaipur was painted pink to welcome Prince Albert in 1876.",
                "topic_name": "General Rajasthan"
            },
            {
                "id": "gen_2",
                "type": "mains_mcq",
                "question": "The Rajasthan Public Service Commission (RPSC) is located in:",
                "options": ["Jaipur", "Ajmer", "Udaipur", "Kota"],
                "correct_answer": 1,
                "explanation": "RPSC headquarters is in Ajmer.",
                "topic_name": "General Rajasthan"
            }
        ]
    
    return {
        "email": email,
        "date": target_date,
        "day_number": day_index + 1,
        "questions": test_questions,
        "total_questions": len(test_questions)
    }
