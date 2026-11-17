# Semantic Job Matching Engine

A production-grade, hybrid semantic search and resume-to-job matching engine designed to solve the limitations of traditional keyword-based recruitment systems. Built with **FastAPI**, **PostgreSQL + pgvector**, **Google Gemini**, and **React + TypeScript + Tailwind CSS**.

---

## 📌 Executive Summary & Problem Solved

Traditional applicant tracking systems (ATS) and job boards rely predominantly on **exact keyword matching** (e.g., standard BM25 lexical search). This creates significant inefficiencies:
* **The Vocabulary Mismatch Problem**: A candidate who writes *"engineered scalable REST APIs with Flask"* will often be excluded from a job posting titled *"Python Backend Engineer"* that explicitly lists *"FastAPI / web microservices"*, despite having the ideal skill set.
* **Semantic Drift in Pure Vector Search**: Pure vector retrieval can sometimes overlook specific domain acronyms, certification prerequisites, or exact tool versions.
* **The "Black Box" Recommendation Problem**: Existing recommendation systems provide ranked lists without explanations, leaving candidates and hiring managers with no insight into *why* a profile matched or what specific skill gaps exist.

### The Solution:
The **Semantic Job Matching Engine** combines **dense vector embeddings** (via Google Gemini `gemini-embedding-001` and PostgreSQL `pgvector`) with **sparse lexical retrieval** (PostgreSQL Full-Text Search with `tsvector`) fused together using **Reciprocal Rank Fusion (RRF)**. It features **in-memory LLM resume parsing**, **candidate-to-job matching**, and **grounded explanations** with programmatic hallucination checks.

---

## 🚀 Key Features

* **🔍 Dense Vector Semantic Search**:
  * Converts natural-language user queries into 768-dimensional dense vectors using Google Gemini.
  * Queries PostgreSQL using `pgvector`'s cosine distance operator (`<=>`) accelerated by an **HNSW (Hierarchical Navigable Small World)** index.
  * Understands engineering intent, role responsibilities, and tooling synonyms beyond exact words.

* **⚡ Hybrid Search with Reciprocal Rank Fusion (RRF)**:
  * Executes parallel retrieval: Lexical full-text search (`tsvector` + GIN index) and Vector similarity search (`pgvector` + HNSW index).
  * Fuses both ranked lists into a single calibrated ranking using Reciprocal Rank Fusion ($k=60$):
    $$\text{RRF Score}(d) = \sum_{m \in \text{modes}} \frac{1}{k + \text{rank}_m(d)}$$
  * Provides superior retrieval precision over both pure keyword and pure vector baselines.

* **📄 In-Memory Resume Parsing (Privacy-Preserving)**:
  * Extracts text from uploaded PDF or plain-text resumes in memory using `pypdf`.
  * Prompts Gemini with strict structured JSON schema output to parse the resume into a strongly-typed `Profile` model (headline, skills, roles, years of experience, education, and summary).
  * Resumes are processed in memory and discarded immediately to preserve applicant privacy.

* **🎯 Profile-to-Job Matching**:
  * Maps parsed candidate profiles against 500+ indexed tech jobs to produce an instant ranked match list with similarity scores.
  * Provides an interactive UI where candidates can review and edit their extracted profile before running matches.

* **💡 Grounded & Explainable Recommendations**:
  * An on-demand `/explain` endpoint uses Gemini to analyze the candidate profile against the selected job posting.
  * Generates an itemized breakdown of **Matched Skills**, **Missing Skills**, and a concise 2–3 sentence fit justification.
  * **Zero-Hallucination Guardrail**: Programmatic grounding validation verifies that every claimed matched skill exists in the resume profile, and every missing skill is explicitly cited in the job description.

* **📊 Automated Offline Evaluation Framework**:
  * Features an evaluation suite (`eval/run_eval.py`) across 20 diverse candidate benchmark profiles.
  * Compares **Precision@10** and **NDCG@10** across Keyword, Vector, and Hybrid modes using an LLM-as-a-judge with a fixed calibration rubric.

