import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
from app.database import get_db
from app.models.auth_models import User

# Настройка алгоритма хеширования (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Загружаем настройки из .env
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_TTL = int(os.getenv("ACCESS_TOKEN_TTL", 60))
REFRESH_TOKEN_TTL = int(os.getenv("REFRESH_TOKEN_TTL", 10080))

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_TTL)
    # Payload - полезная нагрузка токена
    to_encode = {
        "sub": str(user_id),  # subject (обычно id)
        "username": username,
        "type": "access",
        "exp": expire  # expiration (срок годности)
    }
    # Шифруем данные секретным ключом
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_TTL)
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Расшифровываем токен секретным ключом
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except InvalidTokenError:
        # Если токен протух или подделан - выкидываем ошибку
        raise credentials_exception

    # Ищем пользователя в базе
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user