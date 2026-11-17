# Semantic Job Matching Engine

A hybrid semantic search and resume-to-job matching engine built with **FastAPI**, **PostgreSQL + pgvector**, **Google Gemini API**, and **React**.

## Architecture & How It Works

```
[Candidate Query or Resume]
            │
            ▼
    [Google Gemini]
   (Embeddings: 768-dim)
            │
     ┌──────┴───────────────────────────┐
     ▼                                  ▼
[Postgres pgvector]            [Postgres Full-Text]
  Cosine Distance (HNSW)          BM25 / tsvector (GIN)
     │                                  │
     └──────────────┬───────────────────┘
                    ▼
       [Reciprocal Rank Fusion (RRF)]
                    │
                    ▼
          [Top-K Ranked Jobs]
                    │
                    ▼
   [Grounded Match Explanations]
  (Matched vs. Missing Skills verified)
```

## Step 1: Setup & Initialization Guide

### 1. Create Python Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```
Inside `.env`:
```env
DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"
GEMINI_API_KEY="AIzaSy..."
GEMINI_MODEL="gemini-2.5-flash"
EMBED_MODEL="text-embedding-004"
EMBED_DIM=768
```

### 4. Initialize Database Schema
Initializes `pgvector`, the `jobs` table, the HNSW vector index, and the GIN full-text index:
```bash
python scripts/init_db.py
```

### 5. Generate / Load Jobs & Embeddings
If you do not have a `data/raw/jobs.csv`, generate 500 synthetic jobs:
```bash
python scripts/make_synthetic_jobs.py --count 500
```
Then clean, embed (using Gemini `text-embedding-004`), and insert them into PostgreSQL:
```bash
python scripts/load_jobs.py
```

### 6. Verify Records & Vector Search in Database
Run the verification script:
```bash
python scripts/verify_db.py
```

### 7. Run Backend API
```bash
uvicorn backend.app.main:app --reload --port 8000
```
Visit http://127.0.0.1:8000/health or http://127.0.0.1:8000/docs for Swagger UI.
