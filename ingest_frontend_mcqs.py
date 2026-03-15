import json
import logging
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import app.db.base  # This registers all models with SQLAlchemy
from app.models.user import User
from app.models.course import Course, CourseCategory, CourseLevel
from app.models.question_bank import QuestionBank, BankQuestion
import app.models.student_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_mcqs():
    db = SessionLocal()
    try:
        # Get or create admin user
        instructor = db.query(User).filter(User.email == "instructor@eduecosystem.com").first()
        if not instructor:
            instructor = db.query(User).first()
            if not instructor:
                instructor = User(
                    email="instructor@eduecosystem.com",
                    hashed_password="dummy",
                    full_name="System Admin",
                    is_active=True,
                    role="admin",
                )
                db.add(instructor)
                db.commit()
                db.refresh(instructor)
        
        # Get or create a base Course for UPSC
        course = db.query(Course).filter(Course.title == "UPSC Master Question Bank Repository").first()
        if not course:
            course = Course(
                title="UPSC Master Question Bank Repository",
                slug="upsc-master-question-bank-repository",
                description="Centralized repository containing 45,000+ unified MCQs for all subjects.",
                instructor_id=instructor.id,
                price=0,
                is_published=False,
                total_duration_minutes=0
            ) 
            db.add(course)
            db.commit()
            db.refresh(course)
        
        logger.info(f"Using Instructor ID: {instructor.id}, Course ID: {course.id}")

        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'all_mcqs_extracted.json')
        logger.info(f"Loading JSON from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            mcqs = json.load(f)
            
        logger.info(f"Loaded {len(mcqs)} questions from JSON. Grouping by Export Name...")
        
        # Group by _exportName to create QuestionBanks
        banks_data = {}
        for q in mcqs:
            bank_name = q.get('_exportName', 'Unnamed Bank')
            if bank_name not in banks_data:
                banks_data[bank_name] = []
            banks_data[bank_name].append(q)
            
        logger.info(f"Found {len(banks_data)} distinct Question Banks to create.")
        
        total_inserted = 0
        
        # We will delete existing banks with these names to prevent duplicates if script runs twice
        
        for bank_name, questions in banks_data.items():
            # Check if Bank exists
            bank = db.query(QuestionBank).filter(QuestionBank.title == bank_name).first()
            if not bank:
                bank = QuestionBank(
                    course_id=course.id,
                    instructor_id=instructor.id,
                    title=bank_name,
                    description=f"Auto-imported bank containing {len(questions)} questions from frontend ({questions[0].get('_sourceFile', 'unknown file')}).",
                    category="UPSC",
                    difficulty_level="medium",
                    is_active=True
                )
                db.add(bank)
                db.flush() # get ID
            
            # Map questions
            db_questions = []
            for q in questions:
                # Map difficulty
                raw_diff = str(q.get('difficulty', 'medium')).lower()
                diff = 'medium'
                if 'easy' in raw_diff: diff = 'easy'
                elif 'hard' in raw_diff or 'advanced' in raw_diff: diff = 'hard'
                
                # Try to extract the actual text of correct answer if it's an index
                options = q.get('options', [])
                correct_ans = str(q.get('correctAnswer', ''))
                
                # In many frontend files, correctAnswer is an integer index covering 0-3
                try:
                    ans_idx = int(float(correct_ans))
                    if 0 <= ans_idx < len(options):
                        correct_ans = options[ans_idx]
                except (ValueError, TypeError):
                    pass # Keep as string if not an integer index
                
                question_text = q.get('question', '')
                if not question_text:
                    question_text = q.get('statement', '') # sometimes history pyq uses statement
                if not question_text:
                    question_text = "Unknown Question text"
                    
                db_q = BankQuestion(
                    instructor_id=instructor.id,
                    text=question_text,
                    type="multiple_choice",
                    points=1,
                    difficulty=diff,
                    options=json.dumps(options),
                    correct_answer=correct_ans,
                    explanation=q.get('explanation', ''),
                    tags=q.get('subtopic', '') or q.get('topic', '') or "UPSC"
                )
                db_questions.append(db_q)
            
            # Bulk save questions
            db.add_all(db_questions)
            db.flush()
            
            # Associate
            for db_q in db_questions:
                bank.questions.append(db_q)
                
            db.commit()
            total_inserted += len(questions)
            logger.info(f"Saved Question Bank: {bank_name} with {len(questions)} questions.")

        logger.info(f"✅ Successfully ingested {total_inserted} total MCQs into to PostgreSQL database!")

    except Exception as e:
        logger.error(f"Error ingesting MCQs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_mcqs()
