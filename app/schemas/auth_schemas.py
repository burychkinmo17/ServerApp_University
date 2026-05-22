import re
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.dto.auth_dto import UserDTO  # Импортируем DTO для метода toDTO


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