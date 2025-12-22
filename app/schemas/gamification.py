from pydantic import BaseModel
from typing import List


class LeaderboardEntry(BaseModel):
    user_id: int
    full_name: str
    coins: int
    streak_days: int


class Leaderboard(BaseModel):
    entries: List[LeaderboardEntry]
