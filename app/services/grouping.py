from sqlalchemy.orm import Session
from app.models.group import Group
from app.models.user import User
import random


def assign_user_to_group(db: Session, user: User) -> Group:
    """
    Assigns a user to a 'Wolf Pack' based on their profile/activity.
    Logic:
    1. If user is already in a group, return it.
    2. Try to find a group with < 5 members and similar average streak.
    3. If no suitable group found, create a new one or join a random open one.
    """
    if user.group_id:
        return user.group

    # 1. Find best existing group
    all_groups = db.query(Group).all()
    best_group = None
    min_diff = float("inf")

    # Filter for groups with space
    open_groups = [g for g in all_groups if len(g.members) < 5]

    for group in open_groups:
        # Calculate average streak
        if not group.members:
            avg_streak = 0
        else:
            avg_streak = sum(m.streak_days for m in group.members) / len(group.members)

        diff = abs(user.streak_days - avg_streak)

        if diff < min_diff:
            min_diff = diff
            best_group = group

    # 2. If a good match is found (e.g., within 10 days streak diff), join it
    # For now, just take the best one if it exists
    if best_group:
        user.group_id = best_group.id
        db.commit()
        db.refresh(user)
        return best_group

    # 3. If no groups exist or all full, create a new one
    # Generate a cool name
    adjectives = ["Iron", "Cyber", "Neon", "Quantum", "Shadow", "Solar"]
    nouns = ["Wolves", "Titans", "Seekers", "Minds", "Pilots", "Nomads"]

    new_name = f"{random.choice(adjectives)} {random.choice(nouns)}"

    # Ensure uniqueness (simple retry)
    while db.query(Group).filter(Group.name == new_name).first():
        new_name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 99)}"

    new_group = Group(name=new_name, description="A new pack of learners.")
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    user.group_id = new_group.id
    db.commit()
    db.refresh(user)

    return new_group
