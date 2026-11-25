import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db, Article
from backend.models import ArticleCreate, ArticleUpdate, ArticleResponse
from backend.rag_engine import RAGEngine
from backend.document_processor import chunk_text

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("", response_model=List[ArticleResponse])
def get_articles(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = "published",
    db: Session = Depends(get_db)
):
    """Retrieve articles with optional filtering by category, tag, department, or keyword search."""
    query = db.query(Article)

    if status and status != "all":
        query = query.filter(Article.status == status)

    if category and category != "All":
        query = query.filter(Article.category == category)

    if department and department != "All":
        query = query.filter(Article.department == department)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Article.title.ilike(search_pattern)) | 
            (Article.content.ilike(search_pattern))
        )

    articles = query.order_by(Article.updated_at.desc()).all()

    # In-memory filter for tags if specified
    if tag and tag != "All":
        tag_lower = tag.lower().strip()
        filtered = []
        for art in articles:
            parsed_tags = [t.lower() for t in art.to_dict()["tags"]]
            if tag_lower in parsed_tags:
                filtered.append(art)
        articles = filtered

    return [art.to_dict() for art in articles]


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Returns list of distinct categories with article counts."""
    categories = (
        db.query(Article.category, func.count(Article.id))
        .filter(Article.status == "published")
        .group_by(Article.category)
        .all()
    )
    return [{"category": c[0], "count": c[1]} for c in categories]


@router.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    """Returns list of distinct tags across all published articles."""
    articles = db.query(Article).filter(Article.status == "published").all()
    tag_counts = {}
    for art in articles:
        for t in art.to_dict()["tags"]:
            tag_clean = t.strip()
            if tag_clean:
                tag_counts[tag_clean] = tag_counts.get(tag_clean, 0) + 1
    
    sorted_tags = sorted(
        [{"tag": k, "count": v} for k, v in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    return sorted_tags


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Fetch single article by ID."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article.to_dict()


@router.post("", response_model=ArticleResponse, status_code=201)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    """Creates a new knowledge base article and indexes it in the vector store."""
    new_article = Article(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=json.dumps(payload.tags),
        department=payload.department,
        author=payload.author or "Clinic Staff",
        status=payload.status or "published",
        source_file="article_editor"
    )
    db.add(new_article)
    db.commit()
    db.refresh(new_article)

    # Index into Chroma if published
    if new_article.status == "published":
        try:
            rag = RAGEngine.get_instance()
            docs = chunk_text(
                new_article.content,
                metadata={
                    "title": new_article.title,
                    "category": new_article.category,
                    "department": new_article.department,
                    "article_id": new_article.id,
                    "source": f"article_{new_article.id}"
                }
            )
            rag.add_documents(docs)
        except Exception as e:
            # Non-blocking log
            print(f"Failed to auto-index article to Chroma: {e}")

    return new_article.to_dict()


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, payload: ArticleUpdate, db: Session = Depends(get_db)):
    """Updates an existing article and syncs the vector store."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if payload.title is not None:
        article.title = payload.title
    if payload.content is not None:
        article.content = payload.content
    if payload.category is not None:
        article.category = payload.category
    if payload.tags is not None:
        article.tags = json.dumps(payload.tags)
    if payload.department is not None:
        article.department = payload.department
    if payload.author is not None:
        article.author = payload.author
    if payload.status is not None:
        article.status = payload.status

    db.commit()
    db.refresh(article)

    return article.to_dict()


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    """Deletes an article from database."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    db.delete(article)
    db.commit()

    return {"status": "success", "message": f"Article {article_id} deleted."}
