import pytest
from fastapi.testclient import TestClient
from app import app
from backend.database import init_db


def get_test_client():
    """Provides a configured FastAPI test client."""
    init_db()
    return TestClient(app)


@pytest.fixture(scope="module")
def client():
    """Pytest fixture wrapper."""
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_home_endpoint(client):
    """Test health check root endpoint."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "endpoints" in data


def test_articles_crud(client):
    """Test Create, Read, Update, and Delete for knowledge articles."""
    # 1. Create article
    create_payload = {
        "title": "Oncology Screening Clinic",
        "content": "Early cancer screening packages available every Saturday. Packages start from Rs. 1500.",
        "category": "Specialist Care",
        "department": "Oncology",
        "tags": ["cancer", "oncology", "screening"],
        "author": "Dr. Ramanathan",
        "status": "published"
    }
    create_res = client.post("/api/articles", json=create_payload)
    assert create_res.status_code == 201
    created_art = create_res.json()
    art_id = created_art["id"]
    assert created_art["title"] == "Oncology Screening Clinic"

    # 2. Get article by ID
    get_res = client.get(f"/api/articles/{art_id}")
    assert get_res.status_code == 200
    assert get_res.json()["department"] == "Oncology"

    # 3. Update article
    update_payload = {
        "title": "Comprehensive Oncology Screening Clinic",
        "status": "published"
    }
    update_res = client.put(f"/api/articles/{art_id}", json=update_payload)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Comprehensive Oncology Screening Clinic"

    # 4. Delete article
    del_res = client.delete(f"/api/articles/{art_id}")
    assert del_res.status_code == 200

    # 5. Verify deleted
    verify_res = client.get(f"/api/articles/{art_id}")
    assert verify_res.status_code == 404


def test_chat_and_feedback_flow(client):
    """Test Q&A flow and feedback submission."""
    # Ask question
    chat_res = client.post("/api/chat", json={"question": "What are the clinic timings?", "session_id": "test_sess_1"})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "answer" in chat_data
    assert "query_id" in chat_data
    query_id = chat_data["query_id"]

    # Submit feedback
    feedback_res = client.post("/api/feedback", json={"query_id": query_id, "rating": 1, "comment": "Very helpful!"})
    assert feedback_res.status_code == 200
    assert feedback_res.json()["status"] == "success"


def test_analytics_summary(client):
    """Test analytics aggregation endpoint."""
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_queries" in data
    assert "satisfaction_rate" in data
    assert "top_questions" in data
    assert "department_distribution" in data


def test_index_status_and_rebuild(client):
    """Test vector index status and rebuild endpoint."""
    status_res = client.get("/api/index/status")
    assert status_res.status_code == 200
    assert "total_vectors" in status_res.json()

    rebuild_res = client.post("/api/index/rebuild")
    assert rebuild_res.status_code == 200
    assert rebuild_res.json()["status"] == "success"
