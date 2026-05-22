import platform
from fastapi import APIRouter, Request, HTTPException
from app.dto.lb1_dto import ServerInfoDTO, ClientInfoDTO, DatabaseInfoDTO
from sqlalchemy import create_engine, text
import os

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
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            sql = text("SELECT sqlite_version();") if engine.name == 'sqlite' else text("SELECT version();")
            ver = conn.execute(sql).scalar()
            return DatabaseInfoDTO(
                driver=engine.driver,
                database_name=engine.url.database or "local",
                server_version=str(ver)
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection error")