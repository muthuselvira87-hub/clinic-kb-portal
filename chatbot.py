"""
Legacy compatibility wrapper for chatbot functions.
Delegates to backend.rag_engine.RAGEngine for advanced LangChain RAG capabilities.
"""
from backend.rag_engine import RAGEngine
from backend.document_processor import parse_faq_txt, chunk_text
from backend.config import DATA_DIR
from backend.database import init_db, SessionLocal, Article
import json


def create_db():
    """Initializes database and builds Chroma vector index from FAQ dataset."""
    init_db()
    rag = RAGEngine.get_instance()
    rag.clear_index()

    faq_path = DATA_DIR / "faq.txt"
    if faq_path.exists():
        faqs = parse_faq_txt(faq_path)
        chunks = []
        for faq in faqs:
            c = chunk_text(
                faq["content"],
                metadata={
                    "title": faq["title"],
                    "category": faq["category"],
                    "department": faq["department"],
                    "source": "faq.txt"
                }
            )
            chunks.extend(c)
        rag.add_documents(chunks)
        print(f"Successfully indexed {len(chunks)} chunks into Chroma.")


def query_db(question: str) -> str:
    """Queries the Chroma vector store and returns the synthesized answer."""
    rag = RAGEngine.get_instance()
    result = rag.answer_query(question)
    return result["answer"]


if __name__ == "__main__":
    create_db()
    print("Testing query:")
    print(query_db("What are clinic timings?"))