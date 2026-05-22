import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import lb1_routers, auth_routers, ref_routers
from app.database import engine, Base
from app.models import auth_models


load_dotenv()

app = FastAPI(title="University Labs API")

#Проверка базы, и если таблиц users и refresh_tokens нету - создаст их
Base.metadata.create_all(bind=engine)

app.include_router(lb1_routers.router)
app.include_router(auth_routers.router, prefix="/api")
app.include_router(ref_routers.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Сервер запущен.", "locale": os.getenv("APP_LOCALE")}