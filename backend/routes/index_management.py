from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db, Article
from backend.document_processor import chunk_text
from backend.rag_engine import RAGEngine

router = APIRouter(prefix="/api/index", tags=["Index Management"])

_last_rebuild_time = None


@router.get("/status")
def get_index_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns the current status of the Chroma vector store and knowledge base."""
    rag = RAGEngine.get_instance()
    stats = rag.get_index_stats()
    total_articles = db.query(Article).filter(Article.status == "published").count()
    draft_articles = db.query(Article).filter(Article.status == "draft").count()

    return {
        "status": stats.get("status", "ready"),
        "total_vectors": stats.get("total_vectors", 0),
        "total_published_articles": total_articles,
        "total_draft_articles": draft_articles,
        "collection_name": stats.get("collection_name", ""),
        "embedding_model": stats.get("embedding_model", ""),
        "last_rebuild_time": _last_rebuild_time.isoformat() if _last_rebuild_time else None
    }


@router.post("/rebuild")
def rebuild_vector_index(db: Session = Depends(get_db)):
    """
    Clears the Chroma vector database and re-indexes all published articles from SQLite.
    This guarantees fresh synchronization after article additions, edits, or deletions.
    """
    global _last_rebuild_time
    rag = RAGEngine.get_instance()

    # Step 1: Clear current Chroma collection
    rag.clear_index()

    # Step 2: Fetch all published articles
    published_articles = db.query(Article).filter(Article.status == "published").all()
    all_chunks = []

    for art in published_articles:
        chunks = chunk_text(
            art.content,
            metadata={
                "title": art.title,
                "category": art.category,
                "department": art.department,
                "article_id": art.id,
                "source": art.source_file or f"article_{art.id}"
            }
        )
        all_chunks.extend(chunks)

    # Step 3: Ingest chunks into vector store
    indexed_count = rag.add_documents(all_chunks)
    _last_rebuild_time = datetime.utcnow()

    return {
        "status": "success",
        "message": "Vector index successfully rebuilt.",
        "articles_processed": len(published_articles),
        "total_vectors_created": indexed_count,
        "rebuilt_at": _last_rebuild_time.isoformat()
    }
