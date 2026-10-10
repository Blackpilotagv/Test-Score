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
    Development Mode / Test Gateway Callback Simulator.
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

@router.post("/verify-razorpay")
def verify_razorpay_payment(
    req: dict,
    db = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Verifies Razorpay payment signature and unlocks exam access on success.
    """
    order_id = req.get("razorpay_order_id") or req.get("order_id")
    payment_id = req.get("razorpay_payment_id") or req.get("payment_id")
    signature = req.get("razorpay_signature", "")

    if not order_id:
        raise HTTPException(status_code=400, detail="Missing order_id")

    payment_service = get_payment_service()
    if hasattr(payment_service, 'verify_razorpay_signature'):
        is_valid = payment_service.verify_razorpay_signature(
            db=db,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id or "pay_rzp_mock",
            razorpay_signature=signature
        )
        if is_valid:
            pmt = db.payments.find_one({"gateway_order_id": order_id})
            return {
                "status": "SUCCESS",
                "message": "Payment verified successfully. Exam unlocked!",
                "test_id": pmt.get("test_id") if pmt else None,
                "past_year_paper_id": pmt.get("past_year_paper_id") if pmt else None
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
    else:
        # Fallback for mock service
        pmt = payment_service.process_payment_result(db, order_id=order_id, success=True)
        return {
            "status": "SUCCESS",
            "message": "Payment marked SUCCESS! Access unlocked.",
            "test_id": pmt.test_id,
            "past_year_paper_id": pmt.past_year_paper_id
        }

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
