from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crud import discussion as crud_discussion
from app.crud import permissions as crud_permissions
from app.schemas.discussion import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    Thread,
    ThreadCreate,
    ThreadUpdate,
    ThreadListItem,
    ThreadWithPosts,
    Post,
    PostCreate,
    PostUpdate,
    VoteCreate,
)

router = APIRouter()

# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================


@router.get("/courses/{course_id}/categories", response_model=List[Category])
def list_categories(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get all discussion categories for a course"""
    categories = crud_discussion.category.get_by_course(db, course_id=course_id)
    # Add thread counts
    for cat in categories:
        cat.thread_count = len(cat.threads)
    return categories


@router.post(
    "/courses/{course_id}/categories",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    course_id: int,
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new discussion category (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "moderate_discussion"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: moderate_discussion required",
            )

    category_in.course_id = course_id
    category = crud_discussion.category.create_with_course(db, obj_in=category_in)
    category.thread_count = 0
    return category


@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a discussion category (instructor only)"""
    # Check permission
    if not current_user.is_superuser:
        if not crud_permissions.check_permission(
            db, current_user.id, "moderate_discussion"
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: moderate_discussion required",
            )

    category = crud_discussion.category.get(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category = crud_discussion.category.update(db, db_obj=category, obj_in=category_in)
    category.thread_count = len(category.threads)
    return category


# ============================================================================
# THREAD ENDPOINTS
# ============================================================================


@router.get("/courses/{course_id}/threads", response_model=List[ThreadListItem])
def list_threads(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    category_id: Optional[int] = None,
    is_resolved: Optional[bool] = None,
    user_id: Optional[int] = None,
    sort_by: str = "recent",
    skip: int = 0,
    limit: int = Query(default=20, le=100),
) -> Any:
    """List discussion threads for a course with filters"""
    threads = crud_discussion.thread.get_by_course(
        db,
        course_id=course_id,
        category_id=category_id,
        is_resolved=is_resolved,
        user_id=user_id,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )

    # Enhance with author info
    result = []
    for thread in threads:
        thread_dict = ThreadListItem.from_orm(thread).model_dump()
        thread_dict["author_name"] = (
            thread.author.full_name if thread.author else "Unknown"
        )
        thread_dict["author_avatar"] = getattr(thread.author, "avatar_url", None)

        # Get last post info
        if thread.posts:
            last_post = thread.posts[-1]
            thread_dict["last_post_at"] = last_post.created_at
            thread_dict["last_post_author"] = (
                last_post.author.full_name if last_post.author else "Unknown"
            )

        result.append(thread_dict)

    return result


@router.get("/courses/{course_id}/threads/search", response_model=List[ThreadListItem])
def search_threads(
    course_id: int,
    query: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
) -> Any:
    """Search discussion threads"""
    threads = crud_discussion.thread.search(
        db, course_id=course_id, query_text=query, skip=skip, limit=limit
    )

    result = []
    for thread in threads:
        thread_dict = ThreadListItem.from_orm(thread).model_dump()
        thread_dict["author_name"] = (
            thread.author.full_name if thread.author else "Unknown"
        )
        thread_dict["author_avatar"] = getattr(thread.author, "avatar_url", None)
        result.append(thread_dict)

    return result


@router.post("/threads", response_model=Thread, status_code=status.HTTP_201_CREATED)
def create_thread(
    *,
    db: Session = Depends(deps.get_db),
    thread_in: ThreadCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new discussion thread"""
    # Verify category exists if provided
    if thread_in.category_id:
        category = crud_discussion.category.get(db, id=thread_in.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    thread = crud_discussion.thread.create_with_user(
        db, obj_in=thread_in, user_id=current_user.id
    )
    return thread


@router.get("/threads/{thread_id}", response_model=ThreadWithPosts)
def get_thread(
    thread_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get thread details with posts"""
    thread = crud_discussion.thread.get(db, id=thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Increment view count
    crud_discussion.thread.increment_view_count(db, thread_id=thread_id)

    # Get posts with author info
    posts = crud_discussion.post.get_by_thread(db, thread_id=thread_id)

    thread_dict = ThreadWithPosts.from_orm(thread).model_dump()
    thread_dict["posts"] = []

    for post in posts:
        post_dict = Post.from_orm(post).model_dump()
        post_dict["author_name"] = post.author.full_name if post.author else "Unknown"
        post_dict["author_avatar"] = getattr(post.author, "avatar_url", None)
        post_dict["author_role"] = post.author.role if post.author else None
        post_dict["user_vote"] = crud_discussion.vote.get_user_vote(
            db, post_id=post.id, user_id=current_user.id
        )

        # Get replies
        replies = crud_discussion.post.get_replies(db, post_id=post.id)
        post_dict["replies"] = []
        for reply in replies:
            reply_dict = Post.from_orm(reply).model_dump()
            reply_dict["author_name"] = (
                reply.author.full_name if reply.author else "Unknown"
            )
            reply_dict["author_avatar"] = getattr(reply.author, "avatar_url", None)
            reply_dict["user_vote"] = crud_discussion.vote.get_user_vote(
                db, post_id=reply.id, user_id=current_user.id
            )
            post_dict["replies"].append(reply_dict)

        thread_dict["posts"].append(post_dict)

    return thread_dict


@router.put("/threads/{thread_id}", response_model=Thread)
def update_thread(
    thread_id: int,
    *,
    db: Session = Depends(deps.get_db),
    thread_in: ThreadUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a thread (author or instructor)"""
    thread = crud_discussion.thread.get(db, id=thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Check permissions
    # Check permissions
    if thread.user_id != current_user.id and not current_user.is_superuser:
        # Check if moderator/instructor
        if not crud_permissions.check_permission(
            db, current_user.id, "moderate_discussion"
        ):
            raise HTTPException(status_code=403, detail="Not authorized")

    thread = crud_discussion.thread.update(db, db_obj=thread, obj_in=thread_in)
    return thread


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete a thread (author or instructor)"""
    thread = crud_discussion.thread.get(db, id=thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Check permissions
    # Check permissions
    if thread.user_id != current_user.id and not current_user.is_superuser:
        # Check if moderator/instructor
        if not crud_permissions.check_permission(
            db, current_user.id, "moderate_discussion"
        ):
            raise HTTPException(status_code=403, detail="Not authorized")

    crud_discussion.thread.remove(db, id=thread_id)


# ============================================================================
# POST ENDPOINTS
# ============================================================================


@router.post("/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(
    *,
    db: Session = Depends(deps.get_db),
    post_in: PostCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Create a new post/reply"""
    # Verify thread exists and is not locked
    thread = crud_discussion.thread.get(db, id=post_in.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread.is_locked:
        raise HTTPException(status_code=403, detail="Thread is locked")

    post = crud_discussion.post.create_with_user(
        db, obj_in=post_in, user_id=current_user.id
    )

    # Send notification to thread author
    from app.services.notification_helpers import create_and_emit_notification
    from app.models.notification import NotificationType

    if thread.user_id != current_user.id:
        create_and_emit_notification(
            db=db,
            user_id=thread.user_id,
            notification_type=NotificationType.DISCUSSION_REPLY,
            title="New reply to your thread",
            message=f"{current_user.full_name} replied to '{thread.title}'",
            data={"thread_id": thread.id, "post_id": post.id},
            action_url=f"/lms/courses/{thread.course_id}/discussions/{thread.id}",
        )

    return post


@router.put("/posts/{post_id}", response_model=Post)
def update_post(
    post_id: int,
    *,
    db: Session = Depends(deps.get_db),
    post_in: PostUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Update a post (author only)"""
    post = crud_discussion.post.get(db, id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    post = crud_discussion.post.update(db, db_obj=post, obj_in=post_in)
    post.is_edited = True
    db.commit()
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    """Delete a post (author or instructor)"""
    post = crud_discussion.post.get(db, id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id and not current_user.is_superuser:
        # Check if moderator/instructor
        if not crud_permissions.check_permission(db, current_user.id, "delete_post"):
            raise HTTPException(status_code=403, detail="Not authorized")

    crud_discussion.post.remove(db, id=post_id)


@router.post("/posts/{post_id}/mark-answer", response_model=Post)
def mark_as_answer(
    post_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Mark a post as the accepted answer (thread author or instructor)"""
    post = crud_discussion.post.get(db, id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    thread = crud_discussion.thread.get(db, id=post.thread_id)
    if thread.user_id != current_user.id and not current_user.is_superuser:
        # Check if moderator/instructor
        if not crud_permissions.check_permission(
            db, current_user.id, "moderate_discussion"
        ):
            raise HTTPException(status_code=403, detail="Not authorized")

    post = crud_discussion.post.mark_as_answer(db, post_id=post_id)
    return post


# ============================================================================
# VOTING ENDPOINTS
# ============================================================================


@router.post("/posts/{post_id}/vote", response_model=Post)
def vote_post(
    post_id: int,
    *,
    db: Session = Depends(deps.get_db),
    vote_in: VoteCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Vote on a post (upvote or downvote)"""
    post = crud_discussion.vote.vote(
        db, post_id=post_id, user_id=current_user.id, vote_type=vote_in.vote_type
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post
