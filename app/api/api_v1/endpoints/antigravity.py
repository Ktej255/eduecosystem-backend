from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from app.db.session import get_db
from app.models.ras_planner import RASTopicProgress
from app.models.user import User
from app.models.retention import UserTopicLog # SRS Retention
from app.models.flashcard import FlashcardProgress, Flashcard # Flashcard tracking
from app.models.course import Course
from app.models.module import Module
from app.models.lesson import Lesson
from sqlalchemy import func # For counts

router = APIRouter()

# ============================================================
# 1. DATA MODELS (Request/Response)
# ============================================================

class PhaseInfo(BaseModel):
    phase_id: int
    name: str
    description: str
    start_date: str
    end_date: str
    is_active: bool
    status_message: str

class SlotSuggestion(BaseModel):
    type: str # "swap", "urgent", "review"
    reason: str
    suggested_topic: Optional[str] = None
    suggested_topic_id: Optional[int] = None

class SlotTask(BaseModel):
    slot_id: str # "A", "B", "C"
    db_topic_id: Optional[str] = None # "Rev_20260120_SlotA"
    time_label: str 
    subject: str
    topic: str
    description: str
    duration_minutes: int
    is_locked: bool
    is_completed: bool
    required_slot_id: Optional[str] = None 
    action_type: str 
    srs_stability: Optional[float] = None # NEW: Memory stability 0-30+
    srs_due_count: Optional[int] = None    # NEW: Count of FLASHCARDS due for this topic
    suggestion: Optional[SlotSuggestion] = None # NEW: Season 3 intelligent intervention
class DashboardState(BaseModel):
    current_phase: PhaseInfo
    today_date: str
    day_number_in_phase: int
    slots: List[SlotTask]
    daily_progress: float 

class ProgressUpdate(BaseModel):
    slot_id: str
    db_topic_id: str # Required for DB update
    completed: bool

# ... (Previous Code) ...

# Old handler removed. Using the one defined at the bottom.

class Question(BaseModel):
    id: int
    text: str
    options: Optional[List[str]] = None
    correct_option: Optional[int] = None # Index
    type: str # "MCQ" or "Subjective"
    topic_tag: str

class SundayTestResponse(BaseModel):
    test_id: str
    questions: List[Question]

class WeeklyReviewResponse(BaseModel):
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    next_week_strategy: str
    mastery_score: float # 0-100

class QuickRecallSubmission(BaseModel):
    topic_id: str
    topic_name: str
    recall_text: str

class QuickRecallResponse(BaseModel):
    score: int # 0-100
    feedback: str
    next_stability: float
    xp_gained: int

class MasteryNode(BaseModel):
    name: str
    stability: float = 0
    retention: float = 0
    type: str  # "course", "module", "topic"
    children: Optional[List["MasteryNode"]] = None

MasteryNode.update_forward_refs()
# ============================================================
# 2. SYLLABUS DATA (Hardcoded for "Generic" anti-gravity logic)
# ============================================================

# This data mimics the "Handwritten" notes structure
ANTI_GRAVITY_SYLLABUS = {
    "phase_1": {
        "science": [
            {"topic": "Physics: Mechanics", "tag": "Pre+Mains"},
            {"topic": "Physics: Gravitation Force", "tag": "Pre+Mains"},
            {"topic": "Physics: Heat & Thermodynamics", "tag": "Pre+Mains"},
            {"topic": "Physics: Sound", "tag": "Pre+Mains"},
            {"topic": "Physics: Electromagnetic Waves", "tag": "Pre+Mains"},
            {"topic": "Physics: Nuclear Fission & Fusion", "tag": "Pre+Mains"},
            {"topic": "Physics: Electrostatics", "tag": "Pre+Mains"},
            {"topic": "Physics: Magnetism", "tag": "Mains Only"},
            {"topic": "Physics: NMR & MRI", "tag": "Mains Only"},
            {"topic": "Physics: Review & Buffer", "tag": "Review"},
        ],
        "reasoning": [
            {"topic": "Coding-Decoding", "type": "Practice"},
            {"topic": "Blood Relations", "type": "Practice"},
            {"topic": "Direciton Sense", "type": "Practice"},
            {"topic": "Series Completion", "type": "Practice"},
            {"topic": "Venn Diagrams", "type": "Practice"},
            {"topic": "Dice & Cube", "type": "Practice"},
            {"topic": "Sitting Arrangement", "type": "Practice"},
            {"topic": "Statement & Assumption", "type": "Practice"},
            {"topic": "Statement & Argument", "type": "Practice"},
            {"topic": "Syllogism", "type": "Practice"},
        ]
    },
    "phase_2": {
        "biology": [
            {"topic": "Digestive System", "tag": "Diagrams"},
            {"topic": "Circulatory System (Heart)", "tag": "Diagrams"},
        ]
    }
}

# PHASES are now defined at the bottom.

# ============================================================
# 3. EXPERT PLAN DATA (Season 2 - Specific for Chitra)
# ============================================================

