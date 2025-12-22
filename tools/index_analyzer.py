"""
Database Index Analyzer
Scans database models and suggests missing indexes for foreign keys and common queries
"""

import logging
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_missing_indexes():
    """Analyze all models and suggest missing indexes"""
    
    print("\n" + "=" * 80)
    print("DATABASE INDEX ANALYSIS")
    print("=" * 80)
    
    recommendations = []
    
    # Get all models
    for mapper in Base.registry.mappers:
        model = mapper.class_
        table = mapper.local_table
        
        # Check foreign keys for indexes
        for fk in table.foreign_keys:
            column = fk.parent
            
            # Check if this column has an index
            is_indexed = any(
                column in idx.columns
                for idx in table.indexes
            ) or column.primary_key
            
            if not is_indexed:
                recommendations.append({
                    "table": table.name,
                    "column": column.name,
                    "reason": f"Foreign key to {fk.target_fullname}",
                    "priority": "HIGH"
                })
    
    # Print recommendations
    if recommendations:
        print(f"\n⚠️  Found {len(recommendations)} missing indexes:\n")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. Table: {rec['table']}")
            print(f"   Column: {rec['column']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Priority: {rec['priority']}")
            print()
        
        # Generate migration SQL
        print("=" * 80)
        print("SUGGESTED SQL (for Alembic migration):")
        print("=" * 80 + "\n")
        
        for rec in recommendations:
            idx_name = f"idx_{rec['table']}_{rec['column']}"
            print(f"CREATE INDEX {idx_name} ON {rec['table']}({rec['column']});")
        
        print()
    else:
        print("\n✅ No missing indexes found for foreign keys!")
    
    print("=" * 80 + "\n")
    
    return recommendations


if __name__ == "__main__":
    print("Analyzing database for missing indexes...\n")
    analyze_missing_indexes()
