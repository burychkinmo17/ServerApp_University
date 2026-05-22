import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv() # Подгружаем .env
db_url = os.getenv("DATABASE_URL")

#check_same_thread нужен специально для SQLite, чтобы асинхронные запросы не блокировали файл базы.
engine = create_engine(db_url, connect_args={"check_same_thread": False})

# Создаем фабрику сессий (каждый новый запрос будет получать свою независимую сессию БД)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого мы будем наследовать все наши таблицы
Base = declarative_base()

# Функция-генератор (Dependency), которая будет выдавать сессию роутерам и закрывать её
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()