* **🛡️ Resilient Ingestion & Embedding Cache**:
  * Ingestion pipeline (`scripts/load_jobs.py`) normalizes varying CSV schemas, removes duplicate listings, and batches embedding calls.
  * Features persistent local disk caching (`data/cache/embeddings.json`) and automated exponential backoff to respect Google AI Studio Free Tier rate limits.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Ingestion Pipeline"]
        RawCSV["Jobs CSV (500+ records)"] --> Cleaner["Deduplicate & Normalize"]
        Cleaner --> EmbedBatch["Gemini Embedding (768-dim)"]
        EmbedBatch --> DiskCache[("Disk Cache: embeddings.json")]
        EmbedBatch --> PGStore[("Neon PostgreSQL")]
    end

    subgraph Storage["2. Dual-Index PostgreSQL Storage"]
        PGStore --> HNSW["HNSW Index (vector_cosine_ops)"]
        PGStore --> GIN["GIN Index (tsvector English)"]
    end

    subgraph Retrieval["3. Hybrid Retrieval Engine"]
        UserQuery["Candidate Query / Resume Profile"] --> QueryEmbed["Gemini Embedder"]
        QueryEmbed --> VectorSearch["Vector ANN Search (Top-20)"]
        UserQuery --> KeywordSearch["Postgres Full-Text Search (Top-20)"]
        VectorSearch --> RRF["Reciprocal Rank Fusion (k=60)"]
        KeywordSearch --> RRF
        RRF --> TopK["Top-K Calibrated Job Matches"]
    end

    subgraph Explainability["4. Grounded Explainability"]
        TopK --> ExplainPrompt["Gemini Grounded Reasoning"]
        ExplainPrompt --> GroundingCheck{"Programmatic Grounding Verification"}
        GroundingCheck -- Validated --> OutputUI["Interactive UI (Matched vs Missing Skills)"]
        GroundingCheck -- Hallucination Flagged --> FilteredOutput["Sanitized Output"]
    end
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite | Fast, responsive single-page application with type safety. |
| **Styling** | Tailwind CSS, Lucide Icons | Clean, modern SaaS aesthetic with minimal bundle footprint. |
| **Backend API** | Python 3.12, FastAPI, Uvicorn | High-performance asynchronous REST API with automatic OpenAPI docs. |
| **Validation** | Pydantic v2, Pydantic-Settings | Enforces strict schema validation for requests, responses, and LLM outputs. |
| **Database** | PostgreSQL (Neon.tech serverless) | Primary database hosting relational data and vector indexes. |
| **Vector Engine** | `pgvector` (HNSW indexing) | Nearest-neighbor vector similarity search directly in SQL (`<=>`). |
| **Lexical Engine**| PostgreSQL Full-Text (`tsvector` + GIN) | BM25-like keyword matching using `websearch_to_tsquery`. |
| **AI / Embeddings** | Google Gemini `gemini-embedding-001` | 768-dimensional dense semantic embeddings via `google-genai` SDK. |
| **AI / Generation** | Google Gemini `gemini-2.5-flash` | Structured JSON profile parsing, grounded explanations, eval judge. |
| **PDF Extraction**| `pypdf` | Fast, lightweight in-memory PDF text extraction with zero OS dependencies. |
| **Testing** | `pytest`, `pytest-mock` | Unit tests for RRF algorithm, schema validation, and grounding logic. |

---

## 📁 Repository Structure

