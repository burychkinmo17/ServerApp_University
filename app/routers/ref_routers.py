from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.auth_models import User, Role, Permission, RoleUser, PermissionRole
from app.services.auth_service import get_current_user, PermissionChecker
from app.dto.auth_dto import RoleDTO, RoleCollectionDTO
from app.schemas.auth_schemas import StoreRoleRequest, UpdateRoleRequest, AttachUserRoleRequest
from app.dto.auth_dto import PermissionDTO, PermissionCollectionDTO
from app.schemas.auth_schemas import StorePermissionRequest, UpdatePermissionRequest
from pydantic import BaseModel

router = APIRouter(prefix="/ref", tags=["References (RBAC)"])

# --- УПРАВЛЕНИЕ РОЛЯМИ (CRUD) ---
@router.post("/role", response_model=RoleDTO, status_code=status.HTTP_201_CREATED)
def create_role(
        role_data: StoreRoleRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(PermissionChecker("create-role"))
):
    # Проверяем уникальность по slug среди живых ролей
    existing = db.query(Role).filter(Role.slug == role_data.slug, Role.deleted_at == None).first()
    if existing:
        raise HTTPException(status_code=400, detail="Роль с таким шифром (slug) уже существует")

    new_role = Role(
        name=role_data.name,
        slug=role_data.slug,
        description=role_data.description,
        created_by=current_user.id
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return role_data.toDTO(new_role.id, current_user.id)


@router.get("/role", response_model=RoleCollectionDTO)
def get_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получение списка всех не удаленных ролей"""
    query = db.query(Role).filter(Role.deleted_at == None)
    roles = query.all()
    total = query.count()
    return RoleCollectionDTO(roles=roles, total=total)


@router.patch("/role/{id}", response_model=RoleDTO)
def update_role(
        id: int,
        role_data: UpdateRoleRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Частичное обновление роли (PATCH)"""
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    # Обновляем только те поля, которые прислал клиент
    data_dict = role_data.model_dump(exclude_unset=True)
    for key, value in data_dict.items():
        setattr(role, key, value)

    role.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(role)
    return role


@router.delete("/role/{id}", status_code=status.HTTP_200_OK)
def delete_role(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(PermissionChecker("delete-role"))
):
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Вместо физического удаления выставляем флаги
    role.deleted_at = datetime.utcnow()
    role.deleted_by = current_user.id

    # ТЗ: Мягко удаляем связи этой роли с пользователями
    db.query(RoleUser).filter(RoleUser.role_id == id, RoleUser.deleted_at == None).update({
        "deleted_at": datetime.utcnow(),
        "deleted_by": current_user.id
    }, synchronize_session=False)

    db.commit()
    return {"message": "Роль успешно удалена (мягкое удаление)"}


# --- СВЯЗЫВАНИЕ ПОЛЬЗОВАТЕЛЕЙ И РОЛЕЙ ---

@router.post("/user/{id}/role", status_code=status.HTTP_200_OK)
def attach_role_to_user(
        id: int,
        payload: AttachUserRoleRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Привязка роли к пользователю с фиксацией создателя"""
    # Проверяем, существует ли живой юзер
    user = db.query(User).filter(User.id == id).first()  # Юзеры у нас удаляются физически по ЛБ2
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, существует ли живая роль
    role = db.query(Role).filter(Role.id == payload.role_id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Указанная роль не существует или удалена")

    # Проверяем, нет ли уже такой активной связи
    existing_link = db.query(RoleUser).filter(
        RoleUser.user_id == id,
        RoleUser.role_id == payload.role_id,
        RoleUser.deleted_at == None
    ).first()

    if existing_link:
        return {"message": "Эта роль уже назначена данному пользователю"}

    # Создаем связь с заполнением создателя по ТЗ
    new_link = RoleUser(
        user_id=id,
        role_id=payload.role_id,
        created_by=current_user.id
    )
    db.add(new_link)
    db.commit()
    return {"message": f"Роль '{role.name}' успешно назначена пользователю {user.username}"}


# --- УПРАВЛЕНИЕ РАЗРЕШЕНИЯМИ (CRUD) ---

@router.post("/permission", response_model=PermissionDTO, status_code=status.HTTP_201_CREATED)
def create_permission(
        perm_data: StorePermissionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создание нового разрешения (Доступно авторизованным)"""
    existing = db.query(Permission).filter(Permission.slug == perm_data.slug, Permission.deleted_at == None).first()
    if existing:
        raise HTTPException(status_code=400, detail="Разрешение с таким slug уже существует")

    new_perm = Permission(
        name=perm_data.name,
        slug=perm_data.slug,
        description=perm_data.description,
        created_by=current_user.id
    )
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return perm_data.toDTO(new_perm.id, current_user.id)


@router.get("/permission", response_model=PermissionCollectionDTO)
def get_permissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получение списка всех живых разрешений"""
    query = db.query(Permission).filter(Permission.deleted_at == None)
    perms = query.all()
    total = query.count()
    return PermissionCollectionDTO(permissions=perms, total=total)


@router.patch("/permission/{id}", response_model=PermissionDTO)
def update_permission(
        id: int,
        perm_data: UpdatePermissionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Частичное обновление разрешения (PATCH)"""
    perm = db.query(Permission).filter(Permission.id == id, Permission.deleted_at == None).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")

    data_dict = perm_data.model_dump(exclude_unset=True)
    for key, value in data_dict.items():
        setattr(perm, key, value)

    perm.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(perm)
    return perm


@router.delete("/permission/{id}", status_code=status.HTTP_200_OK)
def delete_permission(
        id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Soft Delete
    perm = db.query(Permission).filter(Permission.id == id, Permission.deleted_at == None).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")

    perm.deleted_at = datetime.utcnow()
    perm.deleted_by = current_user.id

    # ТЗ: Мягко удаляем связи этого разрешения с ролями
    db.query(PermissionRole).filter(PermissionRole.permission_id == id, PermissionRole.deleted_at == None).update({
        "deleted_at": datetime.utcnow(),
        "deleted_by": current_user.id
    }, synchronize_session=False)

    db.commit()
    return {"message": "Разрешение успешно удалено"}


# --- СВЯЗЫВАНИЕ РАЗРЕШЕНИЙ И РОЛЕЙ ---

class AttachPermissionRoleRequest(BaseModel):  # Быстрая схема прямо тут, чтобы не бегать по файлам
    permission_id: int

@router.post("/role/{id}/permission", status_code=status.HTTP_200_OK)
def attach_permission_to_role(
        id: int,
        payload: AttachPermissionRoleRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Привязка разрешения к роли с фиксацией создателя"""
    # Ищем живую роль
    role = db.query(Role).filter(Role.id == id, Role.deleted_at == None).first()
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    #  Ищем живое разрешение
    perm = db.query(Permission).filter(Permission.id == payload.permission_id, Permission.deleted_at == None).first()
    if not perm:
        raise HTTPException(status_code=404, detail="Разрешение не найдено")

    # Проверяем дубликат связи
    existing_link = db.query(PermissionRole).filter(
        PermissionRole.role_id == id,
        PermissionRole.permission_id == payload.permission_id,
        PermissionRole.deleted_at == None
    ).first()

    if existing_link:
        return {"message": "Это разрешение уже привязано к данной роли"}

    # Создаем связь по ТЗ
    new_link = PermissionRole(
        role_id=id,
        permission_id=payload.permission_id,
        created_by=current_user.id
    )
    db.add(new_link)
    db.commit()
    return {"message": f"Разрешение '{perm.name}' успешно добавлено к роли '{role.name}'"}