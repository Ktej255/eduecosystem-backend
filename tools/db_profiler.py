"""
Database Query Profiler
Analyzes database queries to identify slow operations and missing indexes
"""

import time
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track query statistics
query_stats = []


@event.listens_for(engine := create_engine(settings.DATABASE_URL), "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time"""
    conn.info.setdefault("query_start_time", []).append(time.time())
    logger.debug(f"START QUERY: {statement[:100]}...")


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query execution time and log slow queries"""
    total_time = time.time() - conn.info["query_start_time"].pop()
    
    query_info = {
        "query": statement[:200],  # First 200 chars
        "duration_ms": round(total_time * 1000, 2),
        "timestamp": time.time()
    }
    
    query_stats.append(query_info)
    
    # Log slow queries (>100ms)
    if total_time * 1000 > 100:
        logger.warning(
            f"SLOW QUERY ({query_info['duration_ms']}ms): {statement[:200]}..."
        )


def get_slow_queries(threshold_ms=100):
    """Get all queries slower than threshold"""
    return [q for q in query_stats if q["duration_ms"] > threshold_ms]


def print_query_report():
    """Print comprehensive query performance report"""
    if not query_stats:
        print("No queries recorded yet")
        return
    
    print("\n" + "=" * 80)
    print("DATABASE QUERY PERFORMANCE REPORT")
    print("=" * 80)
    
    total_queries = len(query_stats)
    slow_queries = get_slow_queries(100)
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Slow Queries (>100ms): {len(slow_queries)}")
    
    if slow_queries:
        print("\n" + "-" * 80)
        print("SLOW QUERIES:")
        print("-" * 80)
        
        for i, q in enumerate(sorted(slow_queries, key=lambda x: x["duration_ms"], reverse=True)[:10], 1):
            print(f"\n{i}. Duration: {q['duration_ms']}ms")
            print(f"   Query: {q['query']}")
    
    # Calculate statistics
    durations = [q["duration_ms"] for q in query_stats]
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    
    print("\n" + "-" * 80)
    print("STATISTICS:")
    print("-" * 80)
    print(f"Average Query Time: {avg_duration:.2f}ms")
    print(f"Slowest Query: {max_duration:.2f}ms")
    print(f"Percentage Slow: {(len(slow_queries) / total_queries * 100):.1f}%")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    print("Database Query Profiler")
    print("This will monitor queries when you run your application")
    print("\nTo use:")
    print("1. Import this module in your app")
    print("2. Run your application normally")
    print("3. Call print_query_report() to see results")
    print("\nFor live monitoring, check the logs for 'SLOW QUERY' warnings")
