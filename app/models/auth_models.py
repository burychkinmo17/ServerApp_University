from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Пароль в открытом виде не храним!
    birthday = Column(Date, nullable=False)


# Таблица для отслеживания Refresh-токенов (сессий)
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Связь с пользователем
    token_hash = Column(String, unique=True, index=True, nullable=False)  # Хеш токена
    is_used = Column(Boolean, default=False)  # Защита от повторного использования
    expires_at = Column(DateTime, nullable=False)  # Когда протухнет
    created_at = Column(DateTime, default=datetime.utcnow)  # Когда создан