from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config import DATABASE_URL

Base = declarative_base()

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    country = Column(String, nullable=False)
    popularity_metrics = Column(JSON, nullable=False)
    source_url = Column(String, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint('workflow_name', 'platform', 'country', name='_workflow_platform_country_uc'),)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()