from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.polity import PolityChapterTask, ChapterStatus
from app.db.session import SessionLocal

router = APIRouter()

# --- Pydantic Schemas ---

class PolityChapterTaskBase(BaseModel):
    research_done: Optional[bool] = None
    report_generated: Optional[bool] = None
    report_saved: Optional[bool] = None
    video_generated: Optional[bool] = None
    podcast_generated: Optional[bool] = None
    status: Optional[ChapterStatus] = None

class PolityChapterTaskUpdate(PolityChapterTaskBase):
    pass

class PolityChapterTaskOut(PolityChapterTaskBase):
    id: int
    chapter_number: int
    chapter_title: str = ""
    updated_at: Optional[str] = None # Will be datetime in real response, Pydantic handles coercion

    class Config:
        orm_mode = True

# --- API Endpoints ---

@router.get("/tasks", response_model=List[PolityChapterTaskOut])
def get_tasks(
    db: Session = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_user), # Uncomment to secure
):
    """
    Get all polity chapter tasks.
    """
    tasks = db.query(PolityChapterTask).order_by(PolityChapterTask.chapter_number).all()
    return tasks

@router.patch("/tasks/{task_id}", response_model=PolityChapterTaskOut)
def update_task(
    task_id: int,
    task_in: PolityChapterTaskUpdate,
    db: Session = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_user), # Uncomment to secure
):
    """
    Update a polity chapter task.
    """
    task = db.query(PolityChapterTask).filter(PolityChapterTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.dict(exclude_unset=True)
    
    # Update fields
    for field, value in update_data.items():
        setattr(task, field, value)

    # Auto-update status logic (optional helper)
    # If all 5 boolean flags are True -> Completed.
    # If at least 1 is True and not all -> In Progress.
    if (task.research_done and task.report_generated and task.report_saved 
        and task.video_generated and task.podcast_generated):
        task.status = ChapterStatus.COMPLETED
    elif (task.research_done or task.report_generated or task.report_saved 
          or task.video_generated or task.podcast_generated):
        task.status = ChapterStatus.IN_PROGRESS
    # Else status remains as is (or pending if we wanted to enforce it)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.post("/seed", response_model=List[PolityChapterTaskOut])
def seed_tasks(
    db: Session = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_superuser), # Secure this!
):
    """
    Seeding endpoint to populate the 95 chapters if they don't exist.
    """
    # Quick check if empty
    count = db.query(PolityChapterTask).count()
    if count > 0:
        return db.query(PolityChapterTask).order_by(PolityChapterTask.chapter_number).all()
        
    # Hardcoded list of chapters (Derived from frontend polity-types-95.ts)
    # Ideally I'd share this data, but for now I'll paste the list of IDs/Titles here or in a separate file.
    # For brevity, I will include a placeholder list and update it with the full 95 list in a subsequent step 
    # if the file is too large, or I'll try to write it all now.
    
    # To save tokens/time, I will just reference the fact I need to import the data. 
    # But since I can't import TS into Python easily, I will copy-paste the data structure.
    
    # ... (I will construct the list in the next step to avoid massive token usage in one single tool call if possible, 
    # but `write_to_file` handles large content well. I'll include the seeding logic with the full list).
    
    # NOTE: I will return empty for now and let the user populate or use a separate script, 
    # OR better yet, I will write a separate `seed_polity.py` script or include the data here.
    # Let's include the data here.
    
    chapters_data = [
        (1, 'Historical Background'), (2, 'Making of the Constitution'), (3, 'Concept of the Constitution'), (4, 'Salient Features of the Constitution'), (5, 'Preamble of the Constitution'), (6, 'Union and its Territory'), (7, 'Citizenship'), (8, 'Fundamental Rights'), (9, 'Directive Principles of State Policy'), (10, 'Fundamental Duties'), (11, 'Amendment of the Constitution'), (12, 'Basic Structure of the Constitution'),
        (13, 'Parliamentary System'), (14, 'Federal System'), (15, 'Centre–State Relations'), (16, 'Inter-State Relations'), (17, 'Emergency Provisions'),
        (18, 'President'), (19, 'Vice-President'), (20, 'Prime Minister'), (21, 'Central Council of Ministers'), (22, 'Cabinet Committees'), (23, 'Parliament'), (24, 'Parliamentary Committees'), (25, 'Parliamentary Forums'), (26, 'Parliamentary Group'), (27, 'Supreme Court'), (28, 'Judicial Review'), (29, 'Judicial Activism'),
        (30, 'Public Interest Litigation'), (31, 'Governor'), (32, 'Chief Minister'), (33, 'State Council of Ministers'), (34, 'State Legislature'), (35, 'High Court'), (36, 'Tribunals'), (37, 'Subordinate Courts'), (38, 'Special Provisions for Some States'),
        (39, 'Panchayati Raj'), (40, 'Municipalities'),
        (41, 'Union Territories'), (42, 'Scheduled and Tribal Areas'),
        (43, 'Election Commission'), (44, 'Union Public Service Commission (UPSC)'), (45, 'State Public Service Commission (SPSC)'), (46, 'Finance Commission'), (47, 'Goods and Services Tax (GST) Council'), (48, 'National Commission for SCs'), (49, 'National Commission for STs'), (50, 'National Commission for Backward Classes (NCBC)'), (51, 'Special Officer for Linguistic Minorities'), (52, 'Comptroller and Auditor General of India (CAG)'), (53, 'Attorney General of India'), (54, 'Advocate General of the State'),
        (55, 'NITI Aayog'), (56, 'National Human Rights Commission (NHRC)'), (57, 'State Human Rights Commission (SHRC)'), (58, 'Central Information Commission (CIC)'), (59, 'State Information Commission (SIC)'), (60, 'Central Vigilance Commission (CVC)'), (61, 'Central Bureau of Investigation (CBI)'), (62, 'Lokpal and Lokayuktas'), (63, 'National Investigation Agency (NIA)'), (64, 'National Disaster Management Authority (NDMA)'), (65, 'National Commission for Women (NCW)'), (66, 'National Commission for Protection of Child Rights (NCPCR)'), (67, 'National Commission for Minorities'),
        (68, 'Bar Council of India'), (69, 'Law Commission of India'), (70, 'Delimitation Commission of India'), (71, 'Consumer Commissions'), (72, 'Co-operative Societies'), (73, 'Official Language'),
        (74, 'Public Services'), (75, 'Rights and Liabilities of the Government'), (76, 'Special Provisions Relating to Certain Classes'), (77, 'Constitutional Prescriptions'), (78, 'Political Parties'), (79, 'Role of Regional Parties'), (80, 'Elections'), (81, 'Election Laws'), (82, 'Electoral Reforms'), (83, 'Voting Behaviour'), (84, 'Coalition Government'),
        (85, 'Anti-Defection Law'), (86, 'Pressure Groups'), (87, 'National Integration'), (88, 'Foreign Policy'), (89, 'Landmark Judgements and their Impact'), (90, 'Important Doctrines of Constitutional Interpretation'), (91, 'World Constitutions'), (92, 'National Commission for Persons with Disabilities'), (93, 'Model Code of Conduct'), (94, 'Bharatiya Nyaya Sanhita (Criminal Law Reforms)'), (95, 'One Nation One Election')
    ]

    tasks_to_add = []
    for num, title in chapters_data:
        tasks_to_add.append(PolityChapterTask(chapter_number=num, chapter_title=title))
    
    db.add_all(tasks_to_add)
    db.commit()
    
    return db.query(PolityChapterTask).order_by(PolityChapterTask.chapter_number).all()
