from typing import Optional, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.student_report import StudentReport
from app.schemas.student_report import StudentReportCreate, StudentReportUpdate

class CRUDStudentReport(CRUDBase[StudentReport, StudentReportCreate, StudentReportUpdate]):
    def get_by_report_key(self, db: Session, *, user_id: int, report_key: str) -> Optional[StudentReport]:
        return db.query(StudentReport).filter(
            StudentReport.user_id == user_id, 
            StudentReport.report_key == report_key
        ).first()

    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[StudentReport]:
        return db.query(StudentReport).filter(StudentReport.user_id == user_id).offset(skip).limit(limit).all()
        
    def get_by_user_and_type(self, db: Session, *, user_id: int, report_type: str, skip: int = 0, limit: int = 100) -> List[StudentReport]:
        return db.query(StudentReport).filter(
            StudentReport.user_id == user_id,
            StudentReport.report_type == report_type
        ).offset(skip).limit(limit).all()

student_report = CRUDStudentReport(StudentReport)
