"""
Pack Service

Handles logic for Wolf Packs competition:
- Aggregating individual points into pack points
- Managing pack rankings
- Weekly resets
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.learning_group import LearningGroup, HouseType, GroupMembership
from app.models.user import User
import json

class PackService:
    def sync_points_to_pack(self, db: Session, user_id: int, points: int):
        """
        Sync user's earned coins/points to their respective pack.
        """
        # Find which pack(s) the user belongs to
        memberships = db.query(GroupMembership).filter(GroupMembership.user_id == user_id).all()
        
        for membership in memberships:
            group = db.query(LearningGroup).filter(LearningGroup.id == membership.group_id).first()
            if group:
                group.pack_points += points
                group.weekly_points += points
        
        db.commit()

    def get_leaderboard(self, db: Session, limit: int = 10) -> List[LearningGroup]:
        """
        Get the top packs by total points.
        """
        return db.query(LearningGroup).order_by(desc(LearningGroup.pack_points)).limit(limit).all()

    def get_weekly_leaderboard(self, db: Session, limit: int = 10) -> List[LearningGroup]:
        """
        Get the top packs by weekly points.
        """
        return db.query(LearningGroup).order_by(desc(LearningGroup.weekly_points)).limit(limit).all()

    def reset_weekly_points(self, db: Session):
        """
        Reset weekly points for all packs (intended for a cron job).
        """
        db.query(LearningGroup).update({LearningGroup.weekly_points: 0})
        db.commit()

    def set_pack_house_details(self, db: Session, group_id: int, house_type: HouseType, metadata: Dict[str, Any]):
        """
        Set visual styling and type for a pack.
        """
        group = db.query(LearningGroup).filter(LearningGroup.id == group_id).first()
        if group:
            group.house_type = house_type
            group.pack_metadata = json.dumps(metadata)
            db.commit()
        return group

pack_service = PackService()
