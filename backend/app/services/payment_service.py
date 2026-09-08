from abc import ABC, abstractmethod
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Payment, PaymentStatus, PaymentMethod, Test, PastYearPaper
from app.core.config import settings

class BasePaymentService(ABC):
    @abstractmethod
    def create_order(self, db: Session, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        """Create a payment order record and return metadata for the client payment flow."""
        pass

    @abstractmethod
    def process_payment_result(self, db: Session, order_id: str, success: bool) -> Payment:
        """Process payment result callback and update payment status."""
        pass


class MockPaymentService(BasePaymentService):
    """
    Development Mode Mock Payment Service.
    Simulates payment gateway workflow without real card transactions or live API keys.
    """
    def create_order(self, db: Session, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        order_id = f"ORDER_MOCK_{uuid.uuid4().hex[:12].upper()}"
        
        # Check if pending or existing payment already exists
        filter_kwargs = {Payment.user_id: user_id, Payment.status: PaymentStatus.SUCCESS}
        query = db.query(Payment).filter(Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS)
        if past_year_paper_id:
            query = query.filter(Payment.past_year_paper_id == past_year_paper_id)
        elif test_id:
            query = query.filter(Payment.test_id == test_id)

        existing_payment = query.first()

        if existing_payment:
            return {
                "order_id": existing_payment.gateway_order_id,
                "amount": existing_payment.amount,
                "status": "ALREADY_PURCHASED",
                "payment_id": existing_payment.id
            }

        payment = Payment(
            user_id=user_id,
            test_id=test_id,
            past_year_paper_id=past_year_paper_id,
            amount=amount,
            gateway_order_id=order_id,
            gateway_payment_id=None,
            status=PaymentStatus.PENDING,
            payment_method=PaymentMethod.MOCK
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "order_id": order_id,
            "amount": amount,
            "status": "PENDING",
            "payment_id": payment.id,
            "mode": "DEMO / TEST PAYMENT"
        }

    def process_payment_result(self, db: Session, order_id: str, success: bool) -> Payment:
        payment = db.query(Payment).filter(Payment.gateway_order_id == order_id).first()
        if not payment:
            raise ValueError(f"Order {order_id} not found.")

        if success:
            payment.status = PaymentStatus.SUCCESS
            payment.gateway_payment_id = f"PAY_MOCK_{uuid.uuid4().hex[:10].upper()}"
        else:
            payment.status = PaymentStatus.FAILED

        db.commit()
        db.refresh(payment)
        return payment


class ProductionPaymentService(BasePaymentService):
    """
    Future Production Payment Service (Razorpay / Gateway Integration).
    """
    def create_order(self, db: Session, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        # Place real Razorpay SDK order creation logic here
        raise NotImplementedError("Production payment gateway disabled in Phase 1. Use Mock Payment Service.")

    def process_payment_result(self, db: Session, order_id: str, success: bool) -> Payment:
        raise NotImplementedError("Production payment gateway verification disabled in Phase 1.")


def get_payment_service() -> BasePaymentService:
    if settings.PAYMENT_MODE.upper() == "MOCK":
        return MockPaymentService()
    else:
        return ProductionPaymentService()
