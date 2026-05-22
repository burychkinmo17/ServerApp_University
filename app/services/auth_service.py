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
from app.models.auth_models import RoleUser, PermissionRole, Role, Permission

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

class PermissionChecker:
    def __init__(self, required_permission_slug: str):
        # Принимаем шифр разрешения, который нужен для этого маршрута
        self.required_permission_slug = required_permission_slug

    def __call__(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """
        Этот метод автоматически вызывается FastAPI при проверке Depends().
        Ищет, есть ли у юзера через его роли нужное разрешение.
        """
        # Находим все активные (не удаленные) роли пользователя
        user_roles = db.query(RoleUser).filter(
            RoleUser.user_id == current_user.id,
            RoleUser.deleted_at == None
        ).subquery()

        # Ищем, привязано ли к этим ролям нужное нам разрешение (проверяем всю цепочку)
        has_permission = db.query(PermissionRole).join(
            Permission, Permission.id == PermissionRole.permission_id
        ).filter(
            PermissionRole.role_id.in_(db.query(user_roles.c.role_id)),
            Permission.slug == self.required_permission_slug,
            PermissionRole.deleted_at == None,
            Permission.deleted_at == None
        ).first()

        # Если в цепочке ничего не нашли — 403 ошибка
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется разрешение: {self.required_permission_slug}"
            )

        return current_user