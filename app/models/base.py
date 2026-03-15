from sqlalchemy import create_engine, Column, Integer, String, Text, SmallInteger, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, schema
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    __table_args__ = {"schema": "learn"}
    id = Column(Integer, primary_key=True)
    poc_id = Column(Integer, nullable=False)
    model_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    finished_at = Column(TIMESTAMP, nullable=True)
    error_message = Column(Text, nullable=True)
    output_model_name = Column(String(200), nullable=True)
    instance_id = Column(String(100), nullable=True)


class TrainingData(Base):
    __tablename__ = "training_data"
    __table_args__ = {"schema": "learn"}
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("learn.training_jobs.id"), nullable=False)
    log_id = Column(Integer, nullable=False)
