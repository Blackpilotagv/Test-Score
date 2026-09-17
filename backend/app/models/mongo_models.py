import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"

class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"

class ExamStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class TestStatus(str, enum.Enum):
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentMethod(str, enum.Enum):
    MOCK = "MOCK"
    ADMIN_GRANTED = "ADMIN_GRANTED"
    RAZORPAY = "RAZORPAY"

class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"

class QuestionSetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class PastYearPaperStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class MongoDoc(dict):
    """Dictionary subclass supporting both dot notation (doc.id) and dict notation (doc['id'])."""
    def __getattr__(self, name: str) -> Any:
        try:
            val = self[name]
            if isinstance(val, dict) and not isinstance(val, MongoDoc):
                return MongoDoc(val)
            elif isinstance(val, list):
                return [MongoDoc(x) if isinstance(x, dict) and not isinstance(x, MongoDoc) else x for x in val]
            return val
        except KeyError:
            raise AttributeError(f"'MongoDoc' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'MongoDoc' object has no attribute '{name}'")

def to_mongo_doc(d: Optional[Dict[str, Any]]) -> Optional[MongoDoc]:
    if d is None:
        return None
    return MongoDoc(d)

def to_mongo_docs(docs: List[Dict[str, Any]]) -> List[MongoDoc]:
    return [MongoDoc(d) for d in docs]