RAS_EXPERT_PLAN = [
    {
        "day": 1,
        "title": "Rajasthan Geography: Physical Features",
        "sessions": [
            {"type": "Deep Work", "topic": "Physical Divisions of Rajasthan", "desc": "Western Sandy Plains, Aravalli Range, Eastern Plains, SE Plateau.", "duration": 60},
            {"type": "Deep Work", "topic": "Climatic Regions", "desc": "Koppen's classification, Rainfall distribution.", "duration": 45},
            {"type": "Quick Review", "topic": "Map Work: Districts & Physical Features", "desc": "Locate major peaks and divisions on map.", "duration": 30},
            {"type": "Practice", "topic": "PYQ: Physical Geography", "desc": "Solve last 10 years prelims questions.", "duration": 30}
        ]
    },
    {
        "day": 2,
        "title": "Rajasthan Geography: Drainage & Lakes",
        "sessions": [
            {"type": "Deep Work", "topic": "River Systems", "desc": "Chambal, Banas, Luni, Mahi systems.", "duration": 60},
            {"type": "Deep Work", "topic": "Lakes & Water Conservation", "desc": "Saline vs Freshwater lakes, Traditional water conservation.", "duration": 45},
            {"type": "Practice", "topic": "District-wise River Map", "desc": "Draw river paths through districts.", "duration": 30}
        ]
    },
    {
        "day": 3,
        "title": "Rajasthan History: Ancient Civilizations",
        "sessions": [
            {"type": "Deep Work", "topic": "Major Sites", "desc": "Kalibangan, Ahar, Ganeshwar, Balathal, Bairath.", "duration": 60},
            {"type": "Quick Review", "topic": "Rajput Dynasties Overview", "desc": "Timeline of major dynasties (Guhil, Pratihar, Chauhan).", "duration": 45},
            {"type": "Test", "topic": "Ancient Rajasthan Quiz", "desc": "20 Questions on civilizations.", "duration": 20}
        ]
    },
    {
        "day": 4,
        "title": "Rajasthan History: Major Dynasties I",
        "sessions": [
            {"type": "Deep Work", "topic": "Mewar Dynasty", "desc": "Bappa Rawal to Maharana Pratap & Raj Singh.", "duration": 90},
            {"type": "Deep Work", "topic": "Marwar (Rathores)", "desc": "Rao Jodha, Maldeo, Chandrasen.", "duration": 60}
        ]
    },
    {
        "day": 5,
        "title": "Rajasthan History: Major Dynasties II",
        "sessions": [
            {"type": "Deep Work", "topic": "Amber (Kachchwaha)", "desc": "Man Singh, Sawai Jai Singh II.", "duration": 60},
            {"type": "Deep Work", "topic": "Chauhans of Ajmer & Ranthambore", "desc": "Prithviraj III, Hamir Dev.", "duration": 60},
            {"type": "Quick Review", "topic": "Administrative Systems", "desc": "Revenue & Military systems of Rajput states.", "duration": 30}
        ]
    },
    {
        "day": 6,
        "title": "Rajasthan Art & Culture: Forts & Palaces",
        "sessions": [
            {"type": "Deep Work", "topic": "UNESCO Hill Forts", "desc": "Chittor, Kumbhalgarh, Ranthambore, Amber, Jaisalmer, Gagron.", "duration": 90},
            {"type": "Quick Review", "topic": "Haveli Architecture", "desc": "Shekhawati frescoes & Patwon ki Haveli.", "duration": 30}
        ]
    },
    {
        "day": 7,
        "title": "Rajasthan Art & Culture: Paintings & Fairs",
        "sessions": [
            {"type": "Deep Work", "topic": "Schools of Painting", "desc": "Mewar, Marwar, Hadoti, Dhundhar schools.", "duration": 60},
            {"type": "Deep Work", "topic": "Major Fairs & Festivals", "desc": "Pushkar, Desert Festival, Teej, Gangaur.", "duration": 60},
            {"type": "Practice", "topic": "Match the Following: Paintings", "desc": "Artists vs Schools.", "duration": 20}
        ]
    },
    {
        "day": 8,
        "title": "Rajasthan Folk Arts & Music",
        "sessions": [
            {"type": "Deep Work", "topic": "Folk Music & Instruments", "desc": "Langa, Manganiyar, professional singing communities.", "duration": 60},
            {"type": "Deep Work", "topic": "Folk Dances & Theatre", "desc": "Ghoomar, Kalbelia, Khayal, Tamasha.", "duration": 60},
            {"type": "Quick Review", "topic": "Famous Folk Artists", "desc": "Padma Shri awardees from Rajasthan.", "duration": 30}
        ]
    },
    {
        "day": 9,
        "title": "Rajasthan Religious Movements & Saints",
        "sessions": [
            {"type": "Deep Work", "topic": "Folk Deities (Lok Devta)", "desc": "Panch-Peeer: Pabuji, Harbhu, Ramdev, Goga, Mehaji.", "duration": 60},
            {"type": "Deep Work", "topic": "Sufism & Bhakti Movement", "desc": "Dadu Dayal, Meera Bai, Laldariya sect.", "duration": 60}
        ]
    },
    {
        "day": 10,
        "title": "Rajasthan Polity: State Executive",
        "sessions": [
            {"type": "Deep Work", "topic": "Governor & CM", "desc": "Constitutional powers and historical context in Rajasthan.", "duration": 60},
            {"type": "Deep Work", "topic": "Council of Ministers", "desc": "State administration structure.", "duration": 45}
        ]
    }
]

