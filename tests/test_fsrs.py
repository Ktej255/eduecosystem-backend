
import pytest
from app.utils.fsrs import update_stability_on_grade, FSRS_PARAMS

def test_update_stability_grade_1():
    # Grade 1 (Again) decreases stability and increases difficulty
    new_stab, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=1,
        days_elapsed=2.0
    )
    # 10.0 * 0.2 = 2.0
    assert abs(new_stab - 2.0) < 1e-5
    assert abs(new_diff - 5.5) < 1e-5

def test_update_stability_grade_2():
    # Grade 2 (Hard) slight increase in stability, no change in diff
    new_stab, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=2,
        days_elapsed=2.0
    )
    # multiplier = 1.2
    # difficulty_modifier = (11 - 5) / 10 = 0.6
    # 10.0 * 1.2 * 0.6 = 7.2
    assert abs(new_stab - 7.2) < 1e-5
    assert abs(new_diff - 5.0) < 1e-5

def test_update_stability_grade_3():
    # Grade 3 (Good) moderate increase in stability, no change in diff
    new_stab, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=3,
        days_elapsed=2.0
    )
    # multiplier = 2.5
    # difficulty_modifier = 0.6
    # 10.0 * 2.5 * 0.6 = 15.0
    assert abs(new_stab - 15.0) < 1e-5
    assert abs(new_diff - 5.0) < 1e-5

def test_update_stability_grade_4():
    # Grade 4 (Easy) large increase in stability, decrease in diff
    new_stab, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=4,
        days_elapsed=2.0
    )
    # multiplier = 3.5
    # difficulty_modifier = 0.6
    # 10.0 * 3.5 * 0.6 = 21.0
    assert abs(new_stab - 21.0) < 1e-5
    assert abs(new_diff - 4.7) < 1e-5

def test_update_stability_invalid_grade_defaults_to_3():
    new_stab_valid, new_diff_valid = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=3,
        days_elapsed=2.0
    )

    new_stab_invalid, new_diff_invalid = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=99,
        days_elapsed=2.0
    )

    assert new_stab_invalid == new_stab_valid
    assert new_diff_invalid == new_diff_valid

def test_update_stability_difficulty_cap():
    # Grade 1 increases difficulty by 0.5, but should cap at 10
    _, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=9.8,
        grade=1,
        days_elapsed=2.0
    )
    assert new_diff == 10.0

def test_update_stability_difficulty_floor():
    # Grade 4 decreases difficulty by 0.3, but should floor at 1
    _, new_diff = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=1.1,
        grade=4,
        days_elapsed=2.0
    )
    assert new_diff == 1.0

def test_update_stability_max_interval_cap():
    max_interval = FSRS_PARAMS["maximum_interval"]
    new_stab, _ = update_stability_on_grade(
        current_stability=max_interval - 10,
        current_difficulty=1.0,
        grade=4,
        days_elapsed=2.0
    )
    # Huge jump that would exceed max_interval
    assert new_stab == max_interval

def test_update_stability_retrievability_bonus():
    # Retrievability < 0.8 should apply a bonus multiplier
    # e^(-t/S) -> e^(-5/10) = e^(-0.5) ≈ 0.6065 (which is < 0.8)
    new_stab_bonus, _ = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=3,
        days_elapsed=5.0
    )

    # e^(-1/10) = e^(-0.1) ≈ 0.9048 (which is > 0.8, no bonus)
    new_stab_no_bonus, _ = update_stability_on_grade(
        current_stability=10.0,
        current_difficulty=5.0,
        grade=3,
        days_elapsed=1.0
    )

    # Using larger days_elapsed with grade=3 should result in higher stability
    # when holding current_stability and current_difficulty constant, due to the low retrievability bonus.
    assert new_stab_bonus > new_stab_no_bonus

def test_update_stability_grade_1_minimum_stability():
    # Grade 1 should not drop stability below 0.5
    new_stab, _ = update_stability_on_grade(
        current_stability=1.0,
        current_difficulty=5.0,
        grade=1,
        days_elapsed=1.0
    )
    # 1.0 * 0.2 = 0.2, but should max with 0.5
    assert new_stab == 0.5
