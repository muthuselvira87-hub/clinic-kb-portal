import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session

from backend.config import UPLOADS_DIR
from backend.database import get_db, Article
from backend.document_processor import process_uploaded_file, extract_text_from_file
from backend.rag_engine import RAGEngine

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("Uploaded Documents"),
    department: Optional[str] = Form("General Helpdesk"),
    db: Session = Depends(get_db)
):
    """
    Uploads a document (.txt, .md, .pdf), chunks its content,
    indexes into Chroma vector store, and stores article record.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    suffix = Path(filename).suffix.lower()
    if suffix not in [".txt", ".md", ".pdf"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed formats: .txt, .md, .pdf"
        )

    file_save_path = UPLOADS_DIR / filename
    try:
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    article_title = title if title and title.strip() else Path(filename).stem.replace("_", " ").title()

    try:
        # Extract text and chunk
        metadata = {
            "title": article_title,
            "category": category,
            "department": department,
            "tags": ["document", suffix.lstrip(".")],
            "source": filename
        }
        chunks = process_uploaded_file(file_save_path, metadata)
        full_text = extract_text_from_file(file_save_path)

        # Index chunks in Chroma
        rag = RAGEngine.get_instance()
        rag.add_documents(chunks)

        # Save record in articles table
        article_record = Article(
            title=article_title,
            content=full_text,
            category=category,
            tags='["document", "' + suffix.lstrip(".") + '"]',
            department=department,
            author="Document Ingestion",
            status="published",
            source_file=filename,
            created_at=datetime.utcnow()
        )
        db.add(article_record)
        db.commit()
        db.refresh(article_record)

        return {
            "status": "success",
            "message": f"File '{filename}' processed successfully.",
            "article_id": article_record.id,
            "chunks_created": len(chunks),
            "filename": filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse and index document: {str(e)}")


@router.get("")
def list_uploaded_documents():
    """Lists all uploaded documents stored in data/uploads."""
    files = []
    for file_path in UPLOADS_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 1),
                "extension": file_path.suffix.lower(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    return files