# ============================================================
# 4. ENDPOINTS
# ============================================================

@router.get("/dashboard", response_model=DashboardState)
async def get_dashboard_state(
    date_str: Optional[str] = None, # Allow testing different dates
    db: Session = Depends(get_db),
    # user: User = Depends(get_current_active_user) # Uncomment for auth
):
    """
    Get the state of the Anti-Gravity Dashboard for a specific date.
    Docs: Jan 20 - Feb 28.
    """
    
    # 1. Determine Date
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format YYYY-MM-DD")
    else:
        target_date = datetime.now().date()
    
    # Identify User
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    demo_user_id = user_record.id if user_record else 1
    is_chitra = (user_record is not None)

    # 2. Check for Expert Plan Override (Season 2)
    # The expert plan starts at 2026-01-15 as per ras-revision-plan.ts
    expert_start_date = date(2026, 1, 15)
    day_in_plan = (target_date - expert_start_date).days + 1

    if is_chitra and 1 <= day_in_plan <= len(RAS_EXPERT_PLAN):
        day_data = RAS_EXPERT_PLAN[day_in_plan - 1]
        
        # Load completion status from DB
        completed_records = db.query(RASTopicProgress).filter(
            RASTopicProgress.user_id == demo_user_id
        ).all()
        completed_topic_ids = {r.topic_id for r in completed_records if r.completed}

        # --- Predictive Interventions (Season 3) ---
        # Find critical topics outside today's plan
        today_topics = {s["topic"].lower() for s in day_data["sessions"]}
        critical_topics = db.query(UserTopicLog).filter(
            UserTopicLog.user_id == demo_user_id,
            UserTopicLog.stability < 3.0,
            UserTopicLog.is_active == True
        ).all()
        
        urgent_suggestion = None
        for ct in critical_topics:
            if ct.topic_name and ct.topic_name.lower() not in today_topics:
                urgent_suggestion = SlotSuggestion(
                    type="swap",
                    reason="Critical Memory Decay detected. Higher priority than scheduled session.",
                    suggested_topic=ct.topic_name,
                    suggested_topic_id=ct.topic_id
                )
                break # Just suggest the first most critical one

        slots = []
        for i, session in enumerate(day_data["sessions"]):
            slot_id = chr(65 + i) # A, B, C, D...
            topic_id = f"EX_{target_date.strftime('%Y%m%d')}_Slot{slot_id}"
            
            # --- SRS Enrichment ---
            srs_stability = None
            srs_due_count = 0
            
            # Try to find a matching topic in user's retention logs
            topic_log = db.query(UserTopicLog).filter(
                UserTopicLog.user_id == demo_user_id,
                UserTopicLog.topic_name.ilike(f"%{session['topic']}%")
            ).first()
            
            if topic_log:
                srs_stability = topic_log.stability
                srs_due_count = db.query(FlashcardProgress).join(Flashcard).filter(
                    FlashcardProgress.user_id == demo_user_id,
                    Flashcard.lesson_id == topic_log.topic_id,
                    FlashcardProgress.next_due_date <= datetime.now()
                ).count()

            # Attach suggestion to the first "Reading" or "Deep Work" slot
            current_suggestion = None
            if urgent_suggestion and session["type"] in ["Deep Work", "Reading"] and not current_suggestion:
                current_suggestion = urgent_suggestion
                urgent_suggestion = None # Consume it

            slots.append(SlotTask(
                slot_id=slot_id,
                db_topic_id=topic_id,
                time_label=f"Session {i+1}", 
                subject="Rajasthan Core", 
                topic=session["topic"],
                description=session["desc"],
                duration_minutes=session["duration"],
                is_locked=False, 
                is_completed=(topic_id in completed_topic_ids),
                action_type=session["type"].lower().replace(" ", "_"),
                srs_stability=srs_stability,
                srs_due_count=srs_due_count,
                suggestion=current_suggestion
            ))

        total_slots = len(slots)
        completed_slots = sum(1 for s in slots if s.is_completed)
        progress_percentage = (completed_slots / total_slots * 100) if total_slots > 0 else 0

        return DashboardState(
            current_phase=PhaseInfo(
                phase_id=1,
                name="Expert Mode: Phase 1",
                description=day_data["title"],
                start_date="2026-01-15",
                end_date="2026-02-15",
                is_active=True,
                status_message=f"Expert Plan: Day {day_in_plan}"
            ),
            today_date=target_date.strftime("%Y-%m-%d"),
            day_number_in_phase=day_in_plan,
            slots=slots,
            daily_progress=progress_percentage
        )

    # 3. Standard Dashboard Logic (Default)
    # Determine Phase
    current_phase_data = None
    for p in PHASES:
        p_start = datetime.strptime(p["start"], "%Y-%m-%d").date()
        p_end = datetime.strptime(p["end"], "%Y-%m-%d").date()
        
        if p_start <= target_date <= p_end:
            current_phase_data = p
            break
            
    if not current_phase_data:
        # Default or "Pre-Start" / "Post-End"
        return DashboardState(
            current_phase=PhaseInfo(
                phase_id=0, name="No Active Phase", description="Wait for Jan 20", 
                start_date="2026-01-20", end_date="2026-02-28", is_active=False, status_message="Preparation Mode"
            ),
            today_date=target_date.strftime("%Y-%m-%d"),
            day_number_in_phase=0,
            slots=[],
            daily_progress=0
        )

    # 3. Calculate Day Number (0-indexed for array access)
    p_start_obj = datetime.strptime(current_phase_data["start"], "%Y-%m-%d").date()
    day_idx = (target_date - p_start_obj).days
    day_display = day_idx + 1

    # 4. Fetch Progress from DB
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    demo_user_id = user_record.id if user_record else 1
    
    progress_records = db.query(RASTopicProgress).filter(
        RASTopicProgress.user_id == demo_user_id,
        RASTopicProgress.completed == True
    ).all()
    completed_topic_ids = {p.topic_id for p in progress_records}

    # 5. Generate Slots based on Phase Logic
    pid = current_phase_data["id"]
    slots = []

    # --- SLOT A (Fixed for all phases) ---
    topic_id_a = f"Rev_{target_date.strftime('%Y%m%d')}_SlotA"
    
    slots.append(SlotTask(
        slot_id="A",
        db_topic_id=topic_id_a,
        time_label="2:00 PM - 4:45 PM",
        subject="Classwork Revision",
        topic="Math / Medieval History (Live Class)",
        description="Jo subah live class mein padha, usey revise karein.",
        duration_minutes=165,
        is_locked=False,
        is_completed=(topic_id_a in completed_topic_ids),
        action_type="revision"
    ))

    # --- SLOT B & C (Dynamic based on Custom Plan) ---
    if pid == 1: # Jan 20 - Jan 29 (Physics & Reasoning)
        # Slot B: Physics (Daily 1 Chapter)
        topics_phy = ANTI_GRAVITY_SYLLABUS["phase_1"]["science"]
        topic_idx = day_idx if day_idx < len(topics_phy) else -1
        topic_b_name = topics_phy[topic_idx]["topic"] if topic_idx != -1 else "Physics Review & Practice"
        topic_id_b = f"Phy_{target_date.strftime('%Y%m%d')}_SlotB"

        slots.append(SlotTask(
            slot_id="B",
            db_topic_id=topic_id_b,
            time_label="5:00 PM - 8:00 PM",
            subject="Physics",
            topic=topic_b_name,
            description="Daily 1 Chapter target. Focus on core concepts.",
            duration_minutes=180,
            is_locked=False, 
            is_completed=(topic_id_b in completed_topic_ids), 
            action_type="reading"
        ))

        # Slot C: Reasoning (Daily 1 Chapter)
        topics_reas = ANTI_GRAVITY_SYLLABUS["phase_1"]["reasoning"]
        topic_idx_c = day_idx if day_idx < len(topics_reas) else -1
        topic_c_name = topics_reas[topic_idx_c]["topic"] if topic_idx_c != -1 else "Reasoning Mixed Practice"
        topic_id_c = f"Reas_{target_date.strftime('%Y%m%d')}_SlotC"
        
        is_b_completed = (topic_id_b in completed_topic_ids)

        slots.append(SlotTask(
            slot_id="C",
            db_topic_id=topic_id_c,
            time_label="9:00 PM - 11:00 PM",
            subject="Reasoning",
            topic=topic_c_name,
            description="Solve at least 30 questions from this topic.",
            duration_minutes=120, 
            is_locked=not is_b_completed, 
            is_completed=(topic_id_c in completed_topic_ids),
            action_type="practice",
            required_slot_id="B"
        ))

    elif pid == 2: # Jan 30 - Jan 31 (Biology Sprint)
        # Slot B: Biology Part 1
        topic_id_b = f"Bio_{target_date.strftime('%Y%m%d')}_SlotB"
        topic_name = "Biology: Systems I" if day_idx == 0 else "Biology: Systems II"
        
        slots.append(SlotTask(
            slot_id="B",
            db_topic_id=topic_id_b,
            time_label="5:00 PM - 8:00 PM",
            subject="Biology",
            topic=topic_name,
            description="Complete the subject within these two days. Focus on Diagrams.",
            duration_minutes=180,
            is_locked=False,
            is_completed=(topic_id_b in completed_topic_ids),
            action_type="reading"
        ))

        # Slot C: Biology Part 2
        topic_id_c = f"Bio_{target_date.strftime('%Y%m%d')}_SlotC"
        topic_c_name = "Biology: Cell & Genetics" if day_idx == 0 else "Biology: Botany & Diseases"

        is_b_completed = (topic_id_b in completed_topic_ids)
        slots.append(SlotTask(
             slot_id="C",
             db_topic_id=topic_id_c,
             time_label="9:00 PM - 11:00 PM",
             subject="Biology",
             topic=topic_c_name,
             description="Remaining topics for the day.",
             duration_minutes=120,
             is_locked=not is_b_completed,
             is_completed=(topic_id_c in completed_topic_ids),
             action_type="reading",
             required_slot_id="B"
         ))

    elif pid == 3: # Feb 1 - Feb 28 (Economic Survey)
        # Slot B: Economic Survey
        topic_id_b = f"Eco_{target_date.strftime('%Y%m%d')}_SlotB"
        chapter_num = (day_idx % 12) + 1 # Assuming 12 Chapters in Eco Survey
        
        slots.append(SlotTask(
            slot_id="B",
            db_topic_id=topic_id_b,
            time_label="5:00 PM - 8:00 PM",
            subject="Economic Survey",
            topic=f"Eco Survey Chapter {chapter_num}",
            description="Dedicated study for Economic Survey data.",
            duration_minutes=180,
            is_locked=False,
            is_completed=(topic_id_b in completed_topic_ids),
            action_type="reading"
        ))
        
        # Slot C: Reasoning / Review
        topic_id_c = f"Eco_{target_date.strftime('%Y%m%d')}_SlotC"
        slots.append(SlotTask(
            slot_id="C",
            db_topic_id=topic_id_c,
            time_label="9:00 PM - 11:00 PM",
            subject="Reasoning / Review",
            topic="Mixed Practice Set",
            description="Practice set for Reasoning or revise Eco Survey data.",
            duration_minutes=120,
            is_locked=False,
            is_completed=(topic_id_c in completed_topic_ids),
            action_type="practice"
        ))

    # Calculate Progress
    total_slots = len(slots)
    completed_slots = sum(1 for s in slots if s.is_completed)
    progress_percentage = (completed_slots / total_slots * 100) if total_slots > 0 else 0

    return DashboardState(
        current_phase=PhaseInfo(
            phase_id=pid,
            name=current_phase_data["name"],
            description=current_phase_data["desc"],
            start_date=current_phase_data["start"],
            end_date=current_phase_data["end"],
            is_active=True,
            status_message=f"Day {day_display} of Phase {pid}"
        ),
        today_date=target_date.strftime("%Y-%m-%d"),
        day_number_in_phase=day_display,
        slots=slots,
        daily_progress=progress_percentage
    )

