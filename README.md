# AI Compliance Platform

A production-ready Django platform for analyzing enterprise documents against compliance standards such as ISO9001, ISO27001, GDPR, and more. The system combines OCR-based document ingestion, Retrieval Augmented Generation (RAG), a Neo4j knowledge graph, and an orchestrated AI agent pipeline to provide compliance scoring, risk detection, and actionable recommendations.

## ✅ Key Features

- ✅ **Multi-format document ingestion:** PDF, DOCX, PPTX, and images (OCR via Tesseract)
- ✅ **Dynamic compliance standards:** Add new standards and controls via Django admin
- ✅ **RAG pipeline:** Embeddings with `sentence-transformers` + vector search stored in PostgreSQL + `pgvector`
- ✅ **Knowledge graph:** Standards and controls modeled in Neo4j
- ✅ **AI agent orchestration:** Parser, compliance, risk, and recommendation agents (LangGraph-ready)
- ✅ **Compliance scoring:** 0-100 scoring plus violations, risks, and recommendations
- ✅ **Analytics dashboard:** Document counts, average scores, violations by standard, risk distribution
- ✅ **Audit report generation:** PDF output via `reportlab`

---

## 📦 Project Structure

```
project/
  config/
    settings.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    documents/
    standards/
    compliance/
    analytics/
    agents/
    rag/
    graph/
    orchestration/
    services/
  reports/
  manage.py
  requirements.txt
  README.md
```

---

## 🔧 Installation

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate    # Windows
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Setup PostgreSQL (or SQLite) + Vector Store

1. Create a PostgreSQL database (e.g., `compliance_db`) and ensure it is accessible.
   - If you prefer a lightweight local setup, enable SQLite by setting `DJANGO_USE_SQLITE=True`.
2. Choose a vector database backend. Supported options:
   - `chromadb` (default, stores vectors locally under `./vector_store`)
   - `faiss` (local index file)
   - `qdrant` (remote service)

Configure the backend with environment variables (shown below).

### 4) Setup Neo4j

1. Install Neo4j (Desktop, Server, or Aura).
2. Configure credentials and note the bolt URI (default: `bolt://localhost:7687`).

---

## 🧩 Configuration

Copy and adjust environment variables as needed:

```bash
export DJANGO_SECRET_KEY='293ofd_^v5ftaraet4u+hj9$xf$i$)u&zbi&qdw1e#u)h4p)nn'
export DJANGO_DEBUG=True
export DJANGO_DB_ENGINE=django.db.backends.postgresql
export DJANGO_DB_NAME=compliance_db
export DJANGO_DB_USER=postgres
export DJANGO_DB_PASSWORD=postgres
export DJANGO_DB_HOST=localhost
export DJANGO_DB_PORT=5432

# Vector store backend (chromadb|faiss|qdrant)
export VECTOR_DB=chromadb
export CHROMADB_PERSIST_DIR=./vector_store

# (Optional) FAISS settings
# export VECTOR_DB=faiss
# export FAISS_PERSIST_PATH=./vector_store/faiss.index

# (Optional) Qdrant settings
# export VECTOR_DB=qdrant
# export QDRANT_URL=http://localhost:6333
# export QDRANT_COLLECTION=compliance_vectors

export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=neo4j123
```

> On Windows, use `set` (current session) or `setx` (persistent) instead of `export`.

---

## 🏃 Run the Platform

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open:

- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/
- Upload documents: http://localhost:8000/upload/
- Audit results: http://localhost:8000/audit-results/
- Analytics: http://localhost:8000/analytics/
- Standards manager: http://localhost:8000/standards/
- Compliance chat: http://localhost:8000/chat/

---

## 🧠 Workflow Example

### 1) Add a standard

Use the Django admin to create a **Standard** (e.g., `ISO9001`) and add multiple **Controls** for that standard.

### 2) Upload documents

- `POST /api/documents/upload/` (single file)
- `POST /api/documents/bulk-upload/` (multiple files)

### 3) Run a compliance audit

```http
POST /api/compliance/audit/
Content-Type: application/json

{
  "document_ids": [1, 2],
  "standard_id": 1
}
```

### 4) View analytics

`GET /api/analytics/dashboard/`

### 5) Generate PDF report

PDF audit reports are generated automatically after each audit and stored under `media/reports/`.

---

## 🧩 Extending Standards Dynamically

Standards and controls are stored in the database and can be updated via the Admin UI. No code changes are required to add new compliance frameworks.

---

## 🧪 Notes for Production

- Configure `DJANGO_DEBUG=False` for production
- Use a real secret key
- Setup proper media storage (S3, Azure Blob)
- Configure a real LLM backend (OpenAI, Azure, local) for better analysis
- Secure Neo4j and PostgreSQL access with strong passwords and network policies

---

## ✅ Final Goals

This platform is designed to allow users to:

- Upload documents
- Select a compliance standard
- Run an AI-led compliance audit
- Analyze multiple documents at once
- Review compliance scores, violations, and risks
- Generate PDF audit reports
