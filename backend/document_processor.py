import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Returns a configured RecursiveCharacterTextSplitter for clinic documents."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "Q: ", "A: ", ". ", " ", ""],
        strip_whitespace=True
    )


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts text content from a PDF file using pypdf."""
    reader = PdfReader(str(pdf_path))
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append(f"[Page {idx + 1}]\n{text}")
    return "\n\n".join(pages_text)


def extract_text_from_file(file_path: Path) -> str:
    """Extracts text content from .txt, .md, or .pdf files."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".txt", ".md", ".json", ".csv"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported formats: .pdf, .txt, .md")


def chunk_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
    """Splits raw text into chunked Document objects with metadata attached."""
    if metadata is None:
        metadata = {}

    splitter = get_text_splitter()
    raw_docs = splitter.create_documents([text], metadatas=[metadata])

    # Assign unique chunk_index and ensure clean representation
    for i, doc in enumerate(raw_docs):
        doc.metadata["chunk_index"] = i
        doc.metadata["total_chunks"] = len(raw_docs)

    return raw_docs


def process_uploaded_file(file_path: Path, metadata: Dict[str, Any]) -> List[Document]:
    """Extracts text and chunks an uploaded document file."""
    text = extract_text_from_file(file_path)
    meta = {
        "title": metadata.get("title", file_path.stem.replace("_", " ").title()),
        "source": file_path.name,
        "category": metadata.get("category", "Uploaded Documents"),
        "department": metadata.get("department", "General Helpdesk"),
        "tags": metadata.get("tags", ["document", file_path.suffix.lstrip(".")]),
    }
    return chunk_text(text, meta)


def parse_faq_txt(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses Q&A pairs from a text file formatted with Q: and A:
    Returns list of dicts with title, content, and category.
    """
    if not file_path.exists():
        return []

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Regex to capture Q: ... A: ... blocks
    qa_blocks = re.findall(r"Q:\s*(.*?)\s*\nA:\s*(.*?)(?=\n\s*Q:|\Z)", content, flags=re.DOTALL)
    results = []

    for q, a in qa_blocks:
        question = q.strip()
        answer = a.strip()
        if not question or not answer:
            continue

        # Simple department categorization heuristic
        q_lower = question.lower()
        if any(w in q_lower for w in ["emergency", "ambulance", "108"]):
            dept = "Emergency Care"
            cat = "Emergency Services"
        elif any(w in q_lower for w in ["pediatric", "child", "children"]):
            dept = "Pediatrics"
            cat = "Specialist Care"
        elif any(w in q_lower for w in ["cardiology", "heart"]):
            dept = "Cardiology"
            cat = "Specialist Care"
        elif any(w in q_lower for w in ["dental", "teeth"]):
            dept = "Dental Clinic"
            cat = "Specialist Care"
        elif any(w in q_lower for w in ["charge", "cost", "fee", "payment", "insurance", "upi"]):
            dept = "Billing & Insurance"
            cat = "Billing"
        elif any(w in q_lower for w in ["lab", "blood", "covid", "test", "diagnostic"]):
            dept = "Laboratory & Diagnostics"
            cat = "Diagnostics"
        elif any(w in q_lower for w in ["timing", "hour", "open", "day", "walk-in", "appointment"]):
            dept = "Appointments & Front Desk"
            cat = "Appointments & Timings"
        elif any(w in q_lower for w in ["pharmacy", "medicine"]):
            dept = "Pharmacy"
            cat = "Pharmacy Services"
        else:
            dept = "General Helpdesk"
            cat = "General Information"

        results.append({
            "title": f"FAQ: {question}",
            "content": f"**Question:** {question}\n\n**Answer:** {answer}",
            "category": cat,
            "department": dept,
            "tags": ["faq", dept.lower().replace(" ", "-")],
            "author": "Clinic Staff",
            "status": "published"
        })

    return results
