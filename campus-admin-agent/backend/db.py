from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()  # Load environment variables from a .env file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, email_sent, profile_update, etc.
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection

# if __name__ == "__main__":
#     try:
#         with engine.connect() as connection:
#             print("Database connection successful.")
#     except Exception as e:
#         print(f"Database connection failed: {e}")

#     print("Creating tables...")
#     Base.metadata.create_all(engine)
#     print("Tables created.")
  