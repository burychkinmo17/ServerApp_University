from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship

# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Пароль в открытом виде не храним!
    birthday = Column(Date, nullable=False)
    roles = relationship("Role", secondary="role_user", viewonly=True)

# Таблица для отслеживания Refresh-токенов (сессий)
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Связь с пользователем
    token_hash = Column(String, unique=True, index=True, nullable=False)  # Хеш токена
    is_used = Column(Boolean, default=False)  # Защита от повторного использования
    expires_at = Column(DateTime, nullable=False)  # Когда протухнет
    created_at = Column(DateTime, default=datetime.utcnow)  # Когда создан


# Промежуточная таблица связи Ролей и Пользователей (Многие-ко-многим)
class RoleUser(Base):
    __tablename__ = "role_user"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # Служебные поля по ТЗ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)  # ID юзера, который выдал роль
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Для мягкого удаления
    deleted_by = Column(Integer, nullable=True)


# Промежуточная таблица связи Разрешений и Ролей (Многие-ко-многим)
class PermissionRole(Base):
    __tablename__ = "permission_role"

    id = Column(Integer, primary_key=True, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    # Служебные поля по ТЗ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)


# Таблица Ролей
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Наименование (Администратор)
    slug = Column(String, unique=True, nullable=False)  # Шифр (admin)
    description = Column(Text, nullable=True)  # Описание

    # Служебные поля
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)
    permissions = relationship("Permission", secondary="permission_role", viewonly=True)

# 4. Таблица Разрешений (Прав)
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Наименование (Удаление пользователей)
    slug = Column(String, unique=True, nullable=False)  # Шифр (delete-users)
    description = Column(Text, nullable=True)  # Описание

    # Служебные поля
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, nullable=True)