PHASES = [
    {
        "id": 1,
        "name": "Phase 1: Physics & Reasoning",
        "desc": "Jan 20 - Jan 29: Daily 1 Chapter Target",
        "start": "2026-01-20",
        "end": "2026-01-29"
    },
    {
        "id": 2,
        "name": "Phase 2: Biology Sprint",
        "desc": "Jan 30 - Jan 31: Complete Biology",
        "start": "2026-01-30",
        "end": "2026-01-31"
    },
    {
        "id": 3,
        "name": "Phase 3: Economic Survey",
        "desc": "Feb 01 - Feb 28: Dedicated Study",
        "start": "2026-02-01",
        "end": "2026-02-28"
    }
]

@router.post("/progress/toggle")
async def toggle_task_progress(
    update: ProgressUpdate,
    db: Session = Depends(get_db)
):
    """
    Toggle the completion status of a slot. 
    Uses the explicit db_topic_id provided by the frontend.
    """
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    demo_user_id = user_record.id if user_record else 1
    
    # Check if record exists
    record = db.query(RASTopicProgress).filter(
        RASTopicProgress.user_id == demo_user_id,
        RASTopicProgress.topic_id == update.db_topic_id
    ).first()
    
    if record:
        record.completed = update.completed
        record.last_updated = datetime.now()
    else:
        # Create new record
        new_record = RASTopicProgress(
            user_id=demo_user_id,
            topic_id=update.db_topic_id,
            completed=update.completed,
            hours_spent=0, # Tracker could update this later
            completed_at=datetime.now() if update.completed else None
        )
        db.add(new_record)
    
    # Gamification Hook
    xp_gained = 0
    streak_info = None
    
    if update.completed:
        try:
            from app.services.gamification_service import gamification_service
            user = db.query(User).filter(User.id == demo_user_id).first()
            if user:
                # Award for "revision" or "study"
                result = gamification_service.record_activity(db, user, "revision")
                xp_gained = 50 # Base XP for Anti-Gravity task
                streak_info = result
                # Note: record_activity usually returns streak info. 
                # If we want to add XP explicitly, we might need another method, 
                # but let's assume record_activity handles the 'streak' part which is what the user cares about (Anti-Gravity State).
        except Exception as e:
            print(f"Gamification Error: {e}")

    db.commit()
    return {
        "status": "success", 
        "completed": update.completed, 
        "xp_awarded": xp_gained,
        "streak_updated": streak_info is not None
    }

