"""
Seed UPSC Platform Data
Populates the database with sample batches, plans, questions, and timer configs for the UPSC module.
"""
import logging
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.models.user import User
from app.models.upsc import (
    UPSCBatch, UPSCPlan, UPSCQuestion, UPSCTimerConfig, 
    UPSCContent, UPSCStudentProfile
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MASTER_EMAIL = "ktej255@gmail.com"

def seed_upsc_data():
    db = SessionLocal()
    try:
        # 1. Get Master User (Admin/Instructor)
        admin_user = db.query(User).filter(User.email == MASTER_EMAIL).first()
        if not admin_user:
            logger.error(f"User {MASTER_EMAIL} not found. Run setup_master_account.py first.")
            return

        logger.info(f"Seeding UPSC data with admin: {admin_user.email}")

        # 2. Create UPSC Batch
        batch = db.query(UPSCBatch).filter(UPSCBatch.name == "UPSC Mains 2025 - Batch A").first()
        if not batch:
            logger.info("Creating 'UPSC Mains 2025 - Batch A'...")
            batch = UPSCBatch(
                name="UPSC Mains 2025 - Batch A",
                description="Comprehensive daily answer writing program for Mains 2025.",
                start_date=datetime.now().date(),
                end_date=datetime.now().date() + timedelta(days=365),
                    # is_active removed
                created_by_id=admin_user.id
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)
        
        # 3. Create Student Profile for the user (so they can access student portal)
        profile = db.query(UPSCStudentProfile).filter(UPSCStudentProfile.user_id == admin_user.id).first()
        if not profile:
            logger.info("Creating Student Profile for admin user...")
            profile = UPSCStudentProfile(
                user_id=admin_user.id,
                batch_id=batch.id,
                enrollment_date=datetime.now().date(),
                target_year=2025
            )
            db.add(profile)
            db.commit()

        # 4. Create Monthly Plan
        monthly_plan = db.query(UPSCPlan).filter(
            UPSCPlan.batch_id == batch.id, 
            UPSCPlan.plan_type == "monthly",
            UPSCPlan.title == "Month 1: Polity & Governance"
        ).first()
        
        if not monthly_plan:
            logger.info("Creating Monthly Plan...")
            monthly_plan = UPSCPlan(
                batch_id=batch.id,
                plan_type="monthly",
                title="Month 1: Polity & Governance",
                start_date=datetime.now().date(),
                end_date=datetime.now().date() + timedelta(days=30),
                sequence_order=1,
                    # is_active removed
            )
            db.add(monthly_plan)
            db.commit()
            db.refresh(monthly_plan)

        # 5. Create Daily Plan (Day 1)
        daily_plan = db.query(UPSCPlan).filter(
            UPSCPlan.parent_plan_id == monthly_plan.id,
            UPSCPlan.plan_type == "daily",
            UPSCPlan.sequence_order == 1
        ).first()

        if not daily_plan:
            logger.info("Creating Daily Plan (Day 1)...")
            daily_plan = UPSCPlan(
                batch_id=batch.id,
                plan_type="daily",
                parent_plan_id=monthly_plan.id,
                title="Day 1: Constitution Basics",
                start_date=datetime.now().date(),
                end_date=datetime.now().date(),
                sequence_order=1,
                    # is_active removed
            )
            db.add(daily_plan)
            db.commit()
            db.refresh(daily_plan)

        # 6. Create Questions for Day 1
        existing_questions = db.query(UPSCQuestion).filter(UPSCQuestion.plan_id == daily_plan.id).count()
        if existing_questions == 0:
            logger.info("Creating Questions for Day 1...")
            q1 = UPSCQuestion(
                plan_id=daily_plan.id,
                question_number=1,
                title="Significance of Preamble",
                question_text="Discuss the significance of the Preamble to the Constitution of India. Is it a part of the Constitution?",
                marks=10,
                subject="GS2",
                topic="Polity",
                microtopics=["Preamble", "Basic Structure"],
                keywords=["Sovereign", "Socialist", "Secular", "Democratic", "Republic", "Justice", "Liberty", "Equality", "Fraternity"],
                created_by_id=admin_user.id
            )
            
            q2 = UPSCQuestion(
                plan_id=daily_plan.id,
                question_number=2,
                title="Fundamental Rights vs Directive Principles",
                question_text="Analyze the conflict between Fundamental Rights and Directive Principles of State Policy with reference to landmark Supreme Court judgments.",
                marks=15,
                subject="GS2",
                topic="Polity",
                microtopics=["Fundamental Rights", "DPSP", "Minerva Mills case"],
                keywords=["Harmonious Construction", "Part III", "Part IV", "Justiciable", "Non-justiciable"],
                created_by_id=admin_user.id
            )

            q3 = UPSCQuestion(
                plan_id=daily_plan.id,
                question_number=3,
                title="Federal Structure",
                question_text="The Indian Constitution is federal in form but unitary in spirit. Comment.",
                marks=15,
                subject="GS2",
                topic="Polity",
                microtopics=["Federalism", "Unitary features", "Emergency provisions"],
                keywords=["Quasi-federal", "Strong Centre", "Single Citizenship", "Governor"],
                created_by_id=admin_user.id
            )
            
            db.add_all([q1, q2, q3])
            db.commit()

        # 7. Create Timer Config
        timer_config = db.query(UPSCTimerConfig).filter(UPSCTimerConfig.batch_id == batch.id).first()
        if not timer_config:
            logger.info("Creating Timer Configuration...")
            # Create configs for each phase
            phases = [
                ("read", 5),
                ("write_before", 20),
                ("study", 60),
                ("write_after", 20)
            ]
            
            for phase, duration in phases:
                tc = UPSCTimerConfig(
                    batch_id=batch.id,
                    phase=phase,
                    duration_minutes=duration,
                        # is_active removed
                    created_by_id=admin_user.id
                )
                db.add(tc)
            db.commit()

        logger.info("✅ UPSC Data seeding complete!")

    except Exception as e:
        logger.error(f"Error seeding UPSC data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_upsc_data()
