from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
import os
from datetime import datetime, timedelta
from app.schemas.auth_schemas import RegisterSchema, LoginSchema
from app.dto.auth_dto import UserDTO, AuthSuccessDTO
from app.services.auth_service import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.models.auth_models import User, RefreshToken
from fastapi import Depends
from app.services.auth_service import get_current_user
from app.dto.auth_dto import TokenListDTO, TokenInfoDTO

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterSchema, db: Session = Depends(get_db)):
    # Проверяем уникальность
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        # Если нашли совпадение, прерываем регистрацию с ошибкой 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или именем уже существует"
        )

    # Слепок пользователя для базы данных
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        birthday=user_data.birthday
    )

    #Сохраняем в базу данных
    db.add(new_user)
    db.commit()  # Подтверждаем транзакцию
    db.refresh(new_user)  # Обновляем объект, чтобы база присвоила ему ID

    return user_data.toDTO(new_user.id)


@router.post("/login", response_model=AuthSuccessDTO, status_code=status.HTTP_200_OK)
def login(credentials: LoginSchema, db: Session = Depends(get_db)):

    # Проверяем, существует ли пользователь и правильный ли пароль
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )  # [cite: 739]

    # Проверяем лимит активных сессий
    MAX_TOKENS = int(os.getenv("MAX_ACTIVE_TOKENS", 5))

    active_sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.is_used == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).order_by(RefreshToken.created_at.asc()).all()

    # Если много, отзываем самую старую
    if len(active_sessions) >= MAX_TOKENS:
        oldest_session = active_sessions[0]
        oldest_session.is_used = True
        db.commit()

    # Генерируем новые токены
    access_token = create_access_token(user.id, user.username)
    refresh_token = create_refresh_token(user.id)

    # Сохраняем Refresh-токен в базу
    ttl_minutes = int(os.getenv("REFRESH_TOKEN_TTL", 10080))
    new_session = RefreshToken(
        user_id=user.id,
        token_hash=get_password_hash(refresh_token),  # Хешируем токен как пароль
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
    )
    db.add(new_session)
    db.commit()

    # Возвращаем успешный ответ
    return AuthSuccessDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )

@router.get("/me", response_model=UserDTO)
def get_me(current_user: User = Depends(get_current_user)):
    return UserDTO.model_validate(current_user)


@router.get("/tokens", response_model=TokenListDTO)
def get_my_tokens(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Ищем все неиспользованные токены этого пользователя, которые еще не протухли
    active_sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_used == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()

    tokens_info = [
        TokenInfoDTO(
            id=session.id,
            created_at=session.created_at.isoformat(),
            expires_at=session.expires_at.isoformat(),
            is_used=session.is_used
        ) for session in active_sessions
    ]

    return TokenListDTO(tokens=tokens_info)


@router.post("/out", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    latest_session = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_used == False
    ).order_by(RefreshToken.created_at.desc()).first()

    if latest_session:
        latest_session.is_used = True
        db.commit()

    return {"message": "Успешно вышли из системы"}

@router.post("/out_all", status_code=status.HTTP_200_OK)
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    active_sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_used == False
    ).all()

    for session in active_sessions:
        session.is_used = True

    db.commit()

    return {"message": "Успешно вышли со всех устройств"}