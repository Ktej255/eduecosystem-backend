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
# RAS SYLLABUS DATA
# ============================================================
RAS_SUBJECTS = {
    "history_rajasthan": {
        "name": "History of Rajasthan",
        "priority": "high",
        "topics": [
            {"id": "hr_01", "name": "Pre-Historic Rajasthan", "subtopics": ["Paleolithic", "Mesolithic", "Chalcolithic sites"]},
            {"id": "hr_02", "name": "Rajput Dynasties", "subtopics": ["Chauhans", "Rathores", "Sisodias", "Kachwahas"]},
            {"id": "hr_03", "name": "Medieval Rajasthan", "subtopics": ["Delhi Sultanate", "Mughal Relations", "Marathas"]},
            {"id": "hr_04", "name": "1857 Revolt in Rajasthan", "subtopics": ["Causes", "Leaders", "Aftermath"]},
            {"id": "hr_05", "name": "Formation of Rajasthan", "subtopics": ["Integration phases", "Key personalities"]},
        ]
    },
    "geography_rajasthan": {
        "name": "Geography of Rajasthan",
        "priority": "high",
        "topics": [
            {"id": "gr_01", "name": "Physical Features", "subtopics": ["Aravalli", "Thar Desert", "Rivers"]},
            {"id": "gr_02", "name": "Climate", "subtopics": ["Monsoon patterns", "Droughts", "Climate zones"]},
            {"id": "gr_03", "name": "Minerals & Resources", "subtopics": ["Mining industry", "Major minerals", "Energy resources"]},
            {"id": "gr_04", "name": "Agriculture", "subtopics": ["Cropping patterns", "Irrigation", "Land reforms"]},
            {"id": "gr_05", "name": "Wildlife & Environment", "subtopics": ["National Parks", "Sanctuaries", "Conservation"]},
        ]
    },
    "polity_rajasthan": {
        "name": "Polity & Governance",
        "priority": "high",
        "topics": [
            {"id": "pr_01", "name": "Constitutional Provisions", "subtopics": ["Governor", "CM", "State Legislature"]},
            {"id": "pr_02", "name": "Panchayati Raj", "subtopics": ["73rd Amendment", "3-tier structure", "Rajasthan PR Act"]},
            {"id": "pr_03", "name": "Urban Governance", "subtopics": ["Municipalities", "74th Amendment", "Smart Cities"]},
            {"id": "pr_04", "name": "State Administration", "subtopics": ["Secretariat", "Districts", "Divisions"]},
            {"id": "pr_05", "name": "Judiciary", "subtopics": ["High Court", "District Courts", "Lok Adalat"]},
        ]
    },
    "economy_rajasthan": {
        "name": "Economy of Rajasthan",
        "priority": "medium",
        "topics": [
            {"id": "er_01", "name": "Economic Overview", "subtopics": ["GSDP", "Per capita income", "Growth trends"]},
            {"id": "er_02", "name": "Industries", "subtopics": ["Textile", "Tourism", "Handicrafts", "IT"]},
            {"id": "er_03", "name": "Infrastructure", "subtopics": ["Roads", "Railways", "Airports", "Power"]},
            {"id": "er_04", "name": "Budget & Finance", "subtopics": ["State budget", "Revenue sources", "Expenditure"]},
            {"id": "er_05", "name": "Welfare Schemes", "subtopics": ["Social security", "Employment", "Health schemes"]},
        ]
    },
    "culture_rajasthan": {
        "name": "Art, Culture & Heritage",
        "priority": "medium",
        "topics": [
            {"id": "cr_01", "name": "Folk Arts", "subtopics": ["Ghoomar", "Kalbeliya", "Puppetry", "Music"]},
            {"id": "cr_02", "name": "Fairs & Festivals", "subtopics": ["Pushkar", "Desert Festival", "Gangaur"]},
            {"id": "cr_03", "name": "Architecture", "subtopics": ["Forts", "Palaces", "Temples", "Havelis"]},
            {"id": "cr_04", "name": "Handicrafts", "subtopics": ["Pottery", "Textiles", "Jewelry", "Paintings"]},
            {"id": "cr_05", "name": "Literature & Saints", "subtopics": ["Meerabai", "Dadu", "Rajasthani literature"]},
        ]
    },
    "current_affairs": {
        "name": "Current Affairs & GK",
        "priority": "high",
        "topics": [
            {"id": "ca_01", "name": "Recent Government Schemes", "subtopics": ["2024-25 schemes", "Budget highlights"]},
            {"id": "ca_02", "name": "Awards & Personalities", "subtopics": ["State awards", "Notable personalities"]},
            {"id": "ca_03", "name": "Sports & Events", "subtopics": ["Rajasthan in sports", "Major events"]},
            {"id": "ca_04", "name": "Environmental Issues", "subtopics": ["Water crisis", "Pollution", "Conservation efforts"]},
            {"id": "ca_05", "name": "Development Projects", "subtopics": ["ERCP", "RUIDP", "Connectivity projects"]},
        ]
    }
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
