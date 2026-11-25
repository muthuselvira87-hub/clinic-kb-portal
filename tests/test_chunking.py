import pytest
from pathlib import Path
from backend.document_processor import (
    chunk_text,
    extract_text_from_file,
    parse_faq_txt,
    get_text_splitter
)
from backend.config import DATA_DIR


def test_text_splitter_configuration():
    """Verify text splitter has appropriate chunk size and overlap."""
    splitter = get_text_splitter()
    assert splitter._chunk_size == 500
    assert splitter._chunk_overlap == 80


def test_chunk_text_metadata_preservation():
    """Ensure chunked documents preserve custom metadata and chunk indices."""
    sample_text = (
        "MetroLife Health Clinic provides comprehensive healthcare services. "
        "Our cardiology unit features advanced echocardiography and stress testing equipment. "
        "Consultations are available Monday through Saturday. "
    ) * 10

    metadata = {
        "title": "Cardiology Services",
        "category": "Specialist Care",
        "department": "Cardiology"
    }

    chunks = chunk_text(sample_text, metadata)
    assert len(chunks) >= 1
    for i, c in enumerate(chunks):
        assert c.metadata["title"] == "Cardiology Services"
        assert c.metadata["category"] == "Specialist Care"
        assert c.metadata["department"] == "Cardiology"
        assert c.metadata["chunk_index"] == i
        assert "total_chunks" in c.metadata


def test_parse_faq_txt():
    """Verify parsing of Q&A blocks from data/faq.txt."""
    faq_file = DATA_DIR / "faq.txt"
    if faq_file.exists():
        faqs = parse_faq_txt(faq_file)
        assert len(faqs) > 0
        first_faq = faqs[0]
        assert "title" in first_faq
        assert "content" in first_faq
        assert "category" in first_faq
        assert "department" in first_faq
        assert "FAQ: " in first_faq["title"]


def test_extract_text_from_txt_and_md(tmp_path):
    """Test text extraction from markdown and text files."""
    sample_file = tmp_path / "test_doc.md"
    sample_file.write_text("# Clinic Guide\n\nWalk-ins are accepted from 9 AM.", encoding="utf-8")

    extracted = extract_text_from_file(sample_file)
    assert "# Clinic Guide" in extracted
    assert "Walk-ins are accepted" in extracted
