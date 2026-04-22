import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import lb1_routers

load_dotenv()

app = FastAPI(title="University Labs API")

app.include_router(lb1_routers.router)

@app.get("/")
async def root():
    return {"message": "Сервер запущен.", "locale": os.getenv("APP_LOCALE")}