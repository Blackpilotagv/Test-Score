from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.models import User, Test, Payment, PaymentStatus, PastYearPaper
from app.schemas.schemas import CreateOrderRequest, ProcessMockPaymentRequest, PaymentOut
from app.api.deps import get_current_user
from app.services.payment_service import get_payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-order")
def create_payment_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_price = 0.0
    test_id = None
    past_year_paper_id = None

    if req.past_year_paper_id:
        paper = db.query(PastYearPaper).filter(PastYearPaper.id == req.past_year_paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Past year paper not found")
        target_price = paper.price
        past_year_paper_id = paper.id
    elif req.test_id:
        test = db.query(Test).filter(Test.id == req.test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        target_price = test.price
        test_id = test.id
    else:
        raise HTTPException(status_code=400, detail="Must specify test_id or past_year_paper_id")

    # Check if already purchased
    query = db.query(Payment).filter(
        Payment.user_id == current_user.id,
        Payment.status == PaymentStatus.SUCCESS
    )
    if past_year_paper_id:
        query = query.filter(Payment.past_year_paper_id == past_year_paper_id)
    else:
        query = query.filter(Payment.test_id == test_id)

    existing_success = query.first()

    if existing_success:
        return {
            "status": "ALREADY_PURCHASED",
            "message": "You have already unlocked access.",
            "test_id": test_id,
            "past_year_paper_id": past_year_paper_id
        }

    payment_service = get_payment_service()
    order_data = payment_service.create_order(
        db=db,
        user_id=current_user.id,
        test_id=test_id,
        past_year_paper_id=past_year_paper_id,
        amount=target_price
    )
    return order_data

@router.post("/process-mock")
def process_mock_payment(
    req: ProcessMockPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Development Mode Mock Gateway Callback Simulator.
    Processes user choice on the 'DEMO / TEST PAYMENT' screen (Test Payment - Success / Failed).
    """
    payment_service = get_payment_service()
    try:
        payment = payment_service.process_payment_result(
            db=db,
            order_id=req.order_id,
            success=req.success
        )
        return {
            "status": payment.status.value,
            "payment_id": payment.gateway_payment_id,
            "test_id": payment.test_id,
            "past_year_paper_id": payment.past_year_paper_id,
            "message": "Payment marked SUCCESS! Access unlocked." if req.success else "Payment marked FAILED. Item remains locked."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[PaymentOut])
def get_payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).order_by(Payment.id.desc()).all()
    out = []
    for p in payments:
        title = ""
        if p.past_year_paper:
            title = p.past_year_paper.title
        elif p.test:
            title = p.test.title
        out.append(PaymentOut(
            id=p.id,
            user_id=p.user_id,
            test_id=p.test_id,
            past_year_paper_id=p.past_year_paper_id,
            test_title=title,
            amount=p.amount,
            gateway_order_id=p.gateway_order_id,
            gateway_payment_id=p.gateway_payment_id,
            status=p.status,
            payment_method=p.payment_method,
            created_at=p.created_at
        ))
    return out
