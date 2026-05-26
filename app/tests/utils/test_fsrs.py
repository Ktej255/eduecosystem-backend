import pytest
from app.utils.fsrs import convert_score_to_grade

@pytest.mark.parametrize("score, expected_grade", [
    # 0-1 range happy path
    (0.0, 1),
    (0.39, 1),
    (0.5, 2),
    (0.7, 3),
    (0.9, 4),
    (1.0, 4),

    # 0-100 range happy path
    (0, 1),
    (39, 1),
    (50, 2),
    (70, 3),
    (90, 4),
    (100, 4),

    # Boundary values for 0-1 range
    (0.4, 2), # Note: code uses < 0.4, so 0.4 goes to Hard
    (0.6, 3), # code uses < 0.6, so 0.6 goes to Good
    (0.85, 4), # code uses < 0.85, so 0.85 goes to Easy

    # Boundary values for 0-100 range
    (40, 2),
    (60, 3),
    (85, 4),

    # Edge cases
    (-1, 1), # Negative scores
    (-0.5, 1),
    (150, 4), # Above 100
    (1.5, 1), # Edge case: if score is 1.5, > 1 normalizes to 0.015, which is < 0.4 -> Grade 1
])
def test_convert_score_to_grade(score, expected_grade):
    assert convert_score_to_grade(score) == expected_grade
