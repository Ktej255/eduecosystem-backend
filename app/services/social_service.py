"""Service for handling social interactions"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List
from datetime import datetime

from app.models.friendship import Friendship, FriendshipStatus
from app.models.direct_message import DirectMessage
from app.models.learning_group import LearningGroup, GroupMembership, MemberRole, GroupType, GroupPrivacy
from app.models.user import User
from app.services.notification_helpers import create_and_emit_notification
from app.models.notification import NotificationType
from app.websocket import manager


class SocialService:
    def __init__(self, db: Session):
        self.db = db

    # --- Friend System ---
    def send_friend_request(self, user_id: int, friend_id: int) -> Friendship:
        if user_id == friend_id:
            raise ValueError("Cannot friend yourself")

        existing = (
            self.db.query(Friendship)
            .filter(
                or_(
                    and_(
                        Friendship.user_id == user_id, Friendship.friend_id == friend_id
                    ),
                    and_(
                        Friendship.user_id == friend_id, Friendship.friend_id == user_id
                    ),
                )
            )
            .first()
        )

        if existing:
            if existing.status == FriendshipStatus.REJECTED:
                # Allow re-requesting if rejected previously? Or update status?
                existing.status = FriendshipStatus.PENDING
                existing.user_id = user_id  # Reset sender
                existing.friend_id = friend_id
                self.db.commit()
                self.db.refresh(existing)
                return existing
            return existing  # Already exists

        friendship = Friendship(
            user_id=user_id, friend_id=friend_id, status=FriendshipStatus.PENDING
        )
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)

        # Notify recipient
        create_and_emit_notification(
            db=self.db,
            user_id=friend_id,
            notification_type=NotificationType.FRIEND_REQUEST,
            title="New Friend Request",
            message="You have a new friend request",
            data={"request_id": friendship.id, "sender_id": user_id},
            action_url="/social/friends",
        )

        return friendship

    def accept_friend_request(self, request_id: int, user_id: int) -> Friendship:
        friendship = (
            self.db.query(Friendship).filter(Friendship.id == request_id).first()
        )
        if not friendship:
            raise ValueError("Request not found")

        if friendship.friend_id != user_id:
            raise ValueError("Not authorized")

        friendship.status = FriendshipStatus.ACCEPTED
        friendship.accepted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(friendship)

        # Notify sender
        create_and_emit_notification(
            db=self.db,
            user_id=friendship.user_id,
            notification_type=NotificationType.FRIEND_REQUEST,  # Or a generic social type
            title="Friend Request Accepted",
            message="Your friend request was accepted!",
            data={"friend_id": user_id},
            action_url="/social/friends",
        )

        return friendship

    def get_friends(self, user_id: int) -> List[User]:
        friendships = (
            self.db.query(Friendship)
            .filter(
                and_(
                    or_(Friendship.user_id == user_id, Friendship.friend_id == user_id),
                    Friendship.status == FriendshipStatus.ACCEPTED,
                )
            )
            .all()
        )

        friends = []
        for f in friendships:
            if f.user_id == user_id:
                friends.append(f.friend)
            else:
                friends.append(f.user)
        return friends

    # --- Messaging ---
    def send_message(
        self, sender_id: int, receiver_id: int, content: str
    ) -> DirectMessage:
        # Check if friends (optional, but good for privacy)
        # For now, allow if not blocked

        msg = DirectMessage(
            sender_id=sender_id, receiver_id=receiver_id, message=content
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        # Emit real-time event via WebSocket
        # We can use the manager to send a custom event
        import asyncio

        asyncio.create_task(
            manager.send_personal_message(
                user_id=receiver_id,
                message={
                    "type": "new_message",
                    "id": msg.id,
                    "sender_id": sender_id,
                    "content": content,
                    "created_at": msg.created_at.isoformat(),
                },
            )
        )

        return msg

    def get_conversation(
        self, user_id: int, other_user_id: int, limit: int = 50
    ) -> List[DirectMessage]:
        messages = (
            self.db.query(DirectMessage)
            .filter(
                or_(
                    and_(
                        DirectMessage.sender_id == user_id,
                        DirectMessage.receiver_id == other_user_id,
                    ),
                    and_(
                        DirectMessage.sender_id == other_user_id,
                        DirectMessage.receiver_id == user_id,
                    ),
                )
            )
            .order_by(desc(DirectMessage.created_at))
            .limit(limit)
            .all()
        )

        return messages[::-1]  # Return chronological order

    # --- Study Groups (Refactored to LearningGroup) ---
    def create_group(
        self,
        creator_id: int,
        name: str,
        description: str = None,
        is_private: bool = False,
    ) -> LearningGroup:
        group = LearningGroup(
            name=name,
            description=description,
            created_by=creator_id,
            privacy=GroupPrivacy.PRIVATE if is_private else GroupPrivacy.PUBLIC,
            group_type=GroupType.STUDY
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)

        # Add creator as admin
        membership = GroupMembership(
            group_id=group.id,
            user_id=creator_id,
            role=MemberRole.ADMIN
        )
        self.db.add(membership)
        self.db.commit()

        return group

    def get_user_groups(self, user_id: int) -> List[LearningGroup]:
        # Query groups where user is a member
        groups = (
            self.db.query(LearningGroup)
            .join(GroupMembership)
            .filter(GroupMembership.user_id == user_id)
            .all()
        )
        return groups


social_service = SocialService
