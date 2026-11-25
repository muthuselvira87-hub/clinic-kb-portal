# 🏥 Clinic Helpdesk Knowledge Base Portal (PRJ-090)
### **Internship Project at Softomatics Technology Services**

---

## 👨‍🎓 Student & Internship Information

| **Field** | **Details** |
|---|---|
| **Student Name** | **MUTHUSELVI.R.A** |
| **Institution** | **PSVPEC** |
| **Department** | **Information Technology (IT)** |
| **Register Number** | **411723205038** |
| **Email Address** | [muthuselvira87@gmail.com](mailto:muthuselvira87@gmail.com) |
| **Serial Number** | **115** |
| **Internship Organization** | **SOFTOMATICS TECHNOLOGY SERVICES** |
| **Project Code** | **PRJ-090** |
| **Project Name** | **Clinic Helpdesk KB Portal** |
| **Category** | **Knowledge Base Portals** |
| **Domain** | **Healthcare** |
| **Focus Area** | **Generative AI (GenAI) & RAG Systems** |
| **Repository** | [https://github.com/muthuselvira87-hub/clinic-kb-portal](https://github.com/muthuselvira87-hub/clinic-kb-portal) |

---

## 🌟 Executive Summary

The **Clinic Helpdesk KB Portal** is a production-grade Generative AI healthcare portal developed during the internship tenure at **Softomatics Technology Services**. Designed to bridge the communication gap between patients and hospital administration, the system combines **FastAPI**, **LangChain**, **Streamlit**, and **Chroma Vector Store** to provide:

1. **Instant, Verified Answers**: Semantic retrieval over official clinic articles, doctors' rosters, and department FAQs.
2. **Clinical Safety & Triage Protocols**: Immediate automatic detection of medical emergencies (e.g., acute chest pain, strokes, trauma) redirecting patients to dial **108** or visit the 24/7 ER.
3. **Traceable Citations**: Every generated response includes source attributions, relevant excerpts, and confidence scores.
4. **Administrative Content Governance**: Role-protected admin portal for article CRUD, multi-format document ingestion (`.pdf`, `.txt`, `.md`), and on-demand vector index rebuilding.
5. **Real-Time Helpdesk Analytics**: Automatic tracking of top patient inquiries, feedback ratings (thumbs up/down), and an **unanswered questions queue** that flags knowledge gaps for administrators.

---

## 🛠️ Technology Stack

| Layer | Component / Library | Purpose |
|---|---|---|
| **Frontend UI** | **Streamlit** (v1.57.0) | Interactive patient chat, knowledge base browser, admin suite, analytics dashboard |
| **Backend API** | **FastAPI** (v0.136.1) + **Uvicorn** | High-performance asynchronous REST API with auto OpenAPI docs |
| **GenAI & RAG** | **LangChain** (v1.2.17) | Document chunking, vector retrieval chains, and citation formatting |
| **Vector Store** | **Chroma DB** (v1.5.8) | Persistent embedding storage and cosine similarity retrieval |
| **Embeddings** | **Sentence-Transformers** (`all-MiniLM-L6-v2`) | 384-dimensional dense semantic vectors (works 100% offline & local) |
| **LLM Support** | **Hybrid RAG Synthesizer** (Local + OpenAI) | Intelligent local extractive generator + optional OpenAI `gpt-4o-mini` |
| **Relational DB** | **SQLite + SQLAlchemy** (v2.0.49) | Articles metadata, query logs, feedback ratings, and content gaps |
| **Doc Processing**| **PyPDF** (v6.10.2) + TextSplitter | Ingestion of clinical PDFs, Markdown manuals, and text files |
| **Validation** | **Pydantic** (v2.13.3) | Strict data schema validation for API inputs/outputs |

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │      Streamlit Web Portal (:8501)      │
                                  ├────────────────────────────────────────┤
                                  │  🩺 Patient Helpdesk Chat (Citations)  │
                                  │  📚 Knowledge Base Search & Directory  │
                                  │  🛠️ Admin Article & Document Manager  │
                                  │  📊 Real-time Query Analytics & Gaps   │
                                  └───────────────────┬────────────────────┘
                                                      │ HTTP REST (JSON)
                                                      ▼
                                  ┌────────────────────────────────────────┐
                                  │        FastAPI Backend (:8000)         │
                                  ├────────────────────────────────────────┤
                                  │  /api/chat       |  /api/articles      │
                                  │  /api/feedback   |  /api/documents     │
                                  │  /api/analytics  |  /api/index         │
                                  └───────────┬────────────────┬───────────┘
                                              │                │
                        ┌─────────────────────▼───────┐  ┌─────▼──────────────────────┐
                        │    LangChain RAG Pipeline   │  │    SQLite Relational DB    │
                        ├─────────────────────────────┤  ├────────────────────────────┤
                        │ • Sentence-Transformers Emb │  │ • Articles (CRUD & Status) │
                        │ • Chroma Vector Database    │  │ • Query Logs & Timestamps  │
                        │ • Emergency Triage Guard    │  │ • Patient Feedback (👍/👎) │
                        │ • Verified Source Citations │  │ • Unanswered Queries Queue │
                        │ • Fallback Response Engine  │  │                            │
                        └─────────────────────────────┘  └────────────────────────────┘
```

---

## 📅 3-Week Implementation & Verification Roadmap

### **Week 1: Knowledge Base Foundation & Document Parsing**
- **Implementation**:
  - Structured article schema with categories, departments, tags, and status.
  - Parsed baseline clinic FAQs (`data/faq.txt`) into structured medical Q&A entries.
  - Implemented `RecursiveCharacterTextSplitter` configured for medical chunk boundaries (chunk size: 500, overlap: 80).
  - Built document extraction support for `.txt`, `.md`, and `.pdf` formats via `pypdf`.
- **Testing & Verification**:
  - `tests/test_chunking.py`: Verified text splitting parameters, chunk index tracking, metadata preservation, and multi-format text extraction.

### **Week 2: LangChain RAG, Citations & Fallback Handling**
- **Implementation**:
  - Chroma vector store integration with dense semantic embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
  - Strict citation engine providing source article title, category, department, matched excerpt, and confidence score.
  - Emergency triage guardrail identifying urgent symptoms (chest pain, stroke, severe bleeding) with immediate **108** redirection.
  - Graceful fallback mechanism with clinic contact info for out-of-scope or low-confidence queries (< 0.45).
  - Admin index refresh workflow to rebuild Chroma embeddings when knowledge articles change.
- **Testing & Verification**:
  - `tests/test_rag_retrieval.py`: Verified standard retrieval precision, citation field structure, emergency detection, and out-of-scope fallback handling.

### **Week 3: UX, Access Control, Analytics & Final Documentation**
- **Implementation**:
  - Interactive multi-page Streamlit portal with clean healthcare styling.
  - Patient chat bubbles, quick prompt buttons, expander citations, and feedback buttons (👍/👎).
  - Admin portal with PIN protection (`admin123`), full article CRUD, and drag-and-drop file uploader.
  - Analytics dashboard featuring metrics, Top 10 Asked Questions bar chart, inquiries by medical department, and actionable unanswered queries queue.
  - Session history and CSV audit log downloads.
- **Testing & Verification**:
  - `tests/test_api_e2e.py`: Verified end-to-end FastAPI endpoints, article lifecycle (Create-Read-Update-Delete), query logging, and analytics aggregation.
  - Comprehensive automated runner (`run_tests.py`) validating all 13 test cases.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/muthuselvira87-hub/clinic-kb-portal.git
cd clinic-kb-portal
```

### 2. Environment Setup
Activate the Python virtual environment:
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Install requirements:
```bash
pip install -r requirements.txt
```

### 3. Launching the Application
You can start both the backend and frontend with a single command:
```bash
python run.py
```

Or run services independently:
```bash
# Terminal 1: Launch FastAPI Backend (Port 8000)
python run.py --backend

# Terminal 2: Launch Streamlit Web Portal (Port 8501)
python run.py --frontend
```

### 4. Application URLs
- 🌐 **Patient & Admin Web Portal**: [http://127.0.0.1:8501](http://127.0.0.1:8501)
- 📑 **FastAPI Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Check**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 5. Staff Admin Credentials
- **Default Admin PIN**: `admin123` *(Configurable via `ADMIN_PIN` in `.env`)*

---

## 🧪 Automated Test Suite Results

Run the full end-to-end verification suite:
```powershell
.\venv\Scripts\python.exe -u run_tests.py
```

### Output:
```text
======================================================================
RUNNING CLINIC HELPDESK KB PORTAL TEST SUITE (PRJ-090)
======================================================================

--- [WEEK 1 TESTS]: Chunking & Ingestion ---
  * Text Splitter Configuration                             [PASS]
  * Metadata & Chunk Index Preservation                     [PASS]
  * FAQ Q&A Text Parser                                     [PASS]
  * Text/MD File Text Extraction                            [PASS]

--- [WEEK 2 TESTS]: RAG Retrieval, Citations & Fallback ---
  * Standard Query Retrieval & Accuracy                     [PASS]
  * Citation Structure & Fields Validation                  [PASS]
  * Emergency Triage Detection & Alert                      [PASS]
  * Out-of-Scope Fallback Handling                          [PASS]

--- [WEEK 3 TESTS]: FastAPI Endpoints, Analytics & CRUD ---
  * API Root & Health Check Endpoint                        [PASS]
  * Knowledge Article CRUD & Auto-Index                     [PASS]
  * Chat Q&A Flow with Feedback Submission                  [PASS]
  * Analytics Aggregation & Insights                        [PASS]
  * Vector Store Index Status & Rebuild                     [PASS]

======================================================================
TEST EXECUTION SUMMARY:
  * Total Tests : 13
  * Passed      : 13 [PASS]
  * Failed      : 0 
  * Elapsed Time: 34.50s
======================================================================
ALL TESTS PASSED SUCCESSFULLY!
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status and available endpoint directory |
| `POST` | `/api/chat` | Patient question processing via RAG, citations & triage |
| `POST` | `/api/feedback` | Record patient rating (+1 helpful, -1 unhelpful) |
| `GET` | `/api/chat/history` | Retrieve conversation history for session |
| `GET` | `/api/articles` | Filter articles by category, tag, department, search |
| `POST` | `/api/articles` | Create new article and synchronize Chroma vector store |
| `PUT` | `/api/articles/{id}` | Update existing article content and metadata |
| `DELETE`| `/api/articles/{id}` | Delete article from knowledge base |
| `GET` | `/api/articles/categories`| Distinct categories with article count |
| `GET` | `/api/articles/tags` | Distinct tags with frequency |
| `POST` | `/api/documents/upload` | Ingest `.pdf`, `.txt`, `.md` files and index chunks |
| `GET` | `/api/documents` | List uploaded files |
| `GET` | `/api/index/status` | Vector store statistics and embeddings model info |
| `POST` | `/api/index/rebuild` | Trigger complete re-indexing of knowledge base |
| `GET` | `/api/analytics/summary`| Metrics, top questions, department distributions |
| `GET` | `/api/analytics/unanswered` | Unanswered queries queue |
| `POST` | `/api/analytics/unanswered/{id}/resolve` | Mark unanswered query as resolved |

---

## 💡 Key Clinical Knowledge Domains Covered
The knowledge base includes verified medical administrative information across:
- **Cardiology & Heart Care**: OPD hours, senior cardiologists, ECG, 2D Echo, consultation fee (Rs. 600).
- **Pediatrics & Child Wellness**: Child health checkups, vaccination schedules, female pediatricians.
- **Dermatology & Skin Care**: Acne, eczema, skin procedures, Tuesday/Thursday/Saturday clinic.
- **Diagnostic Laboratory & Radiology**: 24/7 NABL blood tests, digital X-Ray, ultrasound, home collection.
- **Billing & Cashless Insurance**: Star Health, ICICI Lombard, HDFC ERGO cashless network, UPI/Card payments.
- **Emergency & Trauma Care**: 24/7 ALS ambulance, Casualty unit, emergency contact (**108**).
- **Pharmacy & Home Delivery**: In-house pharmacy hours (8 AM - 10 PM), free delivery within 5 km.
- **Appointments & Teleconsultation**: Online booking, walk-in recommendations, video consults.

---

## 🏆 Project Milestones & Achievements

- ✅ **Full 3-Week Scope Completed**: All deliverables for Week 1, Week 2, and Week 3 implemented and verified.
- ✅ **100% Offline Capability**: Built-in intelligent local RAG synthesizer functions seamlessly without any external API keys or cloud dependencies.
- ✅ **Zero Cost & Production Ready**: Uses open-source Sentence-Transformers, Chroma DB, and FastAPI.
- ✅ **Comprehensive Test Suite**: Automated verification script passing all 13 end-to-end test cases.

---

## 🤝 Acknowledgments

This project was developed as part of the internship program at **Softomatics Technology Services**. Heartfelt thanks to the technical mentors and leadership at Softomatics for their guidance in building enterprise-grade GenAI healthcare systems.
