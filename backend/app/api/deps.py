from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.database.session import get_db
from app.models.models import UserRole, UserStatus, MongoDoc, to_mongo_doc
from app.schemas.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(db = Depends(get_db), token: str = Depends(oauth2_scheme)) -> MongoDoc:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception

    user_data = db.users.find_one({"id": int(token_data.user_id)})
    if user_data is None:
        raise credentials_exception
    user = to_mongo_doc(user_data)
    if user.status == UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="User account is disabled")

    return user

def get_admin_user(current_user: MongoDoc = Depends(get_current_user)) -> MongoDoc:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
