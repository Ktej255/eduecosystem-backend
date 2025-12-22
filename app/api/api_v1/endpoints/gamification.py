from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api import deps
from app.models.user import User
from app.schemas.gamification import LeaderboardEntry

router = APIRouter()


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = 10,
) -> Any:
    """
    Get top users by coins.
    """
    users = db.query(User).order_by(desc(User.coins)).limit(limit).all()
    return [
        LeaderboardEntry(
            user_id=u.id,
            full_name=u.full_name or "Anonymous",
            coins=u.coins,
            streak_days=u.streak_days,
        )
        for u in users
    ]


@router.get("/stats")
def get_user_stats(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's gamification stats.
    """
    return {
        "coins": current_user.coins,
        "streak_days": current_user.streak_days,
        "level": (current_user.coins // 1000) + 1,  # Simple level calculation
    }


@router.post("/add-coins")
def add_coins(
    amount: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add coins to current user (Internal use for MVP).
    """
    current_user.coins += amount
    db.commit()
    return {"msg": "Coins added", "new_balance": current_user.coins}


@router.get("/shop/items")
def get_shop_items(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get available items in the shop.
    """
    # Mock items if DB is empty (for MVP speed)
    from app.models.reward import Reward

    items = db.query(Reward).all()
    if not items:
        mock_items = [
            Reward(
                name="Neon Theme",
                cost=500,
                description="A glowing neon interface.",
                type="theme",
                image_url="neon_theme.png",
            ),
            Reward(
                name="Golden Badge",
                cost=1000,
                description="Show off your wealth.",
                type="badge",
                image_url="gold_badge.png",
            ),
            Reward(
                name="Double XP Potion",
                cost=200,
                description="2x XP for 1 hour.",
                type="consumable",
                image_url="potion.png",
            ),
        ]
        db.add_all(mock_items)
        db.commit()
        items = db.query(Reward).all()

    return items


@router.post("/shop/purchase")
def purchase_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Purchase an item from the shop.
    """
    from app.models.reward import Reward, UserReward

    item = db.query(Reward).filter(Reward.id == item_id).first()
    if not item:
        return {"error": "Item not found"}

    if current_user.coins < item.cost:
        return {"error": "Insufficient coins"}

    # Check if already owned (for non-consumables)
    if item.type != "consumable":
        existing = (
            db.query(UserReward)
            .filter(
                UserReward.user_id == current_user.id, UserReward.reward_id == item.id
            )
            .first()
        )
        if existing:
            return {"error": "Item already owned"}

    # Process transaction
    current_user.coins -= item.cost
    user_reward = UserReward(user_id=current_user.id, reward_id=item.id)
    db.add(user_reward)
    db.commit()

    return {
        "msg": "Purchase successful",
        "new_balance": current_user.coins,
        "item": item.name,
    }


@router.get("/transactions")
def get_transactions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's coin transaction history.
    """
    # For MVP, return empty list if CoinTransaction model doesn't exist
    try:
        from app.models.coin_transaction import CoinTransaction

        transactions = (
            db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == current_user.id)
            .order_by(CoinTransaction.created_at.desc())
            .limit(50)
            .all()
        )

        return [
            {
                "id": t.id,
                "amount": t.amount,
                "reason": t.reason,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in transactions
        ]
    except ImportError:
        # Model doesn't exist yet, return empty list for tests
        return []
