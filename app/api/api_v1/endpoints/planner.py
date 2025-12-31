"""
RAS Revision Planner API
40-Day Revision Plan Endpoints for Students, Teachers, and Admins
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

router = APIRouter()

# ============================================================
# AUTHORIZED USERS (Phase 1: In-memory, Phase 2: Database)
# ============================================================
AUTHORIZED_RAS_USERS = {
    "chitrakumawat33@gmail.com",
    "ktej255@gmail.com",  # Master ID always has access
}

# ============================================================
# RAS SYLLABUS DATA - Updated from Vijay Sir's Syllabus
# ============================================================
RAS_SUBJECTS = {
    # ==================== RAJASTHAN GEOGRAPHY ====================
    "rajasthan_geography": {
        "name": "Rajasthan Geography",
        "priority": "high",
        "topics": [
            {"id": "rg_01", "name": "Basic Geography: Origin of Rajasthan", "subtopics": ["Formation", "Geological history", "Tectonic features"]},
            {"id": "rg_02", "name": "Location & Extension", "subtopics": ["Latitude", "Longitude", "Boundaries", "Area"]},
            {"id": "rg_03", "name": "Physical Divisions", "subtopics": ["Aravalli Range", "Thar Desert", "Eastern Plains", "Hadoti Plateau"]},
            {"id": "rg_04", "name": "Hydro Geography / Drainage System", "subtopics": ["Rivers", "Drainage patterns", "Mains Points"]},
            {"id": "rg_05", "name": "Salt Lakes", "subtopics": ["Sambhar", "Didwana", "Pachpadra", "Lunkaransar"]},
            {"id": "rg_06", "name": "Irrigation Projects (Pre)", "subtopics": ["Major projects", "Minor projects", "Lift irrigation"]},
            {"id": "rg_07", "name": "Water Conservation Techniques", "subtopics": ["Traditional methods", "Johad", "Taanka", "Check dams"]},
            {"id": "rg_08", "name": "IGNP (Indira Gandhi Canal Project)", "subtopics": ["Phases", "Impact", "Command area", "Challenges"]},
            {"id": "rg_09", "name": "Soil (Pre)", "subtopics": ["Types", "Distribution", "Soil conservation"]},
            {"id": "rg_10", "name": "Minerals", "subtopics": ["Metallic", "Non-metallic", "Mining industry", "Distribution"]},
            {"id": "rg_11", "name": "Vegetation", "subtopics": ["Forest types", "Distribution", "Conservation", "Afforestation"]},
            {"id": "rg_12", "name": "Wildlife & Biodiversity", "subtopics": ["National Parks", "Wildlife Sanctuaries", "Conservation efforts"]},
            {"id": "rg_13", "name": "Agriculture", "subtopics": ["Cropping patterns", "Major crops", "Agricultural issues"]},
            {"id": "rg_14", "name": "UNESCO Sites", "subtopics": ["World Heritage Sites", "Tentative list", "Criteria"]},
            {"id": "rg_15", "name": "Industry", "subtopics": ["Major industries", "Industrial areas", "SEZs"]},
            {"id": "rg_16", "name": "Energy", "subtopics": ["Thermal", "Solar", "Wind", "Nuclear energy"]},
            {"id": "rg_17", "name": "Population", "subtopics": ["Census data", "Density", "Sex ratio", "Literacy"]},
            {"id": "rg_18", "name": "Tourism (Pre)", "subtopics": ["Circuits", "Sites", "Parks", "World Heritage Sites", "Geo-parks"]},
        ]
    },
    
    # ==================== PHYSICS ====================
    "physics": {
        "name": "Physics",
        "priority": "medium",
        "topics": [
            {"id": "ph_01", "name": "General Information (Samanya Jankari)", "subtopics": ["Units", "Measurements", "Physical quantities"]},
            {"id": "ph_02", "name": "Gravitational Force (Gurutvakarshan Bal)", "subtopics": ["Newton's laws", "Gravity", "Orbits", "Satellites"]},
            {"id": "ph_03", "name": "Heat (Ushma)", "subtopics": ["Temperature", "Thermal expansion", "Calorimetry", "Heat transfer"]},
            {"id": "ph_04", "name": "Sound & Electromagnetic Waves", "subtopics": ["Wave properties", "Sound propagation", "EM spectrum"]},
            {"id": "ph_05", "name": "Light (Prakash)", "subtopics": ["Reflection", "Refraction", "Lenses", "Optical instruments"], "note": "Pre = 2 Questions, Mains = 12 Marks"},
            {"id": "ph_06", "name": "Nuclear Fission & Fusion", "subtopics": ["Nuclear reactions", "Reactors", "Applications"]},
            {"id": "ph_07", "name": "Electrostatics & Current Electricity", "subtopics": ["Charges", "Electric field", "Circuits", "Ohm's law"], "note": "Pre + Mains"},
            {"id": "ph_08", "name": "Magnetism & Electromagnetism", "subtopics": ["Magnets", "Magnetic field", "Electromagnetic induction"]},
            {"id": "ph_09", "name": "NMR & MRI", "subtopics": ["Principles", "Applications", "Medical imaging"], "note": "Mains Only"},
        ]
    },
    
    # ==================== REASONING ====================
    "reasoning": {
        "name": "Reasoning",
        "priority": "high",
        "topics": [
            {"id": "rs_01", "name": "Shapes and their sub-sections", "subtopics": ["Figure analysis", "Pattern recognition"]},
            {"id": "rs_02", "name": "Problems Based on Relation", "subtopics": ["Blood relations", "Family tree", "Coded relations"]},
            {"id": "rs_03", "name": "Coding-Decoding", "subtopics": ["Letter coding", "Number coding", "Mixed coding"]},
            {"id": "rs_04", "name": "Mirror Image", "subtopics": ["Letter/Number mirrors", "Figure mirrors"]},
            {"id": "rs_05", "name": "Water Image", "subtopics": ["Reflection principles", "Figure inversion"]},
            {"id": "rs_06", "name": "Direction Sense Test", "subtopics": ["Cardinal directions", "Distance calculation", "Route finding"]},
            {"id": "rs_07", "name": "Cube, Cuboid, and Dice", "subtopics": ["Dice problems", "Cube cutting", "Painted cubes"]},
            {"id": "rs_08", "name": "Logical Venn Diagram", "subtopics": ["Set relationships", "Multi-set diagrams"]},
            {"id": "rs_09", "name": "Number/Alphabet Sequence", "subtopics": ["Series completion", "Pattern finding"]},
            {"id": "rs_10", "name": "Sitting Arrangement", "subtopics": ["Linear", "Circular", "Complex arrangements"]},
            {"id": "rs_11", "name": "Syllogism (Nyay Nigaman)", "subtopics": ["Statements", "Conclusions", "Venn approach"]},
            {"id": "rs_12", "name": "Statement & Argument (Kathan Tark)", "subtopics": ["Strong/Weak arguments", "Validity check"]},
            {"id": "rs_13", "name": "Statement & Assumptions", "subtopics": ["Implicit assumptions", "Explicit assumptions"]},
            {"id": "rs_14", "name": "Cause and Effect", "subtopics": ["Identifying cause", "Effect analysis", "Independent events"]},
            {"id": "rs_15", "name": "Statement & Conclusions/Inferences", "subtopics": ["Drawing conclusions", "Valid inferences"]},
            {"id": "rs_16", "name": "Statement & Courses of Action", "subtopics": ["Practical actions", "Feasibility check"]},
        ],
        "note": "20 Questions total (Maths + Reasoning). 5 questions from CSAT."
    },
    
    # ==================== INDIAN ECONOMY ====================
    "indian_economy": {
        "name": "Indian Economy",
        "priority": "high",
        "topics": [
            {"id": "ie_01", "name": "Inflation", "subtopics": ["Types", "Measurement", "Control measures", "WPI", "CPI"]},
            {"id": "ie_02", "name": "Banking", "subtopics": ["RBI", "Commercial banks", "NBFCs", "Digital banking"]},
            {"id": "ie_03", "name": "Finance Market", "subtopics": ["Money market", "Capital market", "Stock exchanges"]},
            {"id": "ie_04", "name": "Fiscal Policy", "subtopics": ["Budget", "Taxation", "Public expenditure", "Deficit financing"]},
            {"id": "ie_05", "name": "Unemployment", "subtopics": ["Types", "Measurement", "Employment schemes"]},
            {"id": "ie_06", "name": "Human Development Report", "subtopics": ["HDI", "Indicators", "India's ranking"]},
            {"id": "ie_07", "name": "Trade Policy", "subtopics": ["Exports", "Imports", "FTAs", "WTO"]},
            {"id": "ie_08", "name": "Global Financial Organisations", "subtopics": ["IMF", "World Bank", "ADB", "NDB", "AIIB"]},
            {"id": "ie_09", "name": "Agriculture Sector", "subtopics": ["Problems", "Schemes", "MSP", "Land reforms"]},
            {"id": "ie_10", "name": "Food Management", "subtopics": ["PDS", "Food security", "Buffer stocks"]},
            {"id": "ie_11", "name": "Food Processing", "subtopics": ["Industry scope", "Schemes", "Cold chain"]},
            {"id": "ie_12", "name": "Industrial Sector", "subtopics": ["Manufacturing", "MSMEs", "Industrial policy"]},
            {"id": "ie_13", "name": "E-Commerce", "subtopics": ["Digital economy", "Regulations", "FDI in e-commerce"]},
            {"id": "ie_14", "name": "Subsidy", "subtopics": ["Types", "Pros/Cons", "Rationalization", "DBT"]},
            {"id": "ie_15", "name": "Public, Private, and Merit Goods", "subtopics": ["Definitions", "Examples", "Government role"]},
            {"id": "ie_16", "name": "Government Schemes (Types)", "subtopics": ["CSS", "State schemes", "Social security"]},
            {"id": "ie_17", "name": "Regulatory Effectiveness", "subtopics": ["Regulatory bodies", "Governance", "Reforms"]},
            {"id": "ie_18", "name": "Role of Government in Economic Activities", "subtopics": ["PSUs", "Disinvestment", "PPP"]},
            {"id": "ie_19", "name": "India's Education Policy", "subtopics": ["NEP 2020", "Sarva Shiksha", "Higher education"], "note": "Not Imp."},
        ]
    },
    
    # ==================== RAJASTHAN HISTORY ====================
    "rajasthan_history": {
        "name": "Rajasthan History",
        "priority": "high",
        "topics": [
            {"id": "rh_01", "name": "History of Rajasthan - General", "subtopics": ["Overview", "Periodization", "Historical sources"]},
            {"id": "rh_02", "name": "Sources of Ancient History", "subtopics": ["Archaeological", "Literary", "Inscriptions", "Coins"]},
            {"id": "rh_03", "name": "Chauhan Dynasty", "subtopics": ["Prithviraj III", "Ajmer", "Battles", "Administration"]},
            {"id": "rh_04", "name": "Parmar Dynasty", "subtopics": ["Abu", "Malwa", "Architecture", "Contributions"]},
            {"id": "rh_05", "name": "Pratihar Dynasty", "subtopics": ["Gurjara-Pratihara", "Mandore", "Jodhpur foundation"]},
            {"id": "rh_06", "name": "Guhil / Sisodia Dynasty", "subtopics": ["Mewar", "Rana Kumbha", "Pratap", "Rajput pride"]},
            {"id": "rh_07", "name": "Rathore Dynasty", "subtopics": ["Marwar", "Jodhpur", "Bikaner", "Military history"]},
            {"id": "rh_08", "name": "Kachhwaha Dynasty", "subtopics": ["Amber", "Jaipur", "Mughal alliance", "Man Singh"]},
        ]
    },
    
    # ==================== BIOLOGY ====================
    "biology": {
        "name": "Biology",
        "priority": "medium",
        "topics": [
            {"id": "bi_01", "name": "Balanced Diet", "subtopics": ["Nutrients", "Vitamins", "Minerals", "Deficiency diseases"], "note": "Pre Only"},
            {"id": "bi_02", "name": "Blood Group", "subtopics": ["ABO system", "Rh factor", "Transfusion", "Compatibility"], "note": "Pre + Mains"},
            {"id": "bi_03", "name": "Disease", "subtopics": ["Infectious", "Non-infectious", "Prevention", "Immunity"]},
            {"id": "bi_04", "name": "Endocrine System", "subtopics": ["Glands", "Hormones", "Disorders", "Feedback mechanism"]},
            {"id": "bi_05", "name": "Eye", "subtopics": ["Structure", "Function", "Defects", "Corrections"]},
            {"id": "bi_06", "name": "Reproductive System", "subtopics": ["Male", "Female", "Reproductive health"]},
            {"id": "bi_07", "name": "Blood", "subtopics": ["Composition", "Functions", "Clotting", "Blood cells"]},
            {"id": "bi_08", "name": "Digestive System", "subtopics": ["Organs", "Digestion process", "Enzymes", "Absorption"]},
            {"id": "bi_09", "name": "Blood Circulatory System", "subtopics": ["Heart", "Blood vessels", "Circulation types"]},
            {"id": "bi_10", "name": "Excretory System", "subtopics": ["Kidneys", "Nephron", "Urine formation"], "note": "Mains Only"},
            {"id": "bi_11", "name": "Sexual and Asexual Reproduction in Plants", "subtopics": ["Methods", "Pollination", "Fertilization"]},
            {"id": "bi_12", "name": "Respiratory System", "subtopics": ["Organs", "Mechanism", "Gas exchange", "Disorders"]},
            {"id": "bi_13", "name": "Nervous System", "subtopics": ["Brain", "Spinal cord", "Nerves", "Reflexes"]},
        ]
    },
    
    # ==================== HINDI ====================
    "hindi": {
        "name": "Hindi",
        "priority": "medium",
        "topics": [
            {"id": "hi_01", "name": "Synonyms (Paryayvachi Shabd)", "subtopics": ["Common words", "Practice sets"]},
            {"id": "hi_02", "name": "Antonyms (Vilom Shabd)", "subtopics": ["Common words", "Practice sets"]},
            {"id": "hi_03", "name": "One word for a phrase (Vakyansh ke liye ek shabd)", "subtopics": ["Phrases", "Single words"]},
            {"id": "hi_04", "name": "Technical Terminology (Paribhashik Shabdavali)", "subtopics": ["Administrative terms", "Legal terms"]},
            {"id": "hi_05", "name": "Idioms (Muhavare)", "subtopics": ["Common idioms", "Usage", "Meanings"]},
            {"id": "hi_06", "name": "Proverbs (Kahavate, Lokoktiyan)", "subtopics": ["Common proverbs", "Meanings", "Usage"]},
            {"id": "hi_07", "name": "Word Purification (Shabd Shuddhi)", "subtopics": ["Common errors", "Correct forms"]},
            {"id": "hi_08", "name": "Sentence Purification (Vakya Shuddhi)", "subtopics": ["Grammar errors", "Correct sentences"]},
            {"id": "hi_09", "name": "Word Pairs (Shabd Yugm)", "subtopics": ["Similar words", "Different meanings"]},
            {"id": "hi_10", "name": "Prefix (Upsarg)", "subtopics": ["Common prefixes", "Word formation"]},
            {"id": "hi_11", "name": "Suffix (Pratyay)", "subtopics": ["Common suffixes", "Word formation"]},
        ]
    },
    
    # ==================== INDIAN POLITY ====================
    "indian_polity": {
        "name": "Indian Polity",
        "priority": "high",
        "topics": [
            {"id": "ip_01", "name": "Making of the Constitution", "subtopics": ["Constituent Assembly", "Drafting", "Key debates"]},
            {"id": "ip_02", "name": "Features of the Constitution", "subtopics": ["Salient features", "Borrowed provisions", "Uniqueness"]},
            {"id": "ip_03", "name": "Amendment of the Constitution", "subtopics": ["Article 368", "Types", "Important amendments"]},
            {"id": "ip_04", "name": "Basic Structure of Constitution", "subtopics": ["Kesavananda Bharati case", "Doctrine evolution"]},
            {"id": "ip_05", "name": "Fundamental Rights", "subtopics": ["Article 12-35", "Right to equality", "Freedoms", "Remedies"]},
            {"id": "ip_06", "name": "Fundamental Duties", "subtopics": ["Article 51A", "11 duties", "Swaran Singh Committee"]},
            {"id": "ip_07", "name": "Federal System", "subtopics": ["Centre-State relations", "Federal features", "Unitary features"]},
            {"id": "ip_08", "name": "Parliamentary System", "subtopics": ["Features", "Parliament structure", "Sessions"]},
            {"id": "ip_09", "name": "President", "subtopics": ["Election", "Powers", "Impeachment", "Ordinances"]},
            {"id": "ip_10", "name": "Prime Minister", "subtopics": ["Appointment", "Powers", "PMO", "Council of Ministers"]},
            {"id": "ip_11", "name": "Central Council of Ministers", "subtopics": ["Categories", "Collective responsibility", "Cabinet committees"]},
            {"id": "ip_12", "name": "Centre-State Relations", "subtopics": ["Legislative", "Administrative", "Financial", "Sarkaria Commission"]},
            {"id": "ip_13", "name": "Supreme Court", "subtopics": ["Composition", "Jurisdiction", "Judicial review"]},
            {"id": "ip_14", "name": "Judicial Review", "subtopics": ["Scope", "Limitations", "Cases"]},
            {"id": "ip_15", "name": "Judicial Activism", "subtopics": ["PIL", "Judicial overreach", "Significance"]},
            {"id": "ip_16", "name": "Election Commission of India", "subtopics": ["Composition", "Functions", "Model code"]},
            {"id": "ip_17", "name": "CAG (Comptroller and Auditor General)", "subtopics": ["Article 148-151", "Functions", "Reports"]},
            {"id": "ip_18", "name": "UPSC", "subtopics": ["Composition", "Functions", "Examinations"]},
            {"id": "ip_19", "name": "NITI Aayog", "subtopics": ["Structure", "Functions", "Comparison with Planning Commission"]},
            {"id": "ip_20", "name": "Central Vigilance Commission (CVC)", "subtopics": ["Composition", "Functions", "Lokpal link"]},
            {"id": "ip_21", "name": "Central Information Commission (CIC)", "subtopics": ["RTI Act", "Functions", "Appeals"]},
            {"id": "ip_22", "name": "National Human Rights Commission (NHRC)", "subtopics": ["Composition", "Functions", "Powers"]},
        ]
    },
}


# In-memory progress storage (Phase 2: Move to database)
USER_PROGRESS: Dict[str, Dict[str, bool]] = {}

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================
class AccessCheckResponse(BaseModel):
    email: str
    has_access: bool
    message: str

class ProgressUpdateRequest(BaseModel):
    email: str
    topic_id: str
    completed: bool

class SubjectProgress(BaseModel):
    name: str
    priority: str
    total_topics: int
    completed_topics: int
    percentage: float

class DashboardResponse(BaseModel):
    email: str
    overall_progress: dict
    subject_progress: Dict[str, SubjectProgress]

class CalendarDay(BaseModel):
    day_number: int
    date: str
    topics_count: int
    completed_count: int
    status: str

class CalendarOverview(BaseModel):
    plan_start: str
    plan_end: str
    total_days: int
    days: List[CalendarDay]

class TimeSlot(BaseModel):
    time: str
    type: str
    duration: int
    topic: Optional[dict] = None
    description: Optional[str] = None
    subject: Optional[str] = None

class DayPlanResponse(BaseModel):
    email: str
    date: str
    day_number: int
    total_days: int
    slots: List[TimeSlot]
    total_topics_today: int
    status: str
    message: Optional[str] = None

class TopicWithStatus(BaseModel):
    id: str
    name: str
    subject: str
    subtopics: List[str]
    priority: str
    completed: bool
    completed_at: Optional[str] = None
    marked_by: Optional[str] = None

class SubjectTopicsResponse(BaseModel):
    subject_key: str
    subject_name: str
    priority: str
    total_topics: int
    completed_count: int
    topics: List[TopicWithStatus]

class ReportsResponse(BaseModel):
    overall_retention: float
    total_submissions: int
    daily_retention: List[dict]
    subject_stats: Dict[str, dict]

class StudentListItem(BaseModel):
    email: str
    name: str
    overall_progress: float
    last_active: Optional[str] = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_user_progress(email: str) -> Dict[str, bool]:
    if email not in USER_PROGRESS:
        USER_PROGRESS[email] = {}
    return USER_PROGRESS[email]

def count_completed_for_subject(email: str, subject_key: str) -> int:
    progress = get_user_progress(email)
    subject = RAS_SUBJECTS.get(subject_key, {})
    topics = subject.get("topics", [])
    return sum(1 for t in topics if progress.get(t["id"], False))

def get_all_topics() -> List[dict]:
    """Get flat list of all topics across subjects"""
    all_topics = []
    for subject_key, subject_data in RAS_SUBJECTS.items():
        for topic in subject_data["topics"]:
            all_topics.append({
                **topic,
                "subject": subject_data["name"],
                "subject_key": subject_key,
                "priority": subject_data["priority"]
            })
    return all_topics

def generate_40_day_calendar(email: str, start_date: datetime) -> List[CalendarDay]:
    """Generate 40-day calendar with topic distribution"""
    all_topics = get_all_topics()
    topics_per_day = max(1, len(all_topics) // 40)
    progress = get_user_progress(email)
    today = datetime.now().date()
    
    days = []
    topic_idx = 0
    
    for day_num in range(1, 41):
        day_date = start_date + timedelta(days=day_num - 1)
        day_topics = all_topics[topic_idx:topic_idx + topics_per_day]
        topic_idx += topics_per_day
        
        completed_count = sum(1 for t in day_topics if progress.get(t["id"], False))
        
        if day_date.date() == today:
            status = "today"
        elif day_date.date() < today:
            status = "completed" if completed_count == len(day_topics) else "partial"
        else:
            status = "future"
        
        days.append(CalendarDay(
            day_number=day_num,
            date=day_date.strftime("%Y-%m-%d"),
            topics_count=len(day_topics),
            completed_count=completed_count,
            status=status
        ))
    
    return days

# ============================================================
# STUDENT ENDPOINTS
# ============================================================

@router.get("/check-access/{email}", response_model=AccessCheckResponse)
async def check_access(email: str):
    """Check if user has access to RAS Revision Plan"""
    has_access = email.lower() in {e.lower() for e in AUTHORIZED_RAS_USERS}
    return AccessCheckResponse(
        email=email,
        has_access=has_access,
        message="Access granted" if has_access else "Access restricted. Contact admin for authorization."
    )

@router.get("/dashboard/{email}", response_model=DashboardResponse)
async def get_dashboard(email: str):
    """Get overall dashboard with progress stats"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    subject_progress = {}
    total_topics = 0
    total_completed = 0
    
    for subject_key, subject_data in RAS_SUBJECTS.items():
        topic_count = len(subject_data["topics"])
        completed = count_completed_for_subject(email, subject_key)
        total_topics += topic_count
        total_completed += completed
        
        subject_progress[subject_key] = SubjectProgress(
            name=subject_data["name"],
            priority=subject_data["priority"],
            total_topics=topic_count,
            completed_topics=completed,
            percentage=round((completed / topic_count) * 100, 1) if topic_count > 0 else 0
        )
    
    return DashboardResponse(
        email=email,
        overall_progress={
            "total_topics": total_topics,
            "completed_topics": total_completed,
            "percentage": round((total_completed / total_topics) * 100, 1) if total_topics > 0 else 0
        },
        subject_progress=subject_progress
    )