```text
job-searching-engine/
├── .env.example               # Environment variables template
├── .gitignore                 # Secrets, cache, and artifact exclusions
├── README.md                  # Complete project documentation and guide
├── schema.sql                 # DDL: jobs table, pgvector extension, HNSW and GIN indexes
├── pytest.ini                 # Pytest configuration
│
├── backend/
│   ├── requirements.txt       # Python backend dependencies
│   ├── app/
│   │   ├── main.py            # FastAPI entry point, CORS, and endpoint routing
│   │   ├── config.py          # Environment settings (EMBED_DIM = 768 single source of truth)
│   │   ├── db.py              # PostgreSQL connection pool, pgvector registration & DNS fallback
│   │   ├── schemas.py         # Pydantic schemas (JobResult, Profile, Explanation, SearchQuery)
│   │   ├── embeddings.py      # Gemini embedding manager with batching, retries, and disk cache
│   │   ├── search.py          # Vector search, full-text search, and RRF fusion implementation
│   │   ├── resume.py          # In-memory PDF text extraction and LLM structured profile parsing
│   │   └── explain.py         # Match explanation generation with programmatic grounding check
│   └── tests/
│       ├── test_step1.py      # Unit tests for configuration, schema, and cache hashing
│       └── test_step2.py      # Integration tests for vector search and semantic retrieval
│
├── frontend/                  # React + TypeScript + Vite + Tailwind CSS web application
│   ├── package.json
│   ├── vite.config.ts         # Vite configuration with proxy
│   ├── tailwind.config.js     # Tailwind CSS theme configuration
│   └── src/
│       ├── main.tsx           # React mounting point
│       ├── App.tsx            # Main application layout and state management
│       ├── api.ts             # Typed API client for FastAPI endpoints
│       ├── types.ts           # Shared TypeScript interfaces
│       └── components/
│           ├── Navbar.tsx     # Navigation header with branding
│           ├── SearchBar.tsx  # Natural-language search input with suggested query pills
│           ├── JobList.tsx    # Results container (loading skeletons, error handling, empty states)
│           └── JobCard.tsx    # Job display card with score badge, company, location, snippet
│
├── data/
│   ├── raw/jobs.csv           # 500+ cleaned job postings dataset
│   └── cache/embeddings.json  # Local persistent disk cache for 768-dim embeddings
│
├── scripts/
│   ├── init_db.py             # Database schema initialization and index verification
│   ├── make_synthetic_jobs.py # Realistic dataset generator across 8 technical domains
│   ├── load_jobs.py           # Ingestion pipeline: cleaning, batch embedding, and DB insertion
│   └── verify_db.py           # Database verification script (row counts, vector math, FTS)
│
└── eval/                      # Evaluation suite for offline metrics (Step 6)
    ├── profiles.jsonl         # 20 diverse candidate benchmark profiles
    ├── rubric.md              # LLM judge grading rubric
    └── run_eval.py            # Precision@10 & NDCG@10 comparative evaluation script
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
* **Python 3.11+** installed
* **Node.js 18+** & **npm** installed
* A hosted PostgreSQL instance with `pgvector` enabled (e.g., [Neon.tech](https://neon.tech))
* A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
# Neon PostgreSQL connection string (with pgvector enabled)
DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/job_matching?sslmode=require"

# Google Gemini API Key
GEMINI_API_KEY="AIzaSy..."

# Model & Embedding settings
GEMINI_MODEL="gemini-2.5-flash"
EMBED_MODEL="gemini-embedding-001"
EMBED_DIM=768
```

### 3. Backend Setup & Ingestion
```powershell
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Initialize Database Schema
python scripts/init_db.py

# 4. Generate & Ingest 500 Jobs with Gemini Embeddings
python scripts/load_jobs.py

# 5. Verify Database Records and Vector Search
python scripts/verify_db.py
```

### 4. Run the Project
Open two terminals:

#### Terminal 1 (Backend API):
```powershell
uvicorn backend.app.main:app --reload --port 8001
```
* Interactive API Documentation (Swagger UI): [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
* Health check: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

#### Terminal 2 (Frontend UI):
```powershell
cd frontend
npm run dev
```
* Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Testing

Run the automated test suite using `pytest`:
```powershell
pytest
```
* **Step 1 Tests**: Schema structure, environment defaults, column alias mappings, and cache hashing.
* **Step 2 Tests**: Vector search similarity calculation, `GET /search` API integration, semantic relevance, and input validation.

---

## 📅 Development Roadmap & Status

- [x] **Step 1: Project Setup, Schema, Ingestion & Embeddings**
  - PostgreSQL schema with `vector(768)` and HNSW index.
  - Gemini embedding generation with batching, rate-limit backoff, and disk cache.
  - Ingestion of 500 jobs into Neon PostgreSQL.
- [x] **Step 2: Semantic Search API & Minimal Search Page**
  - `GET /search` endpoint using pgvector cosine distance.
  - Modern React + TypeScript + Vite + Tailwind CSS frontend interface.
  - Live search verification with semantic query relevance.
- [ ] **Step 3: Resume Upload & Profile Matching**
  - In-memory PDF text extraction (`pypdf`).
  - Structured profile parsing with Gemini.
  - Editable candidate profile UI and resume-to-job matching.
- [ ] **Step 4: Hybrid Retrieval with Reciprocal Rank Fusion (RRF)**
  - Full-text search with `tsvector` and `ts_rank`.
  - Reciprocal Rank Fusion ($k=60$) combining keyword and vector results.
  - Toggle between `keyword`, `vector`, and `hybrid` modes.
- [ ] **Step 5: Grounded Match Explanations**
  - `POST /explain` with itemized matched vs. missing skills.
  - Programmatic grounding verification to eliminate hallucinations.
- [ ] **Step 6: Mini Evaluation Framework**
  - Automated benchmark comparing Keyword vs. Vector vs. Hybrid across 20 profiles.
  - Measurement of Precision@10 and NDCG@10.
- [ ] **Step 7: Production Deployment & Rate Limiting**
  - Live deployment of backend and frontend.
