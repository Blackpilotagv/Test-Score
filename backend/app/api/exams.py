from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.models import Exam, ExamStatus
from app.schemas.schemas import ExamOut

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("", response_model=List[ExamOut])
def get_all_exams(db: Session = Depends(get_db)):
    """Fetch the 3 supported TNPSC Exam categories: Group 1, Group 2, Group 4."""
    exams = db.query(Exam).filter(Exam.status == ExamStatus.ACTIVE).all()
    return exams

@router.get("/{exam_id}", response_model=ExamOut)
def get_exam_by_id(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam category not found")
    return exam