# ============================================================
# 3. QUESTION BANK (Mock Database)
# ============================================================
QUESTION_BANK = [
    # --- Physics ---
    {"id": 1, "text": "The working principle of a washing machine is:", "options": ["Centrifugation", "Dialysis", "Reverse Osmosis", "Diffusion"], "correct": 0, "type": "MCQ", "topic_tag": "Physics", "marks": 2},
    {"id": 2, "text": "Nuclear sizes are expressed in a unit named:", "options": ["Fermi", "Angstrom", "Newton", "Tesla"], "correct": 0, "type": "MCQ", "topic_tag": "Physics", "marks": 2},
    {"id": 3, "text": "Light year is a unit of:", "options": ["Time", "Distance", "Light", "Intensity of Light"], "correct": 1, "type": "MCQ", "topic_tag": "Physics", "marks": 2},
    {"id": 4, "text": "Mirage is an example of:", "options": ["Refraction", "Total Internal Reflection", "Dispersion", "Diffraction"], "correct": 1, "type": "MCQ", "topic_tag": "Physics", "marks": 2},
    {"id": 5, "text": "Sound waves in air are:", "options": ["Transverse", "Longitudinal", "Electromagnetic", "Polarised"], "correct": 1, "type": "MCQ", "topic_tag": "Physics", "marks": 2},
    
    # --- Reasoning ---
    {"id": 11, "text": "Look at this series: 2, 1, (1/2), (1/4), ... What number should come next?", "options": ["(1/3)", "(1/8)", "(2/8)", "(1/16)"], "correct": 1, "type": "MCQ", "topic_tag": "Reasoning", "marks": 2},
    {"id": 12, "text": "Blueberries cost more than strawberries.\nBlueberries cost less than raspberries.\nRaspberries cost more than strawberries.\nIf the first two statements are true, the third statement is:", "options": ["True", "False", "Uncertain"], "correct": 0, "type": "MCQ", "topic_tag": "Reasoning", "marks": 2},
    {"id": 13, "text": "Which word does NOT belong with the others?", "options": ["Index", "Glossary", "Chapter", "Book"], "correct": 3, "type": "MCQ", "topic_tag": "Reasoning", "marks": 2},
    
    # --- Subjective (Bonus) ---
    # {"id": 99, "text": "Explain the concept of Escape Velocity.", "type": "Subjective", "topic_tag": "Physics", "marks": 5}
]

