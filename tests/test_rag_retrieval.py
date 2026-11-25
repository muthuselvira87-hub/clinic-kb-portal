import pytest
from backend.rag_engine import RAGEngine
from backend.document_processor import chunk_text
from backend.config import CLINIC_PHONE, CLINIC_EMERGENCY_NUMBER


def get_test_rag_instance():
    """Builds and returns an initialized RAGEngine instance with test documents."""
    rag = RAGEngine.get_instance()
    # Add representative test documents
    test_docs = chunk_text(
        "Cardiology consultations start from Rs. 600. Senior cardiologists are available Monday to Friday from 10 AM to 4 PM.",
        metadata={"title": "Cardiology Fees & Hours", "category": "Specialist Care", "department": "Cardiology", "source": "test_cardio"}
    )
    test_docs += chunk_text(
        "Our clinic accepts Star Health, ICICI Lombard, and HDFC ERGO health insurance for cashless hospitalization.",
        metadata={"title": "Health Insurance Network", "category": "Billing", "department": "Billing & Accounts", "source": "test_insurance"}
    )
    rag.add_documents(test_docs)
    return rag


@pytest.fixture(scope="module")
def rag_instance():
    """Pytest fixture wrapper."""
    return get_test_rag_instance()


def test_standard_query_retrieval(rag_instance):
    """Test retrieval precision and citation correctness for standard clinic queries."""
    res = rag_instance.answer_query("How much is the cardiology consultation fee?")
    assert res is not None
    assert "600" in res["answer"] or "Cardiology" in res["answer"]
    assert res["is_fallback"] is False
    assert res["confidence_score"] > 0.4
    assert len(res["sources"]) > 0

    top_source = res["sources"][0]
    assert top_source.title != ""
    assert top_source.relevance_score > 0.0


def test_citation_structure(rag_instance):
    """Verify citations contain all required metadata fields."""
    res = rag_instance.answer_query("Do you accept Star Health insurance?")
    assert len(res["sources"]) > 0
    citation = res["sources"][0]
    assert hasattr(citation, "title")
    assert hasattr(citation, "category")
    assert hasattr(citation, "department")
    assert hasattr(citation, "content_snippet")
    assert hasattr(citation, "relevance_score")


def test_emergency_query_triage(rag_instance):
    """Verify emergency queries trigger immediate high-priority safety alert."""
    emergency_queries = [
        "Patient is experiencing severe chest pain and cannot breathe",
        "There is massive arterial bleeding from a deep wound",
        "My grandfather is unconscious and having a stroke"
    ]

    for q in emergency_queries:
        res = rag_instance.answer_query(q)
        assert res["is_fallback"] is False
        assert "EMERGENCY" in res["answer"]
        assert CLINIC_EMERGENCY_NUMBER in res["answer"]
        assert res["confidence_score"] == 1.0


def test_out_of_scope_fallback_handling(rag_instance):
    """Verify out-of-scope edge queries trigger graceful fallback."""
    out_of_scope_query = "What is the best way to repair a Toyota car transmission?"
    res = rag_instance.answer_query(out_of_scope_query)
    assert res["is_fallback"] is True
    assert CLINIC_PHONE in res["answer"]
    assert "could not locate specific guidance" in res["answer"]
