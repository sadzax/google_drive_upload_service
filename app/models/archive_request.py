from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import uuid

# База данных SQLite
DATABASE_URL = "sqlite:///./lg.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocalArchiveRequest = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модель для хранения данных о запросах
class ArchiveRequest(Base):
    __tablename__ = "archive_requests"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_ip = Column(String)
    archive_url = Column(String)
    redirect_success_link = Column(String)
    redirect_fail_link = Column(String)
    cloud_type = Column(String)
    gallery_name = Column(String)
    archive_type = Column(String)

# Создание таблицы
Base.metadata.create_all(bind=engine)
