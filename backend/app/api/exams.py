from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database.session import get_db
from app.models.models import ExamStatus, to_mongo_doc, to_mongo_docs
from app.schemas.schemas import ExamOut

router = APIRouter(prefix="/exams", tags=["Exams"])

@router.get("", response_model=List[ExamOut])
def get_all_exams(db = Depends(get_db)):
    """Fetch the 3 supported TNPSC Exam categories: Group 1, Group 2, Group 4."""
    exams = list(db.exams.find({"status": ExamStatus.ACTIVE}))
    return to_mongo_docs(exams)

@router.get("/{exam_id}", response_model=ExamOut)
def get_exam_by_id(exam_id: int, db = Depends(get_db)):
    exam = db.exams.find_one({"id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam category not found")
    return to_mongo_doc(exam)