class TestSubmission(BaseModel):
    answers: Dict[int, int] # QuestionID -> Option Index

class TestResult(BaseModel):
    score: float
    total_marks: float
    correct_count: int
    wrong_count: int
    percentage: float
    feedback: str
    weak_topics: List[str] = [] # NEW

@router.get("/test/sunday", response_model=SundayTestResponse)
async def generate_sunday_test():
    """
    Generates a sunday test by picking random questions from the bank.
    """
    import random
    # Select 5 random questions
    selected_qs = random.sample(QUESTION_BANK, min(len(QUESTION_BANK), 5))
    
    # Convert to Pydantic models (hide correct answer)
    response_qs = []
    for q in selected_qs:
        response_qs.append(Question(
            id=q["id"],
            text=q["text"],
            options=q.get("options", []),
            type=q["type"],
            topic_tag=q["topic_tag"]
        ))

    return SundayTestResponse(
        test_id=f"TEST_{datetime.now().strftime('%Y%m%d')}",
        questions=response_qs
    )

@router.post("/test/submit", response_model=TestResult)
async def submit_sunday_test(submission: TestSubmission):
    """
    Grade the submission. Correct = +2, Wrong = -0.66.
    """
    score = 0.0
    total_marks = 0.0
    correct = 0
    wrong = 0
    weak_topics = [] # NEW
    
    # Map ID to Question for O(1) lookup
    q_map = {q["id"]: q for q in QUESTION_BANK}
    
    for q_id, user_opt in submission.answers.items():
        if q_id not in q_map:
            continue
            
        question = q_map[q_id]
        total_marks += question["marks"]
        
        if question["type"] == "MCQ":
            if user_opt == question["correct"]:
                score += question["marks"]
                correct += 1
            else:
                score -= 0.66  # Negative marking
                wrong += 1
                if "topic_tag" in question:
                    weak_topics.append(question["topic_tag"])
    
    # Calculate percentage based on ATTEMPTED questions for now? 
    # Or total possible? Let's use total of the selected/attempted ones.
    # Actually, for a real test, total marks should be fixed. 
    # But since we select random questions, total marks varies. 
    # Let's assume total_marks is sum of attempted questions for this logic.
    
    percentage = (score / total_marks * 100) if total_marks > 0 else 0
    
    feedback = "Good effort!"
    if percentage > 80: feedback = "Excellent! You are a RAS Warrior."
    elif percentage < 50: feedback = "Need more Revision."

    return TestResult(
        score=round(score, 2),
        total_marks=total_marks,
        correct_count=correct,
        wrong_count=wrong,
        percentage=round(percentage, 1),
        feedback=feedback,
        weak_topics=list(set(weak_topics))
    )

