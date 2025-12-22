"""
Real-time Chat API Endpoints

Provides REST API endpoints for chat messages, presence status, and related features.
WebSocket endpoints for real-time messaging are in websocket.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.api import deps
from app.models.user import User
from app.models.chat import RealtimeChatMessage
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageResponse,
    ChatMessageList,
    UserPresenceUpdate,
    UserPresenceResponse,
    ReactionCreate,
    ReactionRemove,
)
from app.services.presence import presence_service
from app.core.cache import cache

router = APIRouter()


@router.post("/messages", response_model=ChatMessageResponse)
def create_message(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_in: ChatMessageCreate,
):
    """
    Create a new chat message.
    """
    # Validate that at least one target is specified
    if not any(
        [
            message_in.study_room_id,
            message_in.study_group_id,
            message_in.discussion_thread_id,
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail="Must specify study_room_id, study_group_id, or discussion_thread_id",
        )

    # Create message
    message = RealtimeChatMessage(
        content=message_in.content,
        message_type=message_in.message_type,
        sender_id=current_user.id,
        study_room_id=message_in.study_room_id,
        study_group_id=message_in.study_group_id,
        discussion_thread_id=message_in.discussion_thread_id,
        attachment_url=message_in.attachment_url,
        attachment_name=message_in.attachment_name,
        parent_id=message_in.parent_id,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # Add sender info to response
    response = ChatMessageResponse.from_orm(message)
    response.sender_name = current_user.full_name or current_user.username

    # Invalidate message list cache
    if message_in.study_room_id:
        cache.delete_pattern(f"chat:room:{message_in.study_room_id}:*")
    if message_in.study_group_id:
        cache.delete_pattern(f"chat:group:{message_in.study_group_id}:*")

    return response


@router.get("/messages", response_model=ChatMessageList)
def get_messages(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    study_room_id: Optional[int] = None,
    study_group_id: Optional[int] = None,
    discussion_thread_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Get chat messages with pagination.
    """
    # Build query
    query = db.query(RealtimeChatMessage).filter(
        RealtimeChatMessage.is_deleted == False
    )

    if study_room_id:
        query = query.filter(RealtimeChatMessage.study_room_id == study_room_id)
        cache_key = f"chat:room:{study_room_id}:page:{page}"
    elif study_group_id:
        query = query.filter(RealtimeChatMessage.study_group_id == study_group_id)
        cache_key = f"chat:group:{study_group_id}:page:{page}"
    elif discussion_thread_id:
        query = query.filter(
            RealtimeChatMessage.discussion_thread_id == discussion_thread_id
        )
        cache_key = f"chat:thread:{discussion_thread_id}:page:{page}"
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify study_room_id, study_group_id, or discussion_thread_id",
        )

    # Try cache
    cached = cache.get(cache_key)
    if cached:
        return ChatMessageList(**cached)

    # Get total count
    total = query.count()

    # Get paginated messages
    offset = (page - 1) * page_size
    messages = (
        query.order_by(RealtimeChatMessage.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Add sender info
    message_responses = []
    for msg in messages:
        response = ChatMessageResponse.from_orm(msg)
        if msg.sender:
            response.sender_name = msg.sender.full_name or msg.sender.username
        message_responses.append(response)

    result = ChatMessageList(
        messages=message_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )

    # Cache the result
    cache.set(cache_key, result.model_dump(), ttl=60)  # Cache for 1 minute

    return result


@router.put("/messages/{message_id}", response_model=ChatMessageResponse)
def update_message(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_id: int,
    message_update: ChatMessageUpdate,
):
    """
    Update a chat message (only sender can update).
    """
    message = (
        db.query(RealtimeChatMessage)
        .filter(RealtimeChatMessage.id == message_id)
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to edit this message"
        )

    if message_update.content is not None:
        message.content = message_update.content
        message.is_edited = True
        message.edited_at = datetime.utcnow()

    if message_update.is_deleted is not None:
        message.is_deleted = message_update.is_deleted
        message.deleted_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    # Invalidate cache
    if message.study_room_id:
        cache.delete_pattern(f"chat:room:{message.study_room_id}:*")
    if message.study_group_id:
        cache.delete_pattern(f"chat:group:{message.study_group_id}:*")

    response = ChatMessageResponse.from_orm(message)
    response.sender_name = current_user.full_name or current_user.username

    return response


@router.delete("/messages/{message_id}")
def delete_message(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_id: int,
):
    """
    Soft delete a chat message.
    """
    message = (
        db.query(RealtimeChatMessage)
        .filter(RealtimeChatMessage.id == message_id)
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this message"
        )

    message.is_deleted = True
    message.deleted_at = datetime.utcnow()

    db.commit()

    # Invalidate cache
    if message.study_room_id:
        cache.delete_pattern(f"chat:room:{message.study_room_id}:*")
    if message.study_group_id:
        cache.delete_pattern(f"chat:group:{message.study_group_id}:*")

    return {"message": "Message deleted successfully"}


@router.post("/messages/{message_id}/reactions")
def add_reaction(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_id: int,
    reaction_create: ReactionCreate,
):
    """
    Add emoji reaction to a message.
    """
    message = (
        db.query(RealtimeChatMessage)
        .filter(RealtimeChatMessage.id == message_id)
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Parse existing reactions
    reactions = {}
    if message.reactions:
        try:
            reactions = json.loads(message.reactions)
        except:
            reactions = {}

    # Add user to this emoji's reaction list
    emoji = reaction_create.emoji
    if emoji not in reactions:
        reactions[emoji] = []

    if current_user.id not in reactions[emoji]:
        reactions[emoji].append(current_user.id)

    # Save updated reactions
    message.reactions = json.dumps(reactions)
    db.commit()

    return {"message": "Reaction added", "reactions": reactions}


@router.delete("/messages/{message_id}/reactions")
def remove_reaction(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    message_id: int,
    reaction_remove: ReactionRemove,
):
    """
    Remove emoji reaction from a message.
    """
    message = (
        db.query(RealtimeChatMessage)
        .filter(RealtimeChatMessage.id == message_id)
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Parse existing reactions
    reactions = {}
    if message.reactions:
        try:
            reactions = json.loads(message.reactions)
        except:
            reactions = {}

    # Remove user from this emoji's reaction list
    emoji = reaction_remove.emoji
    if emoji in reactions:
        if current_user.id in reactions[emoji]:
            reactions[emoji].remove(current_user.id)

        # Remove emoji key if no users left
        if not reactions[emoji]:
            del reactions[emoji]

    # Save updated reactions
    message.reactions = json.dumps(reactions)
    db.commit()

    return {"message": "Reaction removed", "reactions": reactions}


# Presence Endpoints


@router.get("/presence/me", response_model=UserPresenceResponse)
def get_my_presence(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get current user's presence status.
    """
    presence = presence_service.get_presence(db, current_user.id)

    if not presence:
        # Create default presence
        presence = presence_service.update_presence(db, current_user.id, "online")

    response = UserPresenceResponse.from_orm(presence)
    response.user_name = current_user.full_name or current_user.username

    return response


@router.put("/presence/me", response_model=UserPresenceResponse)
def update_my_presence(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    presence_update: UserPresenceUpdate,
):
    """
    Update current user's presence status.
    """
    presence = presence_service.update_presence(
        db,
        current_user.id,
        presence_update.status or "online",
        presence_update.status_message,
        presence_update.current_location,
    )

    response = UserPresenceResponse.from_orm(presence)
    response.user_name = current_user.full_name or current_user.username

    return response


@router.post("/presence/heartbeat")
def heartbeat(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Send heartbeat to indicate user is still active.
    """
    presence_service.heartbeat(db, current_user.id)
    return {"message": "Heartbeat received"}


@router.get("/presence/online", response_model=List[UserPresenceResponse])
def get_online_users(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    location: Optional[str] = None,
):
    """
    Get list of currently online users.
    """
    cache_key = f"presence:online:{location or 'all'}"

    # Try cache
    cached = cache.get(cache_key)
    if cached:
        return [UserPresenceResponse(**u) for u in cached]

    presences = presence_service.get_online_users(db, location)

    responses = []
    for presence in presences:
        response = UserPresenceResponse.from_orm(presence)
        if presence.user:
            response.user_name = presence.user.full_name or presence.user.username
        responses.append(response)

    # Cache for 30 seconds
    cache.set(cache_key, [r.model_dump() for r in responses], ttl=30)

    return responses


@router.get("/presence/{user_id}", response_model=UserPresenceResponse)
def get_user_presence(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_id: int,
):
    """
    Get specific user's presence status.
    """
    presence = presence_service.get_presence(db, user_id)

    if not presence:
        raise HTTPException(status_code=404, detail="User presence not found")

    response = UserPresenceResponse.from_orm(presence)
    if presence.user:
        response.user_name = presence.user.full_name or presence.user.username

    return response
