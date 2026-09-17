from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pymongo import DESCENDING
from app.database.session import get_db
from app.models.models import PaymentStatus, to_mongo_doc
from app.schemas.schemas import CreateOrderRequest, ProcessMockPaymentRequest, PaymentOut
from app.api.deps import get_current_user
from app.services.payment_service import get_payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-order")
def create_payment_order(
    req: CreateOrderRequest,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    target_price = 0.0
    test_id = None
    past_year_paper_id = None

    if req.past_year_paper_id:
        paper = db.past_year_papers.find_one({"id": req.past_year_paper_id})
        if not paper:
            raise HTTPException(status_code=404, detail="Past year paper not found")
        target_price = paper["price"]
        past_year_paper_id = paper["id"]
    elif req.test_id:
        test = db.tests.find_one({"id": req.test_id})
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        target_price = test["price"]
        test_id = test["id"]
    else:
        raise HTTPException(status_code=400, detail="Must specify test_id or past_year_paper_id")

    query_filter = {"user_id": current_user.id, "status": PaymentStatus.SUCCESS}
    if past_year_paper_id:
        query_filter["past_year_paper_id"] = past_year_paper_id
    else:
        query_filter["test_id"] = test_id

    existing_success = db.payments.find_one(query_filter)

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
    db = Depends(get_db),
    current_user = Depends(get_current_user)
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
        status_val = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
        return {
            "status": status_val,
            "payment_id": payment.gateway_payment_id,
            "test_id": payment.test_id,
            "past_year_paper_id": payment.past_year_paper_id,
            "message": "Payment marked SUCCESS! Access unlocked." if req.success else "Payment marked FAILED. Item remains locked."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[PaymentOut])
def get_payment_history(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    payment_docs = list(db.payments.find({"user_id": current_user.id}, sort=[("id", DESCENDING)]))
    out = []
    for p_doc in payment_docs:
        p = to_mongo_doc(p_doc)
        title = ""
        if p.past_year_paper_id:
            paper_doc = db.past_year_papers.find_one({"id": p.past_year_paper_id})
            title = paper_doc["title"] if paper_doc else ""
        elif p.test_id:
            test_doc = db.tests.find_one({"id": p.test_id})
            title = test_doc["title"] if test_doc else ""

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