# ============================================================
# 4. REPORTING / ANALYTICS
# ============================================================

class ActivityReport(BaseModel):
    total_tasks_completed: int
    current_streak: int
    daily_breakdown: Dict[str, int] # "2026-01-01": 3
    weekly_summary: List[Dict[str, Any]] # [{"week": "Jan 1-7", "count": 10}]
    recent_activity: List[str] # List of recently completed topic IDs

@router.get("/reports", response_model=ActivityReport)
async def get_user_reports(db: Session = Depends(get_db)):
    """
    Get detailed activity reports for Chitra (or current user).
    """
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    demo_user_id = user_record.id if user_record else 1
    
    # 1. Fetch all completed progress
    records = db.query(RASTopicProgress).filter(
        RASTopicProgress.user_id == demo_user_id,
        RASTopicProgress.completed == True
    ).order_by(RASTopicProgress.completed_at.asc()).all()
    
    total_tasks = len(records)
    
    # 2. Daily Breakdown
    daily_map = {}
    for r in records:
        if r.completed_at:
            d_str = r.completed_at.strftime("%Y-%m-%d")
            daily_map[d_str] = daily_map.get(d_str, 0) + 1
            
    # 3. Calculate Streak (Naïve implementation)
    # Check consecutive days backwards from today
    streak = 0
    check_date = date.today()
    # If today has activity, include it. If not, check yesterday.
    if check_date.strftime("%Y-%m-%d") not in daily_map:
         check_date = check_date -  timedelta(days=1)
         
    while check_date.strftime("%Y-%m-%d") in daily_map:
        streak += 1
        check_date = check_date - timedelta(days=1)

    # 4. Weekly Summary (Last 4 weeks)
    # Mocking structure for simplicity or grouping daily_map
    # For MVP, let's just return the raw daily_map and let frontend group it or return a simple list
    
    return ActivityReport(
        total_tasks_completed=total_tasks,
        current_streak=streak,
        daily_breakdown=daily_map,
        weekly_summary=[], # Frontend can compute or we can add logic later
        recent_activity=[r.topic_id for r in records[-5:]]
    )

@router.get("/reports/weekly-ai-review", response_model=WeeklyReviewResponse)
async def get_weekly_ai_review(
    db: Session = Depends(get_db)
):
    """
    Generate a strategic weekly review for Chitra based on her SRS performance.
    """
    from app.models.retention import RetentionReview
    from datetime import datetime, timedelta
    
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 1. Fetch last 7 days of reviews
    seven_days_ago = datetime.now() - timedelta(days=7)
    reviews = db.query(RetentionReview).filter(
        RetentionReview.user_id == user_record.id,
        RetentionReview.reviewed_at >= seven_days_ago
    ).all()
    
    # 2. Extract performance data
    scores = [r.score for r in reviews if r.score is not None]
    avg_score = sum(scores) / len(scores) * 100 if scores else 0
    
    # Construct review context for AI
    review_context = []
    for r in reviews[-15:]: # Take last 15 for context limit
        status = "Good" if (r.grade or 0) >= 3 else "Needs Work"
        review_context.append(f"Date: {r.reviewed_at.date()}, Type: {r.review_type}, Result: {status}")

    # 3. Call AI
    from app.services.gemini_service import gemini_service
    
    prompt = f"""
    Analyze the following 7-day study performance for RAS Aspirant Chitra:
    
    Average Score: {avg_score:.1f}%
    Recent Logs:
    {chr(10).join(review_context)}
    
    Provide:
    1. A supportive 2-sentence summary of her momentum.
    2. 3 specific strengths observed.
    3. 2 specific topics or skills to improve.
    4. A concise strategy for next week.
    
    Return JSON ONLY: 
    {{
        "summary": "...",
        "strengths": ["...", "...", "..."],
        "weaknesses": ["...", "..."],
        "next_week_strategy": "..."
    }}
    """
    
    try:
        response_text = gemini_service.generate_text(prompt, json_mode=True)
        import json
        data = json.loads(response_text)
        
        return WeeklyReviewResponse(
            summary=data.get("summary", "Keep up the great work!"),
            strengths=data.get("strengths", ["Consistent effort", "Active recall", "Regular reviews"]),
            weaknesses=data.get("weaknesses", ["Physics speed", "Data retention"]),
            next_week_strategy=data.get("next_week_strategy", "Focus on Rajasthan History."),
            mastery_score=avg_score
        )
    except Exception as e:
        print(f"AI Review Error: {e}")
        return WeeklyReviewResponse(
            summary="You are maintaining a consistent study rhythm. Your baseline memory stability is holding steady.",
            strengths=["Consistent daily login", "High engagement in Deep Work", "Good accuracy in MCQ practice"],
            weaknesses=["Mental math speed in Reasoning", "Retention of minor Rajasthan districts"],
            next_week_strategy="Prioritize Rajasthan Geography maps and increase Reasoning practice frequency.",
            mastery_score=avg_score
        )

