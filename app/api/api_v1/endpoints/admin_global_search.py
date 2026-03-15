from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Any, List, Dict
from app.api import deps
from app.models.user import User
from app.models.lead import Lead
from app.models.course import Course

router = APIRouter()

@router.get("/search", response_model=List[Dict[str, Any]])
def global_admin_search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(deps.get_db),
    current_admin: User = Depends(deps.get_admin_user),
) -> Any:
    """
    Global Command Search: Finds Students, Teachers, Leads, or Courses in one go.
    """
    search_query = f"%{q}%"
    results = []

    # 1. Search Users (Students/Teachers)
    users = db.query(User).filter(
        or_(
            User.full_name.ilike(search_query),
            User.email.ilike(search_query)
        )
    ).limit(5).all()
    for u in users:
        results.append({
            "id": u.id,
            "type": "USER",
            "category": u.role.upper(),
            "title": u.full_name or u.email,
            "subtitle": u.email,
            "link": f"/admin/users/{u.id}" if u.role == 'student' else f"/admin/teachers/{u.id}"
        })

    # 2. Search Leads
    leads = db.query(Lead).filter(
        or_(
            Lead.full_name.ilike(search_query),
            Lead.email.ilike(search_query),
            Lead.phone.ilike(search_query)
        )
    ).limit(5).all()
    for l in leads:
        results.append({
            "id": l.id,
            "type": "LEAD",
            "category": "CRM LEAD",
            "title": l.full_name,
            "subtitle": f"{l.email} | {l.source_primary}",
            "link": f"/admin/leads" # Could deep link to lead modal in future
        })

    # 3. Search Courses
    courses = db.query(Course).filter(
        Course.title.ilike(search_query)
    ).limit(5).all()
    for c in courses:
        results.append({
            "id": c.id,
            "type": "COURSE",
            "category": "LMS COURSE",
            "title": c.title,
            "subtitle": f"Instructor ID: {c.instructor_id}",
            "link": f"/admin/courses"
        })

    return results
