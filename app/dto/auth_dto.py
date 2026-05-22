from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date, datetime
from typing import List

class UserDTO(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True) # from_attributes позволяет читать данные из базы SQLAlchemy
    id: int
    username: str
    email: EmailStr
    birthday: date

class TokenInfoDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: int
    created_at: str
    expires_at: str
    is_used: bool

class TokenListDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    tokens: List[TokenInfoDTO]

class AuthSuccessDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    access_token: str
    refresh_token: str
    user: UserDTO

# --- БЛОК ЛАБОРАТОРНОЙ РАБОТЫ №3: РОЛИ И РАЗРЕШЕНИЯ ---

class RoleDTO(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None = None
    created_at: datetime
    created_by: int

class RoleCollectionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    roles: List[RoleDTO]
    total: int # Мета-информация: общее количество ролей

class PermissionDTO(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)
    id: int
    name: str
    slug: str
    description: str | None = None
    created_at: datetime
    created_by: int

class PermissionCollectionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)
    permissions: List[PermissionDTO]
    total: int # Мета-информация: общее количество разрешений