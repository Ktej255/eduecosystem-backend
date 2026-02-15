from sqlalchemy.orm import Session
from app.models.holistic import Skill, StudentSkillProgress
from app.models.user import User
from datetime import datetime

class HolisticService:
    """
    Handles the 'Sequential Learning' logic for the 36 Skills hub
    """
    
    def check_and_unlock_skills(self, db: Session, user: User):
        """
        Scan for academic milestones and unlock corresponding skills
        """
        # 1. Streak-based Unlocking (Mindset Skills)
        if user.streak_days >= 7:
            self._unlock_skill(db, user, "min-1") # Stoic Principles (Mindset)
        
        # 2. XP-based Unlocking (Digital Skills)
        if user.xp >= 5000:
            self._unlock_skill(db, user, "dig-1") # Mastering AI Tools (Digital)

        # 3. Future logic (e.g. Economy completion -> Compound Interest)
        # To be added as we integrate more specific academic tracking
        
        db.commit()

    def _unlock_skill(self, db: Session, user: User, skill_id: str):
        """Helper to unlock a skill for a user"""
        skill = db.query(Skill).filter(Skill.skill_id == skill_id).first()
        if not skill:
            return

        progress = db.query(StudentSkillProgress).filter(
            StudentSkillProgress.user_id == user.id,
            StudentSkillProgress.skill_id == skill.id
        ).first()

        if not progress:
            progress = StudentSkillProgress(
                user_id=user.id,
                skill_id=skill.id,
                status="unlocked",
                unlocked_at=datetime.utcnow()
            )
            db.add(progress)
        elif progress.status == "locked":
            progress.status = "unlocked"
            progress.unlocked_at = datetime.utcnow()
            db.add(progress)

holistic_service = HolisticService()
