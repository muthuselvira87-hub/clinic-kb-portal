from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db, QueryLog, Feedback, UnansweredQuery, Article
from backend.models import AnalyticsSummary, TopQuestionItem, DepartmentCountItem

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Computes aggregate analytics: query volumes, satisfaction ratings, top questions, and category breakdowns."""
    total_queries = db.query(QueryLog).count()

    # Satisfaction ratings
    helpful_count = db.query(Feedback).filter(Feedback.rating == 1).count()
    unhelpful_count = db.query(Feedback).filter(Feedback.rating == -1).count()
    total_rated = helpful_count + unhelpful_count
    satisfaction_rate = round((helpful_count / total_rated * 100), 1) if total_rated > 0 else 100.0

    # Unanswered queries
    unanswered_count = db.query(UnansweredQuery).filter(UnansweredQuery.resolved == False).count()

    # Top asked questions (group by exact or trimmed question)
    top_questions_raw = (
        db.query(
            QueryLog.question,
            func.count(QueryLog.id).label("cnt"),
            func.avg(QueryLog.confidence_score).label("avg_conf")
        )
        .group_by(QueryLog.question)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )
    top_questions = [
        TopQuestionItem(
            question=row[0],
            count=row[1],
            avg_confidence=round(float(row[2] or 0.0), 2)
        )
        for row in top_questions_raw
    ]

    # Department distribution
    dept_raw = (
        db.query(
            QueryLog.category,
            func.count(QueryLog.id).label("cnt")
        )
        .group_by(QueryLog.category)
        .order_by(desc("cnt"))
        .all()
    )
    dept_distribution = [
        DepartmentCountItem(department=row[0] or "General", count=row[1])
        for row in dept_raw
    ]

    # Recent queries
    recent = (
        db.query(QueryLog)
        .order_by(QueryLog.created_at.desc())
        .limit(20)
        .all()
    )
    recent_list = [r.to_dict() for r in recent]

    return AnalyticsSummary(
        total_queries=total_queries,
        helpful_ratings=helpful_count,
        unhelpful_ratings=unhelpful_count,
        satisfaction_rate=satisfaction_rate,
        unanswered_count=unanswered_count,
        top_questions=top_questions,
        department_distribution=dept_distribution,
        recent_queries=recent_list
    )


@router.get("/unanswered")
def get_unanswered_queries(
    resolved: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """Lists queries that resulted in fallback or low confidence for administrator action."""
    query = db.query(UnansweredQuery)
    if resolved is not None:
        query = query.filter(UnansweredQuery.resolved == resolved)

    unanswered = query.order_by(UnansweredQuery.frequency.desc()).all()
    return [u.to_dict() for u in unanswered]


@router.post("/unanswered/{query_id}/resolve")
def resolve_unanswered_query(query_id: int, db: Session = Depends(get_db)):
    """Marks an unanswered query as resolved (e.g., after an article has been published)."""
    item = db.query(UnansweredQuery).filter(UnansweredQuery.id == query_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Unanswered query not found.")
    item.resolved = True
    db.commit()
    return {"status": "success", "message": f"Query {query_id} marked as resolved."}


@router.get("/export")
def export_queries(limit: int = 500, db: Session = Depends(get_db)):
    """Exports full query logs with citations and ratings."""
    logs = (
        db.query(QueryLog)
        .order_by(QueryLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [l.to_dict() for l in logs]
