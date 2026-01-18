from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.battle import PackBattle, BattleStatus
from app.models.learning_group import LearningGroup
import json
import random
from datetime import datetime

router = APIRouter()

# Mock Question Bank for MVP (In PROD this comes from Question Bank DB)
MOCK_QUESTIONS = [
    {"id": 1, "text": "Which Article of the Indian Constitution deals with the Election Commission?", "options": ["Article 324", "Article 320", "Article 280", "Article 356"], "correct": "Article 324"},
    {"id": 2, "text": "Who appoints the Chairman of the UPSC?", "options": ["President", "Prime Minister", "Chief Justice", "Speaker"], "correct": "President"},
    {"id": 3, "text": "The phrase 'Procedure established by law' is borrowed from which constitution?", "options": ["Japan", "USA", "UK", "Canada"], "correct": "Japan"},
    {"id": 4, "text": "Which Schedule contains the Anti-Defection Law?", "options": ["10th Schedule", "9th Schedule", "11th Schedule", "8th Schedule"], "correct": "10th Schedule"},
    {"id": 5, "text": "The idea of 'Concurrent List' was borrowed from?", "options": ["Australia", "Canada", "USA", "Ireland"], "correct": "Australia"},
    {"id": 6, "text": "Who is the guardian of the Fundamental Rights?", "options": ["Supreme Court", "Parliament", "President", "Prime Minister"], "correct": "Supreme Court"},
    {"id": 7, "text": "Right to Privacy is a fundamental right under which Article?", "options": ["Article 21", "Article 19", "Article 14", "Article 32"], "correct": "Article 21"}
]

@router.post("/challenge")
def create_challenge(
    defender_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Create a new Battle Challenge against another user.
    """
    if defender_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot battle yourself (yet).")
        
    defender = db.query(User).filter(User.id == defender_id).first()
    if not defender:
        raise HTTPException(status_code=404, detail="Defender not found")
        
    # Generate random 5 questions
    questions = random.sample(MOCK_QUESTIONS, 5)
    
    battle = PackBattle(
        challenger_id=current_user.id,
        defender_id=defender_id,
        status=BattleStatus.PENDING,
        questions_data=questions
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)
    
    return {"message": "Challenge Sent!", "battle_id": battle.id, "questions": questions}

@router.get("/{battle_id}")
def get_battle(
    battle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    battle = db.query(PackBattle).filter(PackBattle.id == battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
        
    return battle

@router.post("/{battle_id}/submit")
def submit_battle_results(
    battle_id: int,
    score: int,
    is_challenger: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Submit score for a battle.
    If both key players have submitted, determine winner.
    """
    battle = db.query(PackBattle).filter(PackBattle.id == battle_id).first()
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    if is_challenger:
        if battle.challenger_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not the challenger")
        battle.challenger_score = score
        # For MVP, assume challenger plays first instantly
        # Real impl needs separate state tracking for each player
        
    else:
        if battle.defender_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not the defender")
        battle.defender_score = score
        battle.status = BattleStatus.COMPLETED
        battle.completed_at = datetime.utcnow()
        
        # Determine Winner
        if battle.challenger_score > battle.defender_score:
            battle.winner_id = battle.challenger_id
        elif battle.defender_score > battle.challenger_score:
            battle.winner_id = battle.defender_id
        else:
            battle.winner_id = None # Draw
            
    db.commit()
    return {"message": "Score submitted", "status": battle.status}

@router.get("/my-battles")
def get_my_battles(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get battles where user is involved.
    """
    battles = db.query(PackBattle).filter(
        (PackBattle.challenger_id == current_user.id) | 
        (PackBattle.defender_id == current_user.id)
    ).order_by(PackBattle.created_at.desc()).limit(10).all()
    
    return battles
