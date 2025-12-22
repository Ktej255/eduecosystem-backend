"""
WebSocket API Endpoints for Real-Time Features
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.core.websocket import manager, typing_indicator
from app.api import deps
import json

router = APIRouter()


@router.websocket("/ws/discussions/{thread_id}")
async def websocket_discussion(
    websocket: WebSocket,
    thread_id: int,
    token: str = Query(...),
    db: Session = Depends(deps.get_db),
):
    """
    WebSocket endpoint for real-time discussion updates
    """
    # Verify token and get user
    try:
        user = await deps.get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    room = f"discussion:{thread_id}"
    await manager.connect(websocket, room, user.id, user.full_name or user.username)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "typing":
                await typing_indicator.set_typing(
                    room, user.id, user.full_name or user.username
                )

            elif message_type == "stop_typing":
                await typing_indicator.stop_typing(room, user.id)

            elif message_type == "new_post":
                # Broadcast new post to all users in thread
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "new_post",
                        "post": message.get("post"),
                        "user_id": user.id,
                        "user_name": user.full_name or user.username,
                        "timestamp": message.get("timestamp"),
                    },
                )

            elif message_type == "post_updated":
                # Broadcast post update
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "post_updated",
                        "post_id": message.get("post_id"),
                        "content": message.get("content"),
                        "timestamp": message.get("timestamp"),
                    },
                )

            elif message_type == "vote":
                # Broadcast vote update
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "vote_update",
                        "post_id": message.get("post_id"),
                        "votes": message.get("votes"),
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/live-quiz/{quiz_session_id}")
async def websocket_live_quiz(
    websocket: WebSocket,
    quiz_session_id: int,
    token: str = Query(...),
    db: Session = Depends(deps.get_db),
):
    """
    WebSocket endpoint for live quiz sessions
    """
    try:
        user = await deps.get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    room = f"quiz:{quiz_session_id}"
    await manager.connect(websocket, room, user.id, user.full_name or user.username)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "answer_submitted":
                # Broadcast updated leaderboard
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "leaderboard_update",
                        "leaderboard": message.get("leaderboard"),
                    },
                )

            elif message_type == "quiz_started":
                # Only quiz creator/instructor can start
                await manager.broadcast_to_room(
                    room,
                    {"type": "quiz_started", "start_time": message.get("start_time")},
                )

            elif message_type == "quiz_ended":
                await manager.broadcast_to_room(
                    room,
                    {"type": "quiz_ended", "final_results": message.get("results")},
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/whiteboard/{session_id}")
async def websocket_whiteboard(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...),
    db: Session = Depends(deps.get_db),
):
    """
    WebSocket endpoint for collaborative whiteboard
    """
    try:
        user = await deps.get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    room = f"whiteboard:{session_id}"
    await manager.connect(websocket, room, user.id, user.full_name or user.username)

    # Send current state to new user
    from app.models.live_class import LiveClass

    live_class = db.query(LiveClass).filter(LiveClass.id == session_id).first()
    if live_class and live_class.whiteboard_data:
        await websocket.send_text(
            json.dumps({"type": "init_state", "data": live_class.whiteboard_data})
        )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "save_state":
                # Save state to DB (Instructor only ideally, but allowing all for now)
                live_class = (
                    db.query(LiveClass).filter(LiveClass.id == session_id).first()
                )
                if live_class:
                    live_class.whiteboard_data = message.get("data")
                    db.commit()

            elif message_type in ["draw", "erase", "clear", "undo", "redo"]:
                # Broadcast drawing actions to all users except sender
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": message_type,
                        "data": message.get("data"),
                        "user_id": user.id,
                    },
                    exclude=websocket,
                )

                # Auto-save clear action
                if message_type == "clear":
                    live_class = (
                        db.query(LiveClass).filter(LiveClass.id == session_id).first()
                    )
                    if live_class:
                        live_class.whiteboard_data = {}
                        db.commit()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time notifications
    """
    from app.db.session import SessionLocal
    
    # Authenticate with a short-lived session
    db = SessionLocal()
    try:
        user = await deps.get_current_user_ws(token, db)
        if user.id != user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    finally:
        db.close()

    room = f"notifications:{user_id}"
    await manager.connect(websocket, room, user.id, user.full_name or user.username)

    try:
        while True:
            # Keep connection alive and receive any client messages
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