@router.get("/calendar-overview/{email}", response_model=CalendarOverview)
async def get_calendar_overview(email: str):
    """Get 40-day calendar overview"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Plan starts Jan 1, 2026
    start_date = datetime(2026, 1, 1)
    end_date = start_date + timedelta(days=39)
    
    days = generate_40_day_calendar(email, start_date)
    
    return CalendarOverview(
        plan_start=start_date.strftime("%Y-%m-%d"),
        plan_end=end_date.strftime("%Y-%m-%d"),
        total_days=40,
        days=days
    )

@router.get("/plan-by-date/{email}/{date}", response_model=DayPlanResponse)
async def get_plan_by_date(email: str, date: str):
    """Get detailed plan for a specific date"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    start_date = datetime(2026, 1, 1)
    target_date = datetime.strptime(date, "%Y-%m-%d")
    day_number = (target_date - start_date).days + 1
    
    if day_number < 1 or day_number > 40:
        raise HTTPException(status_code=404, detail="Date outside 40-day plan range")
    
    all_topics = get_all_topics()
    topics_per_day = max(1, len(all_topics) // 40)
    start_idx = (day_number - 1) * topics_per_day
    day_topics = all_topics[start_idx:start_idx + topics_per_day]
    
    progress = get_user_progress(email)
    
    # Build time slots
    slots = []
    base_time = datetime.strptime("13:30", "%H:%M")
    
    for i, topic in enumerate(day_topics):
        slot_time = base_time + timedelta(hours=i)
        slots.append(TimeSlot(
            time=slot_time.strftime("%I:%M %p"),
            type="study_session",
            duration=60,
            topic={
                **topic,
                "completed": progress.get(topic["id"], False)
            }
        ))
    
    # Add revision and test slots
    slots.append(TimeSlot(
        time="06:30 PM",
        type="revision",
        duration=30,
        description="Quick revision of today's topics"
    ))
    
    slots.append(TimeSlot(
        time="07:00 PM",
        type="pyq_practice",
        duration=60,
        description="Previous Year Questions practice"
    ))
    
    slots.append(TimeSlot(
        time="08:00 PM",
        type="daily_test",
        duration=30,
        description="Daily retention test"
    ))
    
    return DayPlanResponse(
        email=email,
        date=date,
        day_number=day_number,
        total_days=40,
        slots=slots,
        total_topics_today=len(day_topics),
        status="active"
    )

@router.post("/update-progress")
async def update_progress(request: ProgressUpdateRequest):
    """Mark a topic as completed or incomplete"""
    if request.email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    progress = get_user_progress(request.email)
    progress[request.topic_id] = request.completed
    
    return {
        "success": True,
        "topic_id": request.topic_id,
        "completed": request.completed,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/syllabus-topics/{subject_key}")
async def get_syllabus_topics(subject_key: str, email: str):
    """Get all topics for a subject with completion status"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if subject_key not in RAS_SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    subject = RAS_SUBJECTS[subject_key]
    progress = get_user_progress(email)
    
    topics_with_status = []
    for topic in subject["topics"]:
        topics_with_status.append(TopicWithStatus(
            id=topic["id"],
            name=topic["name"],
            subject=subject["name"],
            subtopics=topic["subtopics"],
            priority=subject["priority"],
            completed=progress.get(topic["id"], False)
        ))
    
    completed_count = sum(1 for t in topics_with_status if t.completed)
    
    return SubjectTopicsResponse(
        subject_key=subject_key,
        subject_name=subject["name"],
        priority=subject["priority"],
        total_topics=len(topics_with_status),
        completed_count=completed_count,
        topics=topics_with_status
    )

@router.get("/reports/{email}", response_model=ReportsResponse)
async def get_reports(email: str):
    """Get retention and progress reports"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    progress = get_user_progress(email)
    total_topics = sum(len(s["topics"]) for s in RAS_SUBJECTS.values())
    completed = sum(1 for v in progress.values() if v)
    
    # Generate mock retention data
    daily_retention = [
        {"day": i, "score": min(100, 60 + i * 2)} for i in range(1, 41)
    ]
    
    subject_stats = {}
    for subject_key, subject_data in RAS_SUBJECTS.items():
        topic_count = len(subject_data["topics"])
        completed_count = count_completed_for_subject(email, subject_key)
        subject_stats[subject_key] = {
            "name": subject_data["name"],
            "total": topic_count,
            "completed": completed_count,
            "percentage": round((completed_count / topic_count) * 100, 1) if topic_count > 0 else 0
        }
    
    return ReportsResponse(
        overall_retention=round((completed / total_topics) * 100, 1) if total_topics > 0 else 0,
        total_submissions=completed,
        daily_retention=daily_retention,
        subject_stats=subject_stats
    )

@router.get("/daily-test/{email}/{date}")
async def get_daily_test(email: str, date: str):
    """Get daily test questions"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate sample MCQs for the day
    questions = [
        {
            "id": 1,
            "question": "Which Rajput dynasty founded Jaipur?",
            "options": ["Rathores", "Kachwahas", "Sisodias", "Chauhans"],
            "correct_answer": 1,
            "topic_name": "Rajput Dynasties",
            "explanation": "Kachwahas founded Jaipur under Sawai Jai Singh II in 1727."
        },
        {
            "id": 2,
            "question": "The Thar Desert is also known as?",
            "options": ["Great Indian Desert", "Marusthali", "Both A and B", "None"],
            "correct_answer": 2,
            "topic_name": "Physical Features",
            "explanation": "Thar Desert is called both Great Indian Desert and Marusthali (Land of Death)."
        },
        {
            "id": 3,
            "question": "Which dance form of Rajasthan is recognized by UNESCO?",
            "options": ["Ghoomar", "Kalbeliya", "Bhavai", "Chari"],
            "correct_answer": 1,
            "topic_name": "Folk Arts",
            "explanation": "Kalbeliya dance was inscribed on UNESCO's Intangible Cultural Heritage list in 2010."
        },
        {
            "id": 4,
            "question": "Rajasthan was formed on which date?",
            "options": ["March 30, 1949", "November 1, 1956", "January 26, 1950", "August 15, 1947"],
            "correct_answer": 0,
            "topic_name": "Formation of Rajasthan",
            "explanation": "Rajasthan was formed on March 30, 1949, after the merger of princely states."
        },
        {
            "id": 5,
            "question": "Which is the largest district of Rajasthan by area?",
            "options": ["Barmer", "Jaisalmer", "Bikaner", "Jodhpur"],
            "correct_answer": 1,
            "topic_name": "Geography",
            "explanation": "Jaisalmer is the largest district of Rajasthan by area (38,401 sq km)."
        }
    ]
    
    return {"date": date, "questions": questions}

# ============================================================
# ADMIN/TEACHER ENDPOINTS
# ============================================================

@router.get("/admin/student-list")
async def get_student_list():
    """Get list of all authorized RAS students with their progress"""
    students = []
    for email in AUTHORIZED_RAS_USERS:
        progress = get_user_progress(email)
        total_topics = sum(len(s["topics"]) for s in RAS_SUBJECTS.values())
        completed = sum(1 for v in progress.values() if v)
        
        students.append(StudentListItem(
            email=email,
            name=email.split("@")[0].replace(".", " ").title(),
            overall_progress=round((completed / total_topics) * 100, 1) if total_topics > 0 else 0,
            last_active=datetime.utcnow().isoformat() if progress else None
        ))
    
    return {"students": students, "total_count": len(students)}

@router.get("/admin/student-progress/{email}")
async def get_student_progress_admin(email: str):
    """Admin view of a specific student's progress"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=404, detail="Student not found in authorized list")
    
    # Return full dashboard data for admin view
    return await get_dashboard(email)

@router.post("/admin/authorize-user")
async def authorize_user(email: str):
    """Add a user to the authorized RAS users list"""
    AUTHORIZED_RAS_USERS.add(email.lower())
    return {"success": True, "email": email, "message": f"{email} has been authorized for RAS Revision Plan"}

@router.delete("/admin/revoke-access/{email}")
async def revoke_access(email: str):
    """Remove a user from the authorized RAS users list"""
    if email.lower() in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        AUTHORIZED_RAS_USERS.discard(email.lower())
        return {"success": True, "email": email, "message": f"Access revoked for {email}"}
    raise HTTPException(status_code=404, detail="User not in authorized list")

@router.post("/admin/reset-progress/{email}")
async def reset_progress(email: str):
    """Reset all progress for a specific user (clears all completed topics)"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=404, detail="User not found in authorized list")
    
    if email in USER_PROGRESS:
        USER_PROGRESS[email] = {}
    
    return {
        "success": True, 
        "email": email, 
        "message": f"All progress has been reset for {email}",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/admin/reset-all-progress")
async def reset_all_progress():
    """Reset progress for all users (admin only)"""
    global USER_PROGRESS
    USER_PROGRESS = {}
    return {
        "success": True, 
        "message": "All user progress has been reset",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================
# PDF CONTENT INTEGRATION (Phase 2 - Future Implementation)
# ============================================================
# Placeholder for topic PDF attachments
# Topics can have PDF content attached via:
# POST /planner/admin/topic/{topic_id}/upload-pdf
# GET /planner/topic/{topic_id}/pdf

@router.get("/topic/{topic_id}/materials")
async def get_topic_materials(topic_id: str, email: str):
    """Get study materials (PDFs, notes) for a specific topic"""
    if email.lower() not in {e.lower() for e in AUTHORIZED_RAS_USERS}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find the topic
    for subject_key, subject_data in RAS_SUBJECTS.items():
        for topic in subject_data["topics"]:
            if topic["id"] == topic_id:
                return {
                    "topic_id": topic_id,
                    "topic_name": topic["name"],
                    "subject": subject_data["name"],
                    "subtopics": topic["subtopics"],
                    "note": topic.get("note", None),
                    "pdf_available": False,  # Will be True when PDFs are uploaded
                    "pdf_url": None,  # Future: S3/storage URL
                    "message": "PDF content will be available soon. Contact admin to upload study materials."
                }
    
    raise HTTPException(status_code=404, detail="Topic not found")

