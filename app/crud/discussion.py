from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.discussion import (
    DiscussionCategory,
    DiscussionThread,
    DiscussionPost,
    PostVote,
)
from app.schemas.discussion import (
    CategoryCreate,
    CategoryUpdate,
    ThreadCreate,
    ThreadUpdate,
    PostCreate,
    PostUpdate,
)


class CRUDCategory(CRUDBase[DiscussionCategory, CategoryCreate, CategoryUpdate]):
    def get_by_course(
        self, db: Session, *, course_id: int, include_inactive: bool = False
    ) -> List[DiscussionCategory]:
        """Get all categories for a course"""
        query = db.query(DiscussionCategory).filter(
            DiscussionCategory.course_id == course_id
        )
        if not include_inactive:
            query = query.filter(DiscussionCategory.is_active == True)
        return query.order_by(asc(DiscussionCategory.order_index)).all()

    def create_with_course(
        self, db: Session, *, obj_in: CategoryCreate
    ) -> DiscussionCategory:
        """Create a new discussion category"""
        db_obj = DiscussionCategory(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDThread(CRUDBase[DiscussionThread, ThreadCreate, ThreadUpdate]):
    def get_by_category(
        self, db: Session, *, category_id: int, skip: int = 0, limit: int = 20
    ) -> List[DiscussionThread]:
        """Get threads by category with pagination"""
        return (
            db.query(DiscussionThread)
            .filter(DiscussionThread.category_id == category_id)
            .order_by(
                desc(DiscussionThread.is_pinned),
                desc(DiscussionThread.last_activity_at),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_course(
        self,
        db: Session,
        *,
        course_id: int,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
        user_id: Optional[int] = None,
        sort_by: str = "recent",
    ) -> List[DiscussionThread]:
        """Get threads for a course with filters"""
        query = db.query(DiscussionThread).filter(
            DiscussionThread.course_id == course_id
        )

        # Apply filters
        if category_id:
            query = query.filter(DiscussionThread.category_id == category_id)
        if is_resolved is not None:
            query = query.filter(DiscussionThread.is_resolved == is_resolved)
        if user_id:
            query = query.filter(DiscussionThread.user_id == user_id)

        # Apply sorting
        if sort_by == "popular":
            query = query.order_by(desc(DiscussionThread.view_count))
        elif sort_by == "unanswered":
            query = query.filter(DiscussionThread.reply_count == 0)
            query = query.order_by(desc(DiscussionThread.created_at))
        else:  # recent
            query = query.order_by(
                desc(DiscussionThread.is_pinned),
                desc(DiscussionThread.last_activity_at),
            )

        return query.offset(skip).limit(limit).all()

    def search(
        self,
        db: Session,
        *,
        course_id: int,
        query_text: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DiscussionThread]:
        """Search threads by title or content"""
        search_term = f"%{query_text}%"
        return (
            db.query(DiscussionThread)
            .filter(
                DiscussionThread.course_id == course_id,
                or_(
                    DiscussionThread.title.ilike(search_term),
                    DiscussionThread.content.ilike(search_term),
                ),
            )
            .order_by(desc(DiscussionThread.last_activity_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_user(
        self, db: Session, *, obj_in: ThreadCreate, user_id: int
    ) -> DiscussionThread:
        """Create a new thread"""
        db_obj = DiscussionThread(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def increment_view_count(self, db: Session, *, thread_id: int) -> DiscussionThread:
        """Increment thread view count"""
        thread = self.get(db, id=thread_id)
        if thread:
            thread.view_count += 1
            db.commit()
            db.refresh(thread)
        return thread

    def update_activity(self, db: Session, *, thread_id: int) -> None:
        """Update last activity timestamp"""
        thread = self.get(db, id=thread_id)
        if thread:
            thread.last_activity_at = datetime.utcnow()
            db.commit()


class CRUDPost(CRUDBase[DiscussionPost, PostCreate, PostUpdate]):
    def get_by_thread(
        self, db: Session, *, thread_id: int, skip: int = 0, limit: int = 100
    ) -> List[DiscussionPost]:
        """Get posts for a thread"""
        return (
            db.query(DiscussionPost)
            .filter(
                DiscussionPost.thread_id == thread_id,
                DiscussionPost.parent_post_id == None,  # Top-level posts only
            )
            .order_by(asc(DiscussionPost.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_replies(self, db: Session, *, post_id: int) -> List[DiscussionPost]:
        """Get replies to a post"""
        return (
            db.query(DiscussionPost)
            .filter(DiscussionPost.parent_post_id == post_id)
            .order_by(asc(DiscussionPost.created_at))
            .all()
        )

    def create_with_user(
        self, db: Session, *, obj_in: PostCreate, user_id: int
    ) -> DiscussionPost:
        """Create a new post/reply"""
        db_obj = DiscussionPost(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)

        # Increment thread reply count
        thread = (
            db.query(DiscussionThread)
            .filter(DiscussionThread.id == obj_in.thread_id)
            .first()
        )
        if thread:
            thread.reply_count += 1
            thread.last_activity_at = datetime.utcnow()

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_as_answer(self, db: Session, *, post_id: int) -> DiscussionPost:
        """Mark post as accepted answer"""
        post = self.get(db, id=post_id)
        if post:
            # Unmark other answers in the same thread
            db.query(DiscussionPost).filter(
                DiscussionPost.thread_id == post.thread_id,
                DiscussionPost.is_answer == True,
            ).update({"is_answer": False})

            # Mark this post as answer
            post.is_answer = True

            # Mark thread as resolved
            thread = (
                db.query(DiscussionThread)
                .filter(DiscussionThread.id == post.thread_id)
                .first()
            )
            if thread:
                thread.is_resolved = True

            db.commit()
            db.refresh(post)
        return post


class CRUDVote:
    def vote(
        self, db: Session, *, post_id: int, user_id: int, vote_type: str
    ) -> DiscussionPost:
        """Vote on a post (upvote or downvote)"""
        # Check if user already voted
        existing_vote = (
            db.query(PostVote)
            .filter(PostVote.post_id == post_id, PostVote.user_id == user_id)
            .first()
        )

        post = db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
        if not post:
            return None

        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type == vote_type:
                # Remove vote if voting same type again
                if vote_type == "upvote":
                    post.upvotes = max(0, post.upvotes - 1)
                else:
                    post.downvotes = max(0, post.downvotes - 1)
                db.delete(existing_vote)
            else:
                # Change vote type
                if vote_type == "upvote":
                    post.downvotes = max(0, post.downvotes - 1)
                    post.upvotes += 1
                else:
                    post.upvotes = max(0, post.upvotes - 1)
                    post.downvotes += 1
                existing_vote.vote_type = vote_type
        else:
            # Create new vote
            new_vote = PostVote(post_id=post_id, user_id=user_id, vote_type=vote_type)
            db.add(new_vote)

            if vote_type == "upvote":
                post.upvotes += 1
            else:
                post.downvotes += 1

        db.commit()
        db.refresh(post)
        return post

    def get_user_vote(
        self, db: Session, *, post_id: int, user_id: int
    ) -> Optional[str]:
        """Get user's vote on a post"""
        vote = (
            db.query(PostVote)
            .filter(PostVote.post_id == post_id, PostVote.user_id == user_id)
            .first()
        )
        return vote.vote_type if vote else None


# Create instances
category = CRUDCategory(DiscussionCategory)
thread = CRUDThread(DiscussionThread)
post = CRUDPost(DiscussionPost)
vote = CRUDVote()
