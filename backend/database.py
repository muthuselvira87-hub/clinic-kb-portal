import json
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from backend.config import SQLITE_DB_PATH

DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), default="General", index=True)
    tags = Column(String(255), default="[]")  # JSON string of list of tags
    department = Column(String(100), default="General Helpdesk", index=True)
    author = Column(String(100), default="Clinic Administrator")
    status = Column(String(50), default="published", index=True)  # published | draft
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        try:
            parsed_tags = json.loads(self.tags) if self.tags else []
        except Exception:
            parsed_tags = [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else []

        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": parsed_tags,
            "department": self.department,
            "author": self.author,
            "status": self.status,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    is_fallback = Column(Boolean, default=False)
    sources = Column(Text, default="[]")  # JSON encoded list of source citations
    category = Column(String(100), default="General")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    feedbacks = relationship("Feedback", back_populates="query_log", cascade="all, delete-orphan")

    def to_dict(self):
        try:
            parsed_sources = json.loads(self.sources) if self.sources else []
        except Exception:
            parsed_sources = []

        return {
            "id": self.id,
            "session_id": self.session_id,
            "question": self.question,
            "answer": self.answer,
            "confidence_score": self.confidence_score,
            "is_fallback": self.is_fallback,
            "sources": parsed_sources,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("query_logs.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1: thumbs up / helpful, -1: thumbs down / unhelpful
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    query_log = relationship("QueryLog", back_populates="feedbacks")


class UnansweredQuery(Base):
    __tablename__ = "unanswered_queries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question = Column(Text, nullable=False, unique=True)
    confidence_score = Column(Float, default=0.0)
    frequency = Column(Integer, default=1)
    resolved = Column(Boolean, default=False, index=True)
    last_asked = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "confidence_score": self.confidence_score,
            "frequency": self.frequency,
            "resolved": self.resolved,
            "last_asked": self.last_asked.isoformat() if self.last_asked else None,
        }


def init_db():
    """Initializes SQLite tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