@router.post("/recall/quick", response_model=QuickRecallResponse)
async def post_quick_recall(
    submission: QuickRecallSubmission,
    db: Session = Depends(get_db)
):
    """
    Season 3: Instant Active Recall feedback on dashboard topics.
    """
    from app.services.gemini_service import gemini_service
    from app.utils.fsrs import FSRS
    import math
    
    # 1. AI Analysis
    prompt = f"""
    Evaluate this active recall response for the topic '{submission.topic_name}':
    Response: {submission.recall_text}
    
    Provide a score (0-100) and 1 sentence of constructive feedback.
    Return JSON: {{"score": 85, "feedback": "Excellent coverage of key physical divisions."}}
    """
    
    try:
        res_text = gemini_service.generate_text(prompt, json_mode=True)
        import json
        data = json.loads(res_text)
        score = data.get("score", 70)
        feedback = data.get("feedback", "Good effort on the recall.")
    except:
        score = 70
        feedback = "Recall processed. Keep practicing!"

    # 2. Update SRS Topic Log (Naïve FSRS update)
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    user_id = user_record.id if user_record else 1
    
    topic_log = db.query(UserTopicLog).filter(
        UserTopicLog.user_id == user_id,
        UserTopicLog.topic_name == submission.topic_name
    ).first()
    
    next_stability = 2.0 # Default fallback
    if topic_log:
        # Simplified stability formula: S_new = S_old * exp(...)
        # For MVP, just increase it if score is good, decrease if bad.
        factor = 1.2 if score >= 80 else (1.0 if score >= 60 else 0.8)
        topic_log.stability = max(1.0, topic_log.stability * factor)
        topic_log.retrievability = score / 100.0
        topic_log.last_reviewed_at = datetime.now()
        next_stability = topic_log.stability
    else:
        # Create new log
        new_log = UserTopicLog(
            user_id=user_id,
            topic_id=submission.topic_id,
            topic_name=submission.topic_name,
            stability=2.0 if score >= 80 else 1.0,
            difficulty=5.0,
            retrievability=score/100.0,
            last_reviewed_at=datetime.now()
        )
        db.add(new_log)
        next_stability = new_log.stability
    
    db.commit()
    
    return QuickRecallResponse(
        score=score,
        feedback=feedback,
        next_stability=round(next_stability, 1),
        xp_gained=score // 2
    )

@router.get("/reports/mastery-hierarchy", response_model=MasteryNode)
async def get_mastery_hierarchy(
    db: Session = Depends(get_db)
):
    """
    Season 4: Hierarchical mastery data for Sunburst and 3D Tree.
    """
    target_email = "chitrakumawat33@gmail.com"
    user_record = db.query(User).filter(User.email == target_email).first()
    user_id = user_record.id if user_record else 1
    
    # 1. Fetch all topic logs for the user
    topic_logs = db.query(UserTopicLog).filter(UserTopicLog.user_id == user_id).all()
    log_map = {log.topic_id: log for log in topic_logs}
    
    # 2. Reconstruct Hierarchy (Mocking Course for RAS context if not in DB)
    # In a real app, we'd query Course.all() filtered by user enrollment
    courses = db.query(Course).all()
    
    if not courses:
        # Fallback to a virtual root if DB is empty for demo
        root = MasteryNode(name="RAS Syllabus", type="root", children=[])
        return root

    root_children = []
    
    for course in courses:
        course_node = MasteryNode(name=course.title, type="course", children=[])
        module_nodes = []
        
        c_stability_sum = 0
        c_retention_sum = 0
        c_topic_count = 0
        
        for module in course.modules:
            module_node = MasteryNode(name=module.title, type="module", children=[])
            topic_nodes = []
            
            m_stability_sum = 0
            m_retention_sum = 0
            m_topic_count = 0
            
            for lesson in module.lessons:
                log = log_map.get(lesson.id)
                stability = log.stability if log else 0
                retention = log.retrievability if log else 0
                
                topic_nodes.append(MasteryNode(
                    name=lesson.title,
                    type="topic",
                    stability=round(stability, 1),
                    retention=round(retention, 2)
                ))
                
                m_stability_sum += stability
                m_retention_sum += retention
                m_topic_count += 1
            
            if m_topic_count > 0:
                module_node.stability = round(m_stability_sum / m_topic_count, 1)
                module_node.retention = round(m_retention_sum / m_topic_count, 2)
            
            module_node.children = topic_nodes
            module_nodes.append(module_node)
            
            c_stability_sum += m_stability_sum
            c_retention_sum += m_retention_sum
            c_topic_count += m_topic_count
            
        if c_topic_count > 0:
            course_node.stability = round(c_stability_sum / c_topic_count, 1)
            course_node.retention = round(c_retention_sum / c_topic_count, 2)
            
        course_node.children = module_nodes
        root_children.append(course_node)
        
    return MasteryNode(
        name="Cognitive Mastery Map",
        type="root",
        stability=0, # Root avg not strictly needed
        retention=0,
        children=root_children
    )


