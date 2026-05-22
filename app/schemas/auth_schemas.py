import re
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.dto.auth_dto import UserDTO, RoleDTO, PermissionDTO


# Общие правила для пароля
def validate_complex_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Пароль должен быть не короче 8 символов")
    if not re.search(r"\d", password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    if not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password):
        raise ValueError("Пароль должен содержать символы в верхнем и нижнем регистре")
    if not re.search(r"[@$!%*?&#^_-]", password):
        raise ValueError("Пароль должен содержать хотя бы один специальный символ")
    return password


# 1. Схема для Регистрации (RegisterRequest из ТЗ)
class RegisterSchema(BaseModel):
    # Field ограничивает длину и проверяет паттерн: Заглавная буква + латиница (минимум 7 символов)
    username: str = Field(..., min_length=7, pattern=r"^[A-Z][a-zA-Z]{6,}$")
    email: EmailStr
    password: str
    c_password: str
    birthday: date

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str):
        return validate_complex_password(v)

    @field_validator("birthday")
    @classmethod
    def check_age(cls, v: date):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14:
            raise ValueError("Возраст должен быть не менее 14 лет")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> 'RegisterSchema':
        if self.password != self.c_password:
            raise ValueError("Пароли не совпадают")
        return self

    # Требование ТЗ: метод, возвращающий экземпляр DTO
    def toDTO(self, user_id: int) -> UserDTO:
        return UserDTO(
            id=user_id,
            username=self.username,
            email=self.email,
            birthday=self.birthday
        )

# 2. Схема для Логина (LoginRequest из ТЗ)
class LoginSchema(BaseModel):
    username: str = Field(..., min_length=7, pattern=r"^[A-Z][a-zA-Z]{6,}$")
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str):
        return validate_complex_password(v)

# Валидация для Ролей
class StoreRoleRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Имя роли")
    # Регулярное выражение разрешает только латиницу, цифры, дефис и подчёркивание
    slug: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", description="Уникальный шифр роли")
    description: str | None = None

    def toDTO(self, role_id: int, created_by: int) -> RoleDTO:
        """Преобразует входной запрос в объект RoleDTO"""
        return RoleDTO(
            id=role_id,
            name=self.name,
            slug=self.slug,
            description=self.description,
            created_at=date.today(), # Будет преобразовано в datetime автоматически
            created_by=created_by
        )

class UpdateRoleRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None):
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Slug должен содержать только латиницу, цифры, дефис или подчёркивание")
        return v

# Валидация для Разрешений (Прав)
class StorePermissionRequest(BaseModel):
    name: str = Field(..., min_length=2)
    slug: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    description: str | None = None

    def toDTO(self, perm_id: int, created_by: int) -> PermissionDTO:
        """Преобразует входной запрос в объект PermissionDTO [cite: 48]"""
        return PermissionDTO(
            id=perm_id,
            name=self.name,
            slug=self.slug,
            description=self.description,
            created_at=date.today(),
            created_by=created_by
        )

class UpdatePermissionRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None):
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Slug должен содержать только латиницу, цифры, дефис или подчёркивание")
        return v

class AttachUserRoleRequest(BaseModel):
    role_id: int = Field(..., description="ID роли, которую нужно присвоить пользователю")