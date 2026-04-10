import sqlite3
import time

def benchmark_n_plus_1(n):
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE students (id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE drill_sessions (student_id INTEGER, score INTEGER)')
    c.execute('CREATE TABLE meditation_sessions (user_id INTEGER, created_at TIMESTAMP)')
    c.execute('CREATE TABLE activity_logs (user_id INTEGER, timestamp TIMESTAMP)')

    for i in range(n):
        c.execute('INSERT INTO students VALUES (?)', (i,))
        for _ in range(5):
            c.execute('INSERT INTO drill_sessions VALUES (?, ?)', (i, 40))
        c.execute('INSERT INTO meditation_sessions VALUES (?, ?)', (i, '2023-01-01'))
        c.execute('INSERT INTO activity_logs VALUES (?, ?)', (i, '2023-01-01'))
    conn.commit()

    # N+1 approach
    start = time.time()
    students = c.execute('SELECT id FROM students').fetchall()
    results_n_plus_1 = []
    for s in students:
        s_id = s[0]
        avg_score = c.execute('SELECT AVG(score) FROM drill_sessions WHERE student_id = ?', (s_id,)).fetchone()[0]
        last_meditation = c.execute('SELECT created_at FROM meditation_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (s_id,)).fetchone()[0]
        last_activity = c.execute('SELECT timestamp FROM activity_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1', (s_id,)).fetchone()[0]
        results_n_plus_1.append((s_id, avg_score, last_meditation, last_activity))
    n_plus_1_time = time.time() - start

    # Optimized approach
    start = time.time()
    students = c.execute('SELECT id FROM students').fetchall()
    avg_scores = dict(c.execute('SELECT student_id, AVG(score) FROM drill_sessions GROUP BY student_id').fetchall())
    last_meditations = dict(c.execute('SELECT user_id, MAX(created_at) FROM meditation_sessions GROUP BY user_id').fetchall())
    last_activities = dict(c.execute('SELECT user_id, MAX(timestamp) FROM activity_logs GROUP BY user_id').fetchall())

    results_optimized = []
    for s in students:
        s_id = s[0]
        results_optimized.append((s_id, avg_scores.get(s_id, 0), last_meditations.get(s_id), last_activities.get(s_id)))
    optimized_time = time.time() - start

    print(f"N={n}")
    print(f"N+1 time: {n_plus_1_time:.4f}s")
    print(f"Optimized time: {optimized_time:.4f}s")
    print(f"Improvement: {n_plus_1_time / optimized_time:.1f}x")

    assert len(results_n_plus_1) == len(results_optimized)

if __name__ == '__main__':
    benchmark_n_plus_1(200)
    benchmark_n_plus_1(1000)
