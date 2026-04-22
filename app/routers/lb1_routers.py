import platform
from fastapi import APIRouter, Request
from app.dto.lb1_dto import ServerInfoDTO, ClientInfoDTO, DatabaseInfoDTO

router = APIRouter(prefix="/info")

@router.get("/server", response_model=ServerInfoDTO)
async def get_server_info():
    return ServerInfoDTO(
        python_version=platform.python_version(),
        server_interface="ASGI (Uvicorn)"
    )

@router.get("/client", response_model=ClientInfoDTO)
async def get_client_info(request: Request):
    return ClientInfoDTO(
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )

@router.get("/database", response_model=DatabaseInfoDTO)
async def get_database_info():
    return DatabaseInfoDTO(
        driver="postgresql",
        database_name="university_db",
        server_version="15.2"
    )