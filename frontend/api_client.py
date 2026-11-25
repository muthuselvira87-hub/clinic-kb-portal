import os
from typing import Dict, Any, List, Optional
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class ClinicAPIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> bool:
        """Returns True if the backend is reachable."""
        try:
            res = requests.get(f"{self.base_url}/", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def ask_chat(self, question: str, session_id: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
        """Sends patient query to /api/chat."""
        url = f"{self.base_url}/api/chat"
        payload = {"question": question, "session_id": session_id, "top_k": top_k}
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()

    def submit_feedback(self, query_id: int, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Submits feedback (+1 / -1) to /api/feedback."""
        url = f"{self.base_url}/api/feedback"
        payload = {"query_id": query_id, "rating": rating, "comment": comment}
        res = requests.post(url, json=payload, timeout=5)
        res.raise_for_status()
        return res.json()

    def get_articles(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = "published"
    ) -> List[Dict[str, Any]]:
        """Fetches articles matching filters."""
        url = f"{self.base_url}/api/articles"
        params = {}
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        if department:
            params["department"] = department
        if search:
            params["search"] = search
        if status:
            params["status"] = status

        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_article(self, article_id: int) -> Dict[str, Any]:
        """Fetches single article details."""
        url = f"{self.base_url}/api/articles/{article_id}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json()

    def create_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates an article in backend."""
        url = f"{self.base_url}/api/articles"
        res = requests.post(url, json=article_data, timeout=15)
        res.raise_for_status()
        return res.json()

    def update_article(self, article_id: int, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates article in backend."""
        url = f"{self.base_url}/api/articles/{article_id}"
        res = requests.put(url, json=article_data, timeout=15)
        res.raise_for_status()
        return res.json()

    def delete_article(self, article_id: int) -> Dict[str, Any]:
        """Deletes an article."""
        url = f"{self.base_url}/api/articles/{article_id}"
        res = requests.delete(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_categories(self) -> List[Dict[str, Any]]:
        """Gets all article categories with counts."""
        url = f"{self.base_url}/api/articles/categories"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json()

    def get_tags(self) -> List[Dict[str, Any]]:
        """Gets all article tags with counts."""
        url = f"{self.base_url}/api/articles/tags"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json()

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Uploads document to backend for ingestion."""
        url = f"{self.base_url}/api/documents/upload"
        files = {"file": (filename, file_bytes)}
        data = {}
        if title:
            data["title"] = title
        if category:
            data["category"] = category
        if department:
            data["department"] = department

        res = requests.post(url, files=files, data=data, timeout=30)
        res.raise_for_status()
        return res.json()

    def get_index_status(self) -> Dict[str, Any]:
        """Fetches vector store status."""
        url = f"{self.base_url}/api/index/status"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json()

    def rebuild_index(self) -> Dict[str, Any]:
        """Triggers vector index rebuild."""
        url = f"{self.base_url}/api/index/rebuild"
        res = requests.post(url, timeout=60)
        res.raise_for_status()
        return res.json()

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Fetches aggregate analytics."""
        url = f"{self.base_url}/api/analytics/summary"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_unanswered_queries(self, resolved: bool = False) -> List[Dict[str, Any]]:
        """Fetches unanswered/low-confidence queries."""
        url = f"{self.base_url}/api/analytics/unanswered"
        res = requests.get(url, params={"resolved": resolved}, timeout=5)
        res.raise_for_status()
        return res.json()

    def resolve_unanswered_query(self, query_id: int) -> Dict[str, Any]:
        """Marks unanswered query as resolved."""
        url = f"{self.base_url}/api/analytics/unanswered/{query_id}/resolve"
        res = requests.post(url, timeout=5)
        res.raise_for_status()
        return res.json()
