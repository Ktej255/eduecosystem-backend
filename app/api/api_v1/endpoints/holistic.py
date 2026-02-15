from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app import models, schemas
from app.models.holistic import Skill, StudentSkillProgress

router = APIRouter()

@router.get("/skills", response_model=List[Any])
def get_skills(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all 36 skills with current user's progress/status
    """
    skills = db.query(Skill).filter(Skill.is_active == True).all()
    
    # If no skills in DB, we should seed them, but for now we return what we have
    # In a production scenario, we'd have a migration or seed script
    
    user_progress = db.query(StudentSkillProgress).filter(
        StudentSkillProgress.user_id == current_user.id
    ).all()
    
    progress_map = {p.skill_id: p for p in user_progress}
    
    output = []
    for skill in skills:
        progress = progress_map.get(skill.id)
        output.append({
            "id": skill.skill_id,
            "title": skill.title,
            "category": skill.category,
            "description": skill.description,
            "icon": skill.icon,
            "color": skill.color,
            "isLocked": progress.status == "locked" if progress else True,
            "progress": progress.mastery_percentage if progress else 0,
            "status": progress.status if progress else "locked"
        })
    
    return output

@router.post("/skills/{skill_id}/unlock")
def unlock_skill_manual(
    skill_id: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Manually unlock a skill (e.g. after payment)
    """
    skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    from app.services.holistic_service import holistic_service
    holistic_service._unlock_skill(db, current_user, skill_id)
    db.commit()
    
    return {"message": "Skill unlocked successfully"}
