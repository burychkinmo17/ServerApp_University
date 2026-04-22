from pydantic import BaseModel, ConfigDict


class ServerInfoDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    python_version: str  # В контексте Python заменяем php_version [cite: 159]
    server_interface: str


class ClientInfoDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    ip: str
    user_agent: str


class DatabaseInfoDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    driver: str
    database_name: str
    server_version: str