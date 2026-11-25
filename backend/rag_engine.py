import json
import logging
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    TOP_K_RESULTS,
    CLINIC_NAME,
    CLINIC_PHONE,
    CLINIC_EMAIL,
    CLINIC_EMERGENCY_NUMBER,
    CLINIC_TIMINGS,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
)
from backend.models import Citation

logger = logging.getLogger(__name__)

# Emergency triage keywords
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe", "shortness of breath",
    "severe bleeding", "bleeding", "arterial bleeding", "unconscious", "unresponsive",
    "stroke", "paralysis", "seizure", "overdose", "poison", "poisoning", "suicide",
    "suicidal", "severe burn", "head trauma", "choking", "anaphylaxis", "cardiac arrest"
]

CLINIC_DISCLAIMER = (
    "Disclaimer: This helpdesk provides clinic administrative and general health information. "
    "It is not a substitute for professional medical diagnosis or emergency treatment. "
    f"In case of an emergency, call {CLINIC_EMERGENCY_NUMBER} or visit the nearest ER immediately."
)


class RAGEngine:
    _instance = None

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.llm = None
        self._initialize_embeddings()
        self._initialize_vector_store()
        self._initialize_llm()

    @classmethod
    def get_instance(cls) -> "RAGEngine":
        if cls._instance is None:
            cls._instance = RAGEngine()
        return cls._instance

    def _initialize_embeddings(self):
        logger.info(f"Loading embeddings model: {EMBEDDING_MODEL_NAME}")
        # Check if local snapshot is present on disk for instant offline loading
        from pathlib import Path
        snapshot_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots" / "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
        effective_model = str(snapshot_dir) if snapshot_dir.exists() else EMBEDDING_MODEL_NAME

        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=effective_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info("Successfully loaded embeddings model.")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace embeddings: {e}")
            raise

    def _initialize_vector_store(self):
        logger.info(f"Connecting to Chroma vector store at: {CHROMA_DIR}")
        self.vector_store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DIR)
        )

    def _initialize_llm(self):
        if OPENAI_API_KEY and len(OPENAI_API_KEY.strip()) > 10:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=OPENAI_MODEL_NAME,
                    api_key=OPENAI_API_KEY,
                    temperature=0.2
                )
                logger.info(f"Initialized OpenAI LLM: {OPENAI_MODEL_NAME}")
            except Exception as e:
                logger.warning(f"Failed to initialize ChatOpenAI: {e}. Falling back to local synthesizer.")
                self.llm = None
        else:
            self.llm = None
            logger.info("Using built-in intelligent local RAG synthesizer (No external LLM key needed).")

    def get_index_stats(self) -> Dict[str, Any]:
        """Returns statistics about the Chroma vector collection."""
        try:
            count = self.vector_store._collection.count()
            return {
                "collection_name": CHROMA_COLLECTION_NAME,
                "total_vectors": count,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "status": "ready" if count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Error fetching vector index stats: {e}")
            return {
                "collection_name": CHROMA_COLLECTION_NAME,
                "total_vectors": 0,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "status": f"error: {str(e)}"
            }

    def add_documents(self, documents: List[Document]) -> int:
        """Adds documents to the Chroma vector store."""
        if not documents:
            return 0
        self.vector_store.add_documents(documents)
        return len(documents)

    def clear_index(self):
        """Clears all vectors in the collection."""
        try:
            self.vector_store.delete_collection()
            self._initialize_vector_store()
            logger.info("Chroma collection cleared successfully.")
        except Exception as e:
            logger.warning(f"Error clearing Chroma collection: {e}")

    def is_emergency_query(self, query: str) -> bool:
        """Checks if the query indicates an urgent medical emergency."""
        query_lower = query.lower()
        return any(re.search(rf"\b{re.escape(kw)}\b", query_lower) for kw in EMERGENCY_KEYWORDS)

    def search_with_scores(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Tuple[Document, float]]:
        """
        Executes similarity search and returns documents with normalized confidence scores (0.0 to 1.0).
        """
        try:
            results = self.vector_store.similarity_search_with_relevance_scores(query, k=top_k)
            normalized_results = []
            for doc, score in results:
                # Normalize score to 0.0 - 1.0 range
                confidence = max(0.0, min(1.0, float(score)))
                normalized_results.append((doc, confidence))
            return normalized_results
        except Exception as e:
            logger.warning(f"similarity_search_with_relevance_scores fallback due to: {e}")
            # Fallback to standard similarity search with distance calculation
            raw_results = self.vector_store.similarity_search_with_score(query, k=top_k)
            normalized_results = []
            for doc, dist in raw_results:
                # Approximate cosine similarity from distance
                confidence = max(0.0, min(1.0, 1.0 - (float(dist) / 2.0)))
                normalized_results.append((doc, confidence))
            return normalized_results

    def generate_local_response(self, query: str, matched_docs: List[Tuple[Document, float]]) -> str:
        """
        Synthesizes a clean, informative clinic response from the retrieved knowledge chunks.
        """
        if not matched_docs:
            return self.get_fallback_response(query)

        top_doc, top_score = matched_docs[0]
        category = top_doc.metadata.get("category", "General")
        dept = top_doc.metadata.get("department", "Clinic Services")
        title = top_doc.metadata.get("title", "Clinic Information")

        # Extract answer segments or clean content
        content = top_doc.page_content.strip()

        # If it's a Q/A formatted block, isolate the answer cleanly
        if "A:" in content:
            parts = content.split("A:", 1)
            primary_text = parts[1].strip()
        elif "**Answer:**" in content:
            parts = content.split("**Answer:**", 1)
            primary_text = parts[1].strip()
        else:
            primary_text = content

        response_lines = [
            f"**{title}** ({dept}):",
            "",
            primary_text,
        ]

        # If secondary chunk adds distinct relevant info, include a helpful note
        if len(matched_docs) > 1 and matched_docs[1][1] >= (CONFIDENCE_THRESHOLD + 0.05):
            second_doc = matched_docs[1][0]
            sec_title = second_doc.metadata.get("title", "")
            sec_content = second_doc.page_content.strip()
            if "A:" in sec_content:
                sec_text = sec_content.split("A:", 1)[1].strip()
            elif "**Answer:**" in sec_content:
                sec_text = sec_content.split("**Answer:**", 1)[1].strip()
            else:
                sec_text = sec_content[:200]

            if sec_text and sec_text not in primary_text:
                response_lines.append("")
                response_lines.append(f"📌 *Related Info ({sec_title})*: {sec_text}")

        response_lines.append("")
        response_lines.append(f"💡 For further assistance, contact {dept} at {CLINIC_PHONE}.")

        return "\n".join(response_lines)

    def generate_llm_response(self, query: str, matched_docs: List[Tuple[Document, float]]) -> str:
        """Generates response using OpenAI Chat model if configured."""
        context_blocks = []
        for i, (doc, score) in enumerate(matched_docs):
            src = doc.metadata.get("title", f"Source {i+1}")
            dept = doc.metadata.get("department", "Clinic")
            context_blocks.append(f"[Source {i+1}: {src} ({dept})]\n{doc.page_content}")

        context_str = "\n\n".join(context_blocks)
        prompt = (
            f"You are the official Clinic Helpdesk Assistant for {CLINIC_NAME}.\n"
            f"Use ONLY the following clinic knowledge base context to answer the patient's question.\n"
            f"Be professional, clear, empathetic, and accurate. If the context does not contain the answer, "
            f"explicitly state that you do not know and refer them to {CLINIC_PHONE}.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}. Falling back to local synthesizer.")
            return self.generate_local_response(query, matched_docs)

    def get_fallback_response(self, query: str) -> str:
        """Standard fallback response when query cannot be answered with high confidence."""
        return (
            f"I could not locate specific guidance for your query in our clinic knowledge base.\n\n"
            f"Please connect directly with our patient support desk:\n"
            f"- 📞 **Phone**: {CLINIC_PHONE}\n"
            f"- ✉️ **Email**: {CLINIC_EMAIL}\n"
            f"- 🕒 **Timings**: {CLINIC_TIMINGS}\n"
            f"- 📍 **Location**: 42 Health Avenue, Chennai\n\n"
            f"Your question has been logged for our administrative team to review and add to our FAQs."
        )

    def get_emergency_response(self) -> str:
        """High-priority emergency response for urgent medical symptoms."""
        return (
            f"🚨 **URGENT MEDICAL EMERGENCY ALERT**\n\n"
            f"Your inquiry indicates severe or life-threatening symptoms. "
            f"**Please do not rely on chat assistance for immediate medical crises.**\n\n"
            f"👉 **Immediate Actions Required:**\n"
            f"1. **Call Emergency Services immediately**: Dial **{CLINIC_EMERGENCY_NUMBER}** (Ambulance / Emergency).\n"
            f"2. Proceed directly to the nearest hospital Emergency Room.\n"
            f"3. Clinic 24/7 Emergency Hotline: **{CLINIC_PHONE}**.\n\n"
            f"Ambulance services and our Trauma Care unit are operational 24 hours a day, 7 days a week."
        )

    def get_suggested_follow_ups(self, query: str, category: str) -> List[str]:
        """Provides smart suggested follow-up questions for the patient."""
        q_lower = query.lower()
        if "timing" in q_lower or "hour" in q_lower or "open" in q_lower:
            return [
                "What are the doctor consultation charges?",
                "How do I book an appointment online?",
                "Are walk-in consultations permitted?"
            ]
        elif "appointment" in q_lower or "book" in q_lower:
            return [
                "What documents should I bring to the clinic?",
                "What is the average consultation duration?",
                "Is teleconsultation available?"
            ]
        elif "charge" in q_lower or "fee" in q_lower or "cost" in q_lower or "billing" in q_lower:
            return [
                "Which health insurance plans are accepted?",
                "What payment methods do you accept?",
                "Are diagnostic lab tests charged separately?"
            ]
        elif "emergency" in q_lower or "ambulance" in q_lower:
            return [
                "What is the emergency contact number?",
                "Are emergency doctors available 24/7?",
                "Where is the clinic casualty entrance located?"
            ]
        elif "pediatric" in q_lower or "child" in q_lower:
            return [
                "Are child vaccination services available?",
                "What are the pediatric department timings?",
                "Are female pediatricians available?"
            ]
        else:
            return [
                "What are the clinic working hours?",
                "How do I book an appointment?",
                "What specialist departments are available?"
            ]

    def answer_query(self, query: str, top_k: int = TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Main RAG pipeline:
        1. Checks for emergency red-flag symptoms.
        2. Retrieves relevant chunks with similarity confidence.
        3. Formats citations.
        4. Synthesizes response (LLM or intelligent local synthesizer).
        5. Handles low-confidence fallbacks.
        """
        query_stripped = query.strip()

        # Step 1: Emergency check
        if self.is_emergency_query(query_stripped):
            return {
                "answer": self.get_emergency_response(),
                "confidence_score": 1.0,
                "is_fallback": False,
                "sources": [
                    Citation(
                        title="Emergency & 24/7 Trauma Care Protocol",
                        category="Emergency Services",
                        department="Emergency Care",
                        content_snippet="Emergency contact number: 108. Trauma center and ambulance operational 24/7.",
                        relevance_score=1.0,
                        source="emergency_protocol.txt"
                    )
                ],
                "suggested_follow_ups": [
                    "Is ambulance service available?",
                    "What is the emergency contact number?",
                    "Where is the emergency department located?"
                ],
                "category": "Emergency Services",
                "disclaimer": CLINIC_DISCLAIMER
            }

        # Step 2: Vector retrieval
        matched_results = self.search_with_scores(query_stripped, top_k=top_k)

        # Build citations
        citations: List[Citation] = []
        for doc, score in matched_results:
            snippet = doc.page_content.strip()
            if len(snippet) > 250:
                snippet = snippet[:247] + "..."

            citations.append(
                Citation(
                    title=doc.metadata.get("title", "Clinic Knowledge Article"),
                    category=doc.metadata.get("category", "General"),
                    department=doc.metadata.get("department", "General Helpdesk"),
                    content_snippet=snippet,
                    relevance_score=round(score, 3),
                    source=str(doc.metadata.get("source", "clinic_kb"))
                )
            )

        top_score = matched_results[0][1] if matched_results else 0.0
        primary_category = matched_results[0][0].metadata.get("category", "General") if matched_results else "General"

        # Step 3: Check fallback threshold
        if not matched_results or top_score < CONFIDENCE_THRESHOLD:
            return {
                "answer": self.get_fallback_response(query_stripped),
                "confidence_score": round(top_score, 3),
                "is_fallback": True,
                "sources": citations[:1] if citations else [],
                "suggested_follow_ups": [
                    "What are the clinic timings?",
                    "How can I book an appointment?",
                    "What are the consultation charges?"
                ],
                "category": "Unclassified",
                "disclaimer": CLINIC_DISCLAIMER
            }

        # Step 4: Synthesize response
        if self.llm:
            answer_text = self.generate_llm_response(query_stripped, matched_results)
        else:
            answer_text = self.generate_local_response(query_stripped, matched_results)

        follow_ups = self.get_suggested_follow_ups(query_stripped, primary_category)

        return {
            "answer": answer_text,
            "confidence_score": round(top_score, 3),
            "is_fallback": False,
            "sources": citations,
            "suggested_follow_ups": follow_ups,
            "category": primary_category,
            "disclaimer": CLINIC_DISCLAIMER
        }
