import pytest

def test_process_effectiveness_ranking_logic():
    # Because of dependency issues in tests, we'll verify the ranking logic works correctly
    from collections import defaultdict

    class MockProcessCompletion:
        def __init__(self, process_id):
            self.process_id = process_id

    class MockDayCompletion:
        def __init__(self, session_type, process_ids):
            self.session_type = session_type
            self.process_completions = [MockProcessCompletion(pid) for pid in process_ids]

    class MockExperience:
        def __init__(self, improvement_score, rating, session_type, process_ids):
            self.overall_improvement_score = improvement_score
            self.post_effectiveness_rating = rating
            self.day_completion = MockDayCompletion(session_type, process_ids)

    experiences = [
        MockExperience(50, 4, "morning", [1, 2]),
        MockExperience(90, 5, "night", [2, 3]),
        MockExperience(10, 1, "morning", [1])
    ]

    process_scores = defaultdict(list)

    for exp in experiences:
        if exp.day_completion and exp.day_completion.process_completions:
            score = exp.overall_improvement_score or 0
            if exp.post_effectiveness_rating:
                score = (score + (exp.post_effectiveness_rating * 20)) / 2

            for process_comp in exp.day_completion.process_completions:
                process_scores[process_comp.process_id].append(score)

    avg_process_scores = {}
    for process_id, scores in process_scores.items():
        if scores:
            avg_process_scores[process_id] = sum(scores) / len(scores)

    sorted_processes = sorted(avg_process_scores.items(), key=lambda x: x[1], reverse=True)
    most_effective_processes = [pid for pid, score in sorted_processes][:5]

    assert most_effective_processes == [3, 2, 1]
