import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "db"
SQLITE_DB_PATH = DATA_DIR / "clinic_kb.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Vector & RAG Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_COLLECTION_NAME = "clinic_kb_collection"
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))

# Clinic Metadata & Emergency Info
CLINIC_NAME = "MetroLife Health Clinic & Specialty Care"
CLINIC_LOCATION = "42 Health Avenue, Chennai, India"
CLINIC_PHONE = "+91 44 2800 1234"
CLINIC_EMAIL = "helpdesk@metrolifeclinic.com"
CLINIC_EMERGENCY_NUMBER = "108"
CLINIC_TIMINGS = "Mon - Sat: 8:00 AM - 8:00 PM | Sun: 9:00 AM - 1:00 PM | Emergency: 24/7"

# Admin Authentication
ADMIN_PIN = os.getenv("ADMIN_PIN", "admin123")

# Optional External LLM Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
