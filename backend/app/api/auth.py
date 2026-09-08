from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, UserRole, UserStatus
from app.schemas.schemas import UserCreate, UserOut, Token, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    if db.query(User).filter(User.email == user_in.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if mobile exists
    if db.query(User).filter(User.mobile == user_in.mobile).first():
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        mobile=user_in.mobile,
        password_hash=get_password_hash(user_in.password),
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Username can be email or mobile
    query = db.query(User).filter(
        (User.email == user_in.username.lower()) | (User.mobile == user_in.username)
    )
    user = query.first()

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email/mobile or password")

    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Account disabled by administrator")

    access_token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "user_id": user.id,
        "name": user.name
    }

@router.post("/login/form", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(UserLogin(username=form_data.username, password=form_data.password), db=db)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
