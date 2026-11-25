from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Article Schemas ---
class ArticleBase(BaseModel):
    title: str = Field(..., description="Title of the article")
    content: str = Field(..., description="Full markdown content or text")
    category: str = Field(default="General", description="Category of the article")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    department: str = Field(default="General Helpdesk", description="Clinic department")
    author: Optional[str] = Field(default="Clinic Staff", description="Author or staff designation")
    status: Optional[str] = Field(default="published", description="'published' or 'draft'")


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    department: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None


class ArticleResponse(ArticleBase):
    id: int
    source_file: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- Chat & RAG Schemas ---
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Patient question or search query")
    session_id: Optional[str] = Field(default=None, description="Client session ID for multi-turn history")
    top_k: Optional[int] = Field(default=3, ge=1, le=10, description="Number of context chunks to retrieve")


class Citation(BaseModel):
    title: str
    category: str
    department: Optional[str] = None
    content_snippet: str
    relevance_score: float
    source: str


class ChatResponse(BaseModel):
    query_id: int
    question: str
    answer: str
    confidence_score: float
    is_fallback: bool
    sources: List[Citation]
    suggested_follow_ups: List[str]
    disclaimer: str


# --- Feedback Schemas ---
class FeedbackCreate(BaseModel):
    query_id: int
    rating: int = Field(..., description="1 for helpful (thumbs up), -1 for unhelpful (thumbs down)")
    comment: Optional[str] = None


# --- Search Schemas ---
class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tag: Optional[str] = None
    limit: Optional[int] = 5


# --- Admin & Index Schemas ---
class AdminAuthRequest(BaseModel):
    pin: str


class IndexStatusResponse(BaseModel):
    total_articles: int
    total_vectors: int
    last_indexed_at: Optional[str]
    collection_name: str
    status: str


# --- Analytics Schemas ---
class TopQuestionItem(BaseModel):
    question: str
    count: int
    avg_confidence: float


class DepartmentCountItem(BaseModel):
    department: str
    count: int


class AnalyticsSummary(BaseModel):
    total_queries: int
    helpful_ratings: int
    unhelpful_ratings: int
    satisfaction_rate: float
    unanswered_count: int
    top_questions: List[TopQuestionItem]
    department_distribution: List[DepartmentCountItem]
    recent_queries: List[Dict[str, Any]]
