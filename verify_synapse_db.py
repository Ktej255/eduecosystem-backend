from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.upsc_synapse import UPSCCognitiveProfile, UPSCGapAnalysis, UPSCUnlockTransaction
# Do not import User model to avoid schema mismatch errors
# from app.models.user import User 

def verify_synapse_db():
    db = SessionLocal()
    try:
        # 1. Get a dummy user via Raw SQL to avoid Model Drift issues
        result = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        
        if result:
            user_id = result[0]
            print(f"✅ Found existing User ID: {user_id}")
        else:
            print("⚠️ No users found. Inserting dummy user via SQL...")
            db.execute(text("INSERT INTO users (email, hashed_password, is_active) VALUES ('test_synapse@example.com', 'dummy', 1)"))
            db.commit()
            user_id = db.execute(text("SELECT id FROM users WHERE email='test_synapse@example.com'")).fetchone()[0]
            print(f"✅ Created dummy User ID: {user_id}")

        # 2. CRUD Profile
        existing_profile = db.query(UPSCCognitiveProfile).filter_by(user_id=user_id).first()
        if existing_profile:
             # Clean up previous runs
             db.delete(existing_profile)
             db.commit()

        new_profile = UPSCCognitiveProfile(
            user_id=user_id,
            current_level="level1",
            wps_score=45.5,
            stress_index=3.2
        )
        db.add(new_profile)
        db.commit()
        print("✅ Created Profile")

        # 3. CRUD Gap Analysis
        gap = UPSCGapAnalysis(
            profile_id=new_profile.id,
            chapter_id=5,
            status="knowledge_gap",
            gap_details={"missingConcept": "Preamble"}
        )
        db.add(gap)
        db.commit()
        print("✅ Created Gap Analysis Entry")

        # 4. CRUD Unlock
        unlock = UPSCUnlockTransaction(
            profile_id=new_profile.id,
            level_unlocked="level2",
            amount_paid=499.0
        )
        db.add(unlock)
        db.commit()
        print("✅ Created Unlock Transaction")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_synapse_db()
