import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db, QueryLog, Feedback, UnansweredQuery
from backend.models import ChatRequest, ChatResponse, FeedbackCreate, Citation
from backend.rag_engine import RAGEngine

router = APIRouter(prefix="/api", tags=["Chat & Q&A"])


@router.post("/chat", response_model=ChatResponse)
def ask_question(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Submits a patient question to the RAG engine.
    Retrieves knowledge context, performs emergency triage, generates answer,
    logs the transaction, and tracks fallback queries for analytics.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    rag = RAGEngine.get_instance()
    result = rag.answer_query(question, top_k=payload.top_k or 3)

    # Serialize sources for storage
    sources_data = [src.dict() for src in result["sources"]]

    # Log query in database
    log_entry = QueryLog(
        session_id=payload.session_id,
        question=question,
        answer=result["answer"],
        confidence_score=result["confidence_score"],
        is_fallback=result["is_fallback"],
        sources=json.dumps(sources_data),
        category=result.get("category", "General"),
        created_at=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    # If fallback or low confidence, track in UnansweredQuery for admin review
    if result["is_fallback"] or result["confidence_score"] < 0.45:
        existing_unanswered = (
            db.query(UnansweredQuery)
            .filter(UnansweredQuery.question.ilike(question))
            .first()
        )
        if existing_unanswered:
            existing_unanswered.frequency += 1
            existing_unanswered.last_asked = datetime.utcnow()
            existing_unanswered.confidence_score = min(existing_unanswered.confidence_score, result["confidence_score"])
        else:
            new_unanswered = UnansweredQuery(
                question=question,
                confidence_score=result["confidence_score"],
                frequency=1,
                resolved=False,
                last_asked=datetime.utcnow()
            )
            db.add(new_unanswered)
        db.commit()

    return ChatResponse(
        query_id=log_entry.id,
        question=question,
        answer=result["answer"],
        confidence_score=result["confidence_score"],
        is_fallback=result["is_fallback"],
        sources=result["sources"],
        suggested_follow_ups=result["suggested_follow_ups"],
        disclaimer=result["disclaimer"]
    )


@router.post("/feedback")
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    """Records patient feedback (helpful = 1, unhelpful = -1) for a specific query answer."""
    query_log = db.query(QueryLog).filter(QueryLog.id == payload.query_id).first()
    if not query_log:
        raise HTTPException(status_code=404, detail="Query log not found.")

    feedback_entry = Feedback(
        query_id=payload.query_id,
        rating=payload.rating,
        comment=payload.comment,
        created_at=datetime.utcnow()
    )
    db.add(feedback_entry)
    db.commit()

    return {"status": "success", "message": "Feedback submitted successfully."}


@router.get("/chat/history")
def get_chat_history(session_id: str, limit: int = 15, db: Session = Depends(get_db)):
    """Returns conversation history for a given session ID."""
    logs = (
        db.query(QueryLog)
        .filter(QueryLog.session_id == session_id)
        .order_by(QueryLog.created_at.asc())
        .limit(limit)
        .all()
    )
    return [log.to_dict() for log in logs]
