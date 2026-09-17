from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database.session import get_db, get_next_sequence
from app.models.models import UserRole, UserStatus, MongoDoc, to_mongo_doc
from app.schemas.schemas import UserCreate, UserOut, Token, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db = Depends(get_db)):
    # Check if email exists
    if db.users.find_one({"email": user_in.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if mobile exists
    if db.users.find_one({"mobile": user_in.mobile}):
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    user_id = get_next_sequence(db, "user_id")
    now = datetime.utcnow()
    user_doc = {
        "id": user_id,
        "name": user_in.name,
        "email": user_in.email.lower(),
        "mobile": user_in.mobile,
        "password_hash": get_password_hash(user_in.password),
        "role": UserRole.STUDENT,
        "status": UserStatus.ACTIVE,
        "created_at": now,
        "updated_at": now
    }
    db.users.insert_one(user_doc)
    return to_mongo_doc(user_doc)

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db = Depends(get_db)):
    # Username can be email or mobile
    user_data = db.users.find_one({
        "$or": [
            {"email": user_in.username.lower()},
            {"mobile": user_in.username}
        ]
    })

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid email/mobile or password")

    user = to_mongo_doc(user_data)
    if not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email/mobile or password")

    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Account disabled by administrator")

    role_str = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    access_token = create_access_token(subject=user.id, role=role_str)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_str,
        "user_id": user.id,
        "name": user.name
    }

@router.post("/login/form", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    return login(UserLogin(username=form_data.username, password=form_data.password), db=db)

@router.get("/me", response_model=UserOut)
def get_me(current_user: MongoDoc = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
