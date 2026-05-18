import math
import pytest
import sys
from unittest.mock import MagicMock

# Mock missing dependencies
sys.modules['fastapi'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['jose'] = MagicMock()
sys.modules['passlib'] = MagicMock()

from app.utils.fsrs import generate_decay_curve_points, calculate_retrievability


def test_generate_decay_curve_points_basic():
    """Test generating decay curve points with natural decay and no reviews."""
    stability = 5.0
    days = 5

    points = generate_decay_curve_points(stability, days=days)

    assert len(points) == days + 1

    for day in range(days + 1):
        point = points[day]
        assert point["day"] == day
        assert point["reviewed"] is False

        # Manually calculate expected retention
        expected_retention = calculate_retrievability(stability, day)
        assert math.isclose(point["retention"], expected_retention, rel_tol=1e-5)


def test_generate_decay_curve_points_zero_stability():
    """Test with 0 stability, where retention should immediately drop to 0."""
    points = generate_decay_curve_points(0.0, days=5)

    assert points[0]["day"] == 0
    assert points[0]["retention"] == 0.0

    for i in range(1, 6):
        assert points[i]["retention"] == 0.0


def test_generate_decay_curve_points_with_reviews():
    """Test generating decay curve with review events."""
    initial_stability = 2.0
    days = 10

    # Review on day 3 (new stability 5.0), and day 7 (new stability 10.0)
    review_events = [
        (3, 5.0),
        (7, 10.0)
    ]

    points = generate_decay_curve_points(initial_stability, days=days, review_events=review_events)

    assert len(points) == days + 1

    # Check day 0 to 2 (decaying with initial stability)
    assert points[0]["retention"] == 1.0  # e^(0)
    assert math.isclose(points[1]["retention"], calculate_retrievability(2.0, 1), rel_tol=1e-5)
    assert math.isclose(points[2]["retention"], calculate_retrievability(2.0, 2), rel_tol=1e-5)

    # Check day 3 (first review)
    assert points[3]["retention"] == 1.0
    assert points[3]["reviewed"] is True

    # Check day 4 to 6 (decaying with new stability 5.0 from day 3)
    assert math.isclose(points[4]["retention"], calculate_retrievability(5.0, 1), rel_tol=1e-5)
    assert points[4]["reviewed"] is False
    assert math.isclose(points[5]["retention"], calculate_retrievability(5.0, 2), rel_tol=1e-5)
    assert math.isclose(points[6]["retention"], calculate_retrievability(5.0, 3), rel_tol=1e-5)

    # Check day 7 (second review)
    assert points[7]["retention"] == 1.0
    assert points[7]["reviewed"] is True

    # Check day 8 to 10 (decaying with new stability 10.0 from day 7)
    assert math.isclose(points[8]["retention"], calculate_retrievability(10.0, 1), rel_tol=1e-5)
    assert points[8]["reviewed"] is False
    assert math.isclose(points[9]["retention"], calculate_retrievability(10.0, 2), rel_tol=1e-5)
    assert math.isclose(points[10]["retention"], calculate_retrievability(10.0, 3), rel_tol=1e-5)


def test_generate_decay_curve_points_default_days():
    """Test with default days (10) when not provided."""
    stability = 2.0
    points = generate_decay_curve_points(stability)

    assert len(points) == 11  # 0 to 10 is 11 points
    assert points[-1]["day"] == 10
