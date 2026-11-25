import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import DATA_DIR, CLINIC_NAME
from backend.database import init_db, get_db, Article, SessionLocal
from backend.document_processor import parse_faq_txt, chunk_text
from backend.rag_engine import RAGEngine
from backend.routes.chat import router as chat_router
from backend.routes.articles import router as articles_router
from backend.routes.documents import router as documents_router
from backend.routes.index_management import router as index_router
from backend.routes.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def seed_database_and_index():
    """Initializes tables and seeds articles if database is newly initialized."""
    init_db()
    db = SessionLocal()
    try:
        existing_articles_count = db.query(Article).count()
        rag = RAGEngine.get_instance()
        stats = rag.get_index_stats()

        if existing_articles_count == 0:
            logger.info("Initializing knowledge base with seed articles and FAQs...")
            articles_to_index = []

            # 1. Load seed_articles.json if available
            seed_file = DATA_DIR / "seed_articles.json"
            if seed_file.exists():
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_articles = json.load(f)
                for item in seed_articles:
                    art = Article(
                        title=item["title"],
                        content=item["content"],
                        category=item.get("category", "General Information"),
                        tags=json.dumps(item.get("tags", [])),
                        department=item.get("department", "General Helpdesk"),
                        author=item.get("author", "Clinic Staff"),
                        status=item.get("status", "published"),
                        source_file="seed_articles.json"
                    )
                    db.add(art)
                    articles_to_index.append(art)

            # 2. Load faq.txt if available
            faq_file = DATA_DIR / "faq.txt"
            if faq_file.exists():
                faqs = parse_faq_txt(faq_file)
                for faq in faqs:
                    art = Article(
                        title=faq["title"],
                        content=faq["content"],
                        category=faq["category"],
                        tags=json.dumps(faq["tags"]),
                        department=faq["department"],
                        author="FAQ Archive",
                        status="published",
                        source_file="faq.txt"
                    )
                    db.add(art)
                    articles_to_index.append(art)

            db.commit()
            logger.info(f"Inserted {len(articles_to_index)} seed articles into SQLite database.")

            # Index into Chroma if collection is empty
            if stats.get("total_vectors", 0) == 0:
                all_chunks = []
                for art in articles_to_index:
                    chunks = chunk_text(
                        art.content,
                        metadata={
                            "title": art.title,
                            "category": art.category,
                            "department": art.department,
                            "article_id": art.id,
                            "source": art.source_file
                        }
                    )
                    all_chunks.extend(chunks)

                indexed = rag.add_documents(all_chunks)
                logger.info(f"Vector index populated with {indexed} chunks.")
        else:
            logger.info(f"Knowledge base already initialized with {existing_articles_count} articles.")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Clinic Helpdesk KB Portal API...")
    seed_database_and_index()
    yield
    # Shutdown
    logger.info("Shutting down Clinic Helpdesk KB Portal API...")


app = FastAPI(
    title=f"{CLINIC_NAME} - Knowledge Base Portal API",
    description="GenAI-powered Clinic Helpdesk REST API supporting LangChain RAG, citations, article management, document ingestion, and query analytics.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router)
app.include_router(articles_router)
app.include_router(documents_router)
app.include_router(index_router)
app.include_router(analytics_router)


# Root & Backwards-Compatible Endpoints
@app.get("/")
def home():
    return {
        "status": "online",
        "service": f"{CLINIC_NAME} KB Portal API",
        "version": "2.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "articles": "/api/articles",
            "documents": "/api/documents/upload",
            "index_status": "/api/index/status",
            "analytics": "/api/analytics/summary",
            "docs": "/docs"
        }
    }


@app.get("/setup")
def setup():
    """Manual setup endpoint to re-seed and rebuild vector database."""
    seed_database_and_index()
    rag = RAGEngine.get_instance()
    stats = rag.get_index_stats()
    return {
        "status": "success",
        "message": "Database and vector index initialized successfully",
        "stats": stats
    }


@app.get("/ask")
def ask(q: str):
    """Backwards-compatible endpoint for legacy callers."""
    rag = RAGEngine.get_instance()
    result = rag.answer_query(q)
    return {
        "question": q,
        "answer": result["answer"],
        "confidence": result["confidence_score"],
        "sources": [s.title for s in result["sources"]]
    }