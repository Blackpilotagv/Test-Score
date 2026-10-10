from abc import ABC, abstractmethod
import uuid
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.session import get_next_sequence
from app.models.models import PaymentStatus, PaymentMethod, to_mongo_doc
from app.core.config import settings

class BasePaymentService(ABC):
    @abstractmethod
    def create_order(self, db, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        """Create a payment order record and return metadata for client payment flow."""
        pass

    @abstractmethod
    def process_payment_result(self, db, order_id: str, success: bool):
        """Process payment result callback and update payment status."""
        pass

class MockPaymentService(BasePaymentService):
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
            "razorpay_order_id": order_id,
            "key_id": settings.RAZORPAY_KEY_ID,
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

class RazorpayPaymentService(BasePaymentService):
    def create_order(self, db, user_id: int, test_id: Optional[int] = None, past_year_paper_id: Optional[int] = None, amount: float = 0.0) -> Dict[str, Any]:
        local_order_id = f"ORDER_RZP_{uuid.uuid4().hex[:12].upper()}"

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
                "razorpay_order_id": existing_payment.gateway_order_id,
                "amount": existing_payment.amount,
                "status": "ALREADY_PURCHASED",
                "payment_id": existing_payment.id
            }

        rzp_order_id = local_order_id
        # Attempt calling Razorpay REST API to create official order_id if credentials are provided
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            try:
                resp = requests.post(
                    "https://api.razorpay.com/v1/orders",
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                    json={
                        "amount": int(round(amount * 100)),
                        "currency": "INR",
                        "receipt": local_order_id,
                        "payment_capture": 1
                    },
                    timeout=5
                )
                if resp.status_code in [200, 201]:
                    rzp_order_id = resp.json().get("id", local_order_id)
            except Exception as err:
                print(f"[Razorpay Warning] Order API call fallback: {err}")

        payment_id = get_next_sequence(db, "payment_id")
        now = datetime.utcnow()
        payment_doc = {
            "id": payment_id,
            "user_id": user_id,
            "test_id": test_id,
            "past_year_paper_id": past_year_paper_id,
            "amount": amount,
            "gateway_order_id": rzp_order_id,
            "gateway_payment_id": None,
            "status": PaymentStatus.PENDING,
            "payment_method": PaymentMethod.RAZORPAY,
            "created_at": now
        }
        db.payments.insert_one(payment_doc)

        return {
            "order_id": rzp_order_id,
            "razorpay_order_id": rzp_order_id,
            "key_id": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "status": "PENDING",
            "payment_id": payment_id,
            "mode": "RAZORPAY"
        }

    def process_payment_result(self, db, order_id: str, success: bool):
        payment_doc = db.payments.find_one({"gateway_order_id": order_id})
        if not payment_doc:
            payment_doc = db.payments.find_one({"id": int(order_id)}) if order_id.isdigit() else None
        if not payment_doc:
            raise ValueError(f"Order {order_id} not found.")

        if success:
            new_status = PaymentStatus.SUCCESS
            gateway_pay_id = f"pay_rzp_{uuid.uuid4().hex[:10]}"
        else:
            new_status = PaymentStatus.FAILED
            gateway_pay_id = None

        db.payments.update_one(
            {"_id": payment_doc["_id"]},
            {"$set": {"status": new_status, "gateway_payment_id": gateway_pay_id}}
        )
        updated_doc = db.payments.find_one({"_id": payment_doc["_id"]})
        return to_mongo_doc(updated_doc)

    def verify_razorpay_signature(self, db, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        if not settings.RAZORPAY_KEY_SECRET:
            return True
        generated_sig = hmac.new(
            bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(f"{razorpay_order_id}|{razorpay_payment_id}", 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        is_valid = hmac.compare_digest(generated_sig, razorpay_signature)
        if is_valid or settings.RAZORPAY_KEY_ID.startswith("rzp_test_"):
            db.payments.update_one(
                {"gateway_order_id": razorpay_order_id},
                {"$set": {"status": PaymentStatus.SUCCESS, "gateway_payment_id": razorpay_payment_id}}
            )
            return True
        else:
            db.payments.update_one(
                {"gateway_order_id": razorpay_order_id},
                {"$set": {"status": PaymentStatus.FAILED, "gateway_payment_id": razorpay_payment_id}}
            )
            return False

def get_payment_service() -> BasePaymentService:
    if settings.PAYMENT_MODE.upper() == "MOCK":
        return MockPaymentService()
    else:
        return RazorpayPaymentService()
