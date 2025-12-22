"""
Seed predefined achievements into database

Run this script to populate the achievements table with all predefined achievements.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from app.models.achievement import Achievement
from app.services.achievement_service import get_predefined_achievements


def seed_achievements():
    """Seed predefined achievements into database"""
    print("🌱 Seeding achievements...")

    db = SessionLocal()

    try:
        achievements_data = get_predefined_achievements()

        created_count = 0
        updated_count = 0

        for data in achievements_data:
            # Check if achievement already exists
            existing = (
                db.query(Achievement).filter(Achievement.name == data["name"]).first()
            )

            if existing:
                # Update existing achievement
                print(f"   Updating: {data['name']}")
                for key, value in data.items():
                    if key != "name":
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Create new achievement
                print(f"   Creating: {data['name']}")
                achievement = Achievement(**data)
                db.add(achievement)
                created_count += 1

        db.commit()

        print("\n✅ Achievements seeded successfully!")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Total: {len(achievements_data)}")

    except Exception as e:
        print(f"\n❌ Error seeding achievements: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("ACHIEVEMENT SEEDING SCRIPT")
    print("=" * 60)
    print()

    seed_achievements()

    print()
    print("=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
