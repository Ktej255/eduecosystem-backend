"""
FSRS v4 Algorithm Implementation
Free Spaced Repetition Scheduler for calculating optimal review intervals.
"""
import math
from datetime import datetime, timedelta
from typing import Tuple, Optional


# FSRS v4 Default Parameters
FSRS_PARAMS = {
    "w": [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61],
    "request_retention": 0.9,  # Target 90% retention
    "maximum_interval": 365,  # Max 1 year between reviews
}


def calculate_retrievability(stability: float, days_elapsed: float) -> float:
    """
    Calculate current retention probability using FSRS forgetting curve.
    
    Formula: R(t) = e^(-t/S)
    Where:
        t = time elapsed (days)
        S = stability (days until R drops to ~90%)
    
    Returns: Retention probability (0.0 to 1.0)
    """
    if stability <= 0 or days_elapsed < 0:
        return 0.0
    
    return math.exp(-days_elapsed / stability)


def calculate_next_interval(stability: float, target_retention: float = 0.9) -> int:
    """
    Calculate days until retention drops to target threshold.
    
    Formula: t = -S * ln(R_target)
    
    Args:
        stability: Current stability value
        target_retention: Target retention (default 0.9 = 90%)
    
    Returns: Number of days until next review needed
    """
    if stability <= 0:
        return 1
    
    interval = int(-stability * math.log(target_retention))
    return max(1, min(interval, FSRS_PARAMS["maximum_interval"]))


def update_stability_on_grade(
    current_stability: float,
    current_difficulty: float,
    grade: int,
    days_elapsed: float
) -> Tuple[float, float]:
    """
    Update stability and difficulty based on recall grade.
    
    FSRS Grade Scale:
        1 = Again (Failed to recall)
        2 = Hard (Recalled with significant difficulty)
        3 = Good (Recalled correctly)
        4 = Easy (Recalled perfectly)
    
    Returns: (new_stability, new_difficulty)
    """
    # Stability multipliers based on grade
    grade_multipliers = {
        1: 0.2,   # Again - major setback
        2: 1.2,   # Hard - small gain
        3: 2.5,   # Good - moderate gain
        4: 3.5,   # Easy - large gain
    }
    
    # Validate grade
    if grade not in grade_multipliers:
        grade = 3  # Default to "Good"
    
    # Calculate new stability
    multiplier = grade_multipliers[grade]
    
    # Factor in current retrievability for more accurate updates
    retrievability = calculate_retrievability(current_stability, days_elapsed)
    
    if grade == 1:  # Failed - reset stability significantly
        new_stability = max(0.5, current_stability * multiplier)
    else:
        # Bonus for reviewing when retrievability is low
        difficulty_modifier = (11 - current_difficulty) / 10  # Easier = higher multiplier
        if retrievability < 0.8:
            multiplier *= (1 + (1 - retrievability) * 0.3)
        new_stability = current_stability * multiplier * difficulty_modifier
    
    # Update difficulty
    if grade == 1:
        new_difficulty = min(10, current_difficulty + 0.5)
    elif grade == 4:
        new_difficulty = max(1, current_difficulty - 0.3)
    else:
        new_difficulty = current_difficulty
    
    # Cap stability at maximum interval
    new_stability = min(new_stability, FSRS_PARAMS["maximum_interval"])
    
    return (new_stability, new_difficulty)


def convert_score_to_grade(score: float) -> int:
    """
    Convert a percentage score (0-100 or 0-1) to FSRS grade (1-4).
    
    Score ranges:
        0-40%  → Grade 1 (Again)
        41-60% → Grade 2 (Hard)
        61-85% → Grade 3 (Good)
        86-100% → Grade 4 (Easy)
    """
    # Normalize to 0-1 if needed
    if score > 1:
        score = score / 100
    
    if score < 0.4:
        return 1  # Again
    elif score < 0.6:
        return 2  # Hard
    elif score < 0.85:
        return 3  # Good
    else:
        return 4  # Easy


def calculate_initial_stability(encoding_score: float, base_stability: float = 1.0) -> float:
    """
    Calculate initial stability based on encoding (comprehension) score.
    Better understanding = higher initial stability.
    
    Args:
        encoding_score: AI comprehension score (0-1)
        base_stability: Base stability for new topics
    
    Returns: Initial stability value
    """
    if encoding_score <= 0:
        return base_stability * 0.5
    
    # Scale: 0.5 → stability * 0.7, 1.0 → stability * 2.0
    multiplier = 0.5 + (encoding_score * 1.5)
    return base_stability * multiplier


def get_retention_status(retrievability: float) -> str:
    """
    Get human-readable status based on current retrievability.
    
    Returns: "mastered", "stable", "review_soon", "critical", "forgotten"
    """
    if retrievability >= 0.95:
        return "mastered"
    elif retrievability >= 0.85:
        return "stable"
    elif retrievability >= 0.70:
        return "review_soon"
    elif retrievability >= 0.50:
        return "critical"
    else:
        return "forgotten"


def get_color_for_retention(retrievability: float) -> str:
    """Get visualization color based on retention level."""
    if retrievability >= 0.85:
        return "green"
    elif retrievability >= 0.70:
        return "yellow"
    else:
        return "red"


def generate_decay_curve_points(
    stability: float,
    days: int = 10,
    review_events: Optional[list] = None
) -> list:
    """
    Generate data points for knowledge decay curve visualization.
    
    Args:
        stability: Current stability value
        days: Number of days to project
        review_events: List of (day, new_stability) tuples for reviews
    
    Returns: List of {"day": x, "retention": y} points
    """
    points = []
    current_stability = stability
    
    for day in range(days + 1):
        # Check if there's a review on this day
        if review_events:
            for event_day, new_stability in review_events:
                if event_day == day:
                    current_stability = new_stability
                    # On review day, retention jumps back to 100%
                    points.append({"day": day, "retention": 1.0, "reviewed": True})
                    continue
        
        # Calculate natural decay
        retention = calculate_retrievability(current_stability, day)
        points.append({"day": day, "retention": retention, "reviewed": False})
    
    return points
