from abc import ABC, abstractmethod
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.session import get_next_sequence
from app.models.models import PaymentStatus, PaymentMethod, to_mongo_doc
from app.core.config import settings

class BasePaymentService(ABC):
    @abstractmethod
    def create_order(self, db, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        """Create a payment order record and return metadata for the client payment flow."""
        pass

    @abstractmethod
    def process_payment_result(self, db, order_id: str, success: bool):
        """Process payment result callback and update payment status."""
        pass


class MockPaymentService(BasePaymentService):
    """
    Development Mode Mock Payment Service.
    Simulates payment gateway workflow without real card transactions or live API keys.
    """
    def create_order(self, db, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        order_id = f"ORDER_MOCK_{uuid.uuid4().hex[:12].upper()}"

        query_filter = {"user_id": user_id, "status": PaymentStatus.SUCCESS}
        if past_year_paper_id:
            query_filter["past_year_paper_id"] = past_year_paper_id
        elif test_id:
            query_filter["test_id"] = test_id

        existing_doc = db.payments.find_one(query_filter)
        if existing_doc:
            existing_payment = to_mongo_doc(existing_doc)
            return {
                "order_id": existing_payment.gateway_order_id,
                "amount": existing_payment.amount,
                "status": "ALREADY_PURCHASED",
                "payment_id": existing_payment.id
            }

        payment_id = get_next_sequence(db, "payment_id")
        now = datetime.utcnow()
        payment_doc = {
            "id": payment_id,
            "user_id": user_id,
            "test_id": test_id,
            "past_year_paper_id": past_year_paper_id,
            "amount": amount,
            "gateway_order_id": order_id,
            "gateway_payment_id": None,
            "status": PaymentStatus.PENDING,
            "payment_method": PaymentMethod.MOCK,
            "created_at": now
        }
        db.payments.insert_one(payment_doc)

        return {
            "order_id": order_id,
            "amount": amount,
            "status": "PENDING",
            "payment_id": payment_id,
            "mode": "DEMO / TEST PAYMENT"
        }

    def process_payment_result(self, db, order_id: str, success: bool):
        payment_doc = db.payments.find_one({"gateway_order_id": order_id})
        if not payment_doc:
            raise ValueError(f"Order {order_id} not found.")

        if success:
            new_status = PaymentStatus.SUCCESS
            gateway_pay_id = f"PAY_MOCK_{uuid.uuid4().hex[:10].upper()}"
        else:
            new_status = PaymentStatus.FAILED
            gateway_pay_id = None

        db.payments.update_one(
            {"gateway_order_id": order_id},
            {"$set": {"status": new_status, "gateway_payment_id": gateway_pay_id}}
        )
        updated_doc = db.payments.find_one({"gateway_order_id": order_id})
        return to_mongo_doc(updated_doc)


class ProductionPaymentService(BasePaymentService):
    def create_order(self, db, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        raise NotImplementedError("Production payment gateway disabled in Phase 1. Use Mock Payment Service.")

    def process_payment_result(self, db, order_id: str, success: bool):
        raise NotImplementedError("Production payment gateway verification disabled in Phase 1.")


def get_payment_service() -> BasePaymentService:
    if settings.PAYMENT_MODE.upper() == "MOCK":
        return MockPaymentService()
    else:
        return ProductionPaymentService()
