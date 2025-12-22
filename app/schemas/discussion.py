from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


# ============================================================================
# DISCUSSION CATEGORY SCHEMAS
# ============================================================================


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    order_index: int = Field(default=0, ge=0)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Schema for creating a discussion category"""

    course_id: int


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryInDBBase(CategoryBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDBBase):
    """Full category schema"""

    thread_count: int = 0  # Calculated field


# ============================================================================
# DISCUSSION THREAD SCHEMAS
# ============================================================================


class ThreadBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class ThreadCreate(ThreadBase):
    """Schema for creating a discussion thread"""

    category_id: int
    course_id: int


class ThreadUpdate(BaseModel):
    """Schema for updating a thread"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None
    is_resolved: Optional[bool] = None


class ThreadInDBBase(ThreadBase):
    id: int
    category_id: int
    course_id: int
    user_id: int
    is_pinned: bool
    is_locked: bool
    is_resolved: bool
    view_count: int
    reply_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Thread(ThreadInDBBase):
    """Full thread schema"""

    pass


class ThreadListItem(ThreadInDBBase):
    """Thread schema for list views with author info"""

    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    last_post_at: Optional[datetime] = None
    last_post_author: Optional[str] = None


class ThreadWithPosts(Thread):
    """Thread with nested posts"""

    posts: List["Post"] = []


# ============================================================================
# DISCUSSION POST SCHEMAS
# ============================================================================


class PostBase(BaseModel):
    content: str = Field(..., min_length=1)


class PostCreate(PostBase):
    """Schema for creating a post/reply"""

    thread_id: int
    parent_post_id: Optional[int] = None


class PostUpdate(BaseModel):
    """Schema for updating a post"""

    content: str = Field(..., min_length=1)


class PostInDBBase(PostBase):
    id: int
    thread_id: int
    user_id: int
    parent_post_id: Optional[int] = None
    is_answer: bool
    is_edited: bool
    upvotes: int
    downvotes: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Post(PostInDBBase):
    """Full post schema"""

    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    author_role: Optional[str] = None
    user_vote: Optional[str] = None  # "upvote", "downvote", or None


class PostWithReplies(Post):
    """Post with nested replies"""

    replies: List["PostWithReplies"] = []


# ============================================================================
# VOTING SCHEMAS
# ============================================================================


class VoteCreate(BaseModel):
    """Schema for voting on a post"""

    vote_type: str = Field(..., pattern="^(upvote|downvote)$")


class Vote(BaseModel):
    id: int
    post_id: int
    user_id: int
    vote_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SEARCH/FILTER SCHEMAS
# ============================================================================


class ThreadSearchParams(BaseModel):
    """Parameters for searching/filtering threads"""

    query: Optional[str] = None
    category_id: Optional[int] = None
    is_resolved: Optional[bool] = None
    user_id: Optional[int] = None
    sort_by: str = "recent"  # recent, popular, unanswered
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, le=100)


# Update forward references for nested models
ThreadWithPosts.model_rebuild()
PostWithReplies.model_rebuild()
