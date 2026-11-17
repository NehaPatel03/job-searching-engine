Semantic Job Matching Engine: MVP Spec for Antigravity
Prepared for Neha Patel. A fast, minimal build of a resume-to-job matching and semantic search engine, designed to finish in 7 to 10 days and to demonstrate retrieval, ranking, LLM structured outputs, evaluation and a Python backend.
How to use this document
Open an empty project folder in Antigravity and save this file as SPEC.md in the root.
Paste the kickoff prompt below.
Let the agent build ONE step at a time. Run it, check it, then tell it to continue.
Kickoff prompt:
Read SPEC.md fully. Do not write code yet. First reply with a short plan: the folder structure you will create, the libraries you will use, and any questions or assumptions. After I approve, implement Step 1 only, explain how to run and test it, and stop. Continue one step at a time only when I say so. Keep the code simple and readable, because I must be able to explain every part in an interview.
1. Project overview
Problem. Job boards rely on keyword search. A candidate who writes 'built REST services in Flask' may never see a 'Python backend engineer' role, and recommendations come with no explanation.
Solution. A web app where a user can (a) type a natural-language query and get semantically relevant jobs, and (b) upload a resume, have it parsed into a structured profile, and get a ranked list of matching jobs with a short, grounded explanation of why each one fits and which skills are missing.
How it works (pipeline).
Jobs CSV -> clean and normalize -> embed -> Postgres + pgvectorQuery or resume -> (resume: LLM parses to Profile JSON) -> query text   -> keyword search (Postgres full-text)  \   -> vector search (pgvector)             -> RRF fusion -> top K jobs   -> LLM explanation per top job (grounded in the job text)
What this demonstrates. Embeddings and semantic search, hybrid retrieval and ranking, structured LLM outputs, grounding checks, SQL, a Python (FastAPI) backend, and a small evaluation that compares keyword, vector and hybrid retrieval.
2. MVP scope
In scope:
Load 500 to 2,000 jobs from a static dataset
Embeddings stored in Postgres with pgvector
Semantic search endpoint and page
Resume upload (PDF or text), parsed into a structured profile
Resume-to-jobs ranking
Hybrid retrieval with RRF fusion
Per-job explanation with matched and missing skills
A mini evaluation with about 20 test profiles
Deployment with a live link
Out of scope for the MVP (do NOT build these unless asked):
User accounts and login
Live scraping or scheduled ingestion
Save, like or dislike personalization
Heavy filters, notifications, admin pages
Multi-service microservices
3. Ground rules for the agent
Keep it simple: one FastAPI backend, one React frontend, one Postgres database. No extra frameworks unless justified.
Explain choices briefly and keep functions small and typed.
Never hardcode secrets. Use a .env file and provide .env.example.
Read model names from env vars (GEMINI_MODEL, EMBED_MODEL) and check the current Gemini API docs before choosing defaults. Keep the embedding size in one constant, EMBED_DIM.
Handle API rate limits with batching, retries and backoff. Cache embeddings to disk so re-runs do not re-embed everything.
Never invent data or metrics. All evaluation numbers must come from scripts that actually run.
Add a few pytest tests for core logic (RRF fusion, profile parsing validation, grounding check).
Stop after each step and summarize what changed and how to test it.
4. Tech stack
Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic, psycopg (v3) or SQLAlchemy, pgvector Python package
Database: PostgreSQL with the pgvector extension (a free hosted instance from a pgvector-capable provider such as Neon or Supabase, used for both development and deployment; no Docker)
LLM and embeddings: Google Gemini API (google-genai SDK)
Resume text extraction: pypdf (or pdfplumber)
Frontend: React + TypeScript + Vite + Tailwind CSS
Tests: pytest
5. Repo layout
/backend  /app    main.py            # FastAPI app and routes    config.py          # env settings    db.py              # connection and queries    schemas.py         # Pydantic models    embeddings.py      # embed with batching, retry and disk cache    search.py          # keyword, vector, RRF, hybrid    resume.py          # PDF text extraction, LLM profile parsing    explain.py         # per-job explanation and grounding check  /tests/frontend              # Vite React TS app/data  /raw                 # jobs.csv (dataset file placed here)/scripts  load_jobs.py         # clean, insert, embed  make_synthetic_jobs.py   # fallback dataset generator/eval  profiles.jsonl       # test profiles  run_eval.py  results/schema.sql             # table and index definitions.env.exampleREADME.md
6. Database schema
CREATE EXTENSION IF NOT EXISTS vector;CREATE TABLE jobs (  id SERIAL PRIMARY KEY,  title TEXT NOT NULL,  company TEXT,  location TEXT,  experience_level TEXT,  skills TEXT,  description TEXT NOT NULL,  embedding vector(768),  tsv tsvector GENERATED ALWAYS AS (    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(skills,'') || ' ' || coalesce(description,''))  ) STORED);CREATE INDEX jobs_embedding_idx ON jobs USING hnsw (embedding vector_cosine_ops);CREATE INDEX jobs_tsv_idx ON jobs USING gin (tsv);
The vector size must match EMBED_DIM; request a 768-dimension output from the embedding model if it supports that.
Step 1: Project setup, data and embeddings (about 1.5 days)
Create the folder structure, .env.example, and the schema as a plain schema.sql file. Create a free hosted Postgres database on Neon or Supabase, enable the pgvector extension, put its connection string in .env as DATABASE_URL, and apply the schema with a small Python script. Do not use Docker or Docker Compose.
Data: the user will download a public job postings dataset from Kaggle (for example a LinkedIn job postings dataset) and place it at data/raw/jobs.csv. Do not try to download it yourself. If the file is missing, run scripts/make_synthetic_jobs.py to generate about 500 synthetic job postings with Gemini across varied roles (backend, frontend, data, ML, DevOps, QA, product) and say clearly in the README that the data is synthetic.
scripts/load_jobs.py: read the CSV, map columns to the schema (inspect the CSV and adapt), drop rows with empty descriptions, deduplicate on title plus company, keep 500 to 2,000 rows, and insert them.
Embedding text for each job: title, company, skills and the first ~1,500 characters of the description. Embed in batches with retry and backoff, cache results on disk, and store vectors in jobs.embedding.
Acceptance: the schema applies to the hosted database, then python scripts/load_jobs.py fills the table; a quick SQL check shows row counts and non-null embeddings.
Step 2: Semantic search API and page (about 1 day)
GET /search?q=...&k=10 embeds the query and returns the nearest jobs by cosine similarity using pgvector.
Response model:
class JobResult(BaseModel):    job_id: int    title: str    company: str | None    location: str | None    score: float    snippet: str   # first ~250 characters of the description
Frontend search page: a query box, a results list showing title, company, location and snippet, loading and error states.
Enable CORS for the frontend dev URL.
Acceptance: searching 'python backend developer' returns relevant jobs even when the exact words differ; the page displays them.
Step 3: Resume upload and profile matching (about 1.5 days)
POST /resume/parse accepts a PDF or text file, extracts text, and asks Gemini to return a structured profile. Validate with Pydantic; on failure retry once, passing the validation error back to the model.
class Profile(BaseModel):    headline: str    skills: list[str]    roles: list[str]    years_experience: float    education: str | None    summary: str
POST /match accepts a Profile (the user may edit it in the UI first) and returns the top K jobs. For now, build a query text from headline, roles and skills, embed it, and run vector search.
Frontend match page: upload a resume, show the parsed profile in an editable form, then show ranked jobs with scores.
Do not store uploaded resumes. Process in memory and discard.
Acceptance: uploading a sample resume produces a sensible profile and a ranked job list.
Step 4: Hybrid retrieval with RRF (about 1 day)
Implement in search.py.
Keyword search with Postgres full-text:
SELECT id FROM jobsWHERE tsv @@ websearch_to_tsquery('english', %s)ORDER BY ts_rank(tsv, websearch_to_tsquery('english', %s)) DESCLIMIT 20;
Vector search returns its top 20 ids.
Fuse the two ranked lists with Reciprocal Rank Fusion:
def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:    scores: dict[int, float] = {}    for ranking in rankings:        for rank, doc_id in enumerate(ranking):            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)    return sorted(scores, key=scores.get, reverse=True)
Add a mode parameter to /search and /match: keyword, vector or hybrid (default). The evaluation compares these modes, so all three must stay available.
Optional stretch, only if time remains: an LLM rerank of the fused top 20 down to 10, behind a flag.
Acceptance: unit test for rrf; all three modes return results; a query with an exact rare keyword now works better in hybrid mode than in vector mode.
Step 5: Grounded match explanations (about 1 day)
POST /explain takes a Profile and a job_id and returns:
class Explanation(BaseModel):    matched_skills: list[str]    missing_skills: list[str]    reason: str   # 2 to 3 sentences
Prompt Gemini with the profile and the job text only, and instruct it to use nothing else.
Grounding check: every entry in matched_skills must appear in the profile, and every entry in missing_skills must be supported by the job text. Drop or flag entries that fail, and record how often this happens.
Frontend: a 'Why this match' expandable section on each result, loaded on demand so the list stays fast.
Acceptance: explanations load on click, contain no skills that are not in the resume or job text, and tests cover the grounding check with a mocked model.
Step 6: Mini evaluation (about 1.5 days)
This produces the numbers for the resume.
Create eval/profiles.jsonl with about 20 short test profiles (for example fresher backend, data analyst, ML engineer, frontend, DevOps, QA), written by hand and varied in wording, including some that use different vocabulary from the job postings.
For each profile, run all three modes (keyword, vector, hybrid) and pool the top 10 from each.
Label each pooled job 0 (not relevant), 1 (partly) or 2 (relevant) with an LLM judge using a fixed rubric stored in the repo, at temperature 0. Export about 30 percent of the labels to a CSV so the author can hand-check them and report agreement.
Metrics: precision@10 and NDCG@10 (using the graded labels) for each mode. Note in the README that recall is measured only over the pooled results.
python eval/run_eval.py writes raw results to eval/results/ and a markdown table to EVAL_RESULTS.md. No number is hardcoded.
Acceptance: one command reproduces the table comparing keyword, vector and hybrid.
Step 7: Deployment (about 1 day)
Hosted Postgres with pgvector (for example Neon or Supabase); run the schema and load_jobs.py against it.
Deploy the backend to Render, Railway or Fly.io from the GitHub repo, with secrets in the platform's env settings.
Deploy the frontend to Vercel or Netlify with the backend URL as an env var.
Add basic rate limiting on the explain and resume endpoints to protect the API key.
README: project summary, architecture diagram, setup steps, evaluation table, live link, and a clear note about the dataset.
Acceptance: the live link supports search, resume upload, matching and explanations.
7. Definition of done
☐ Search works in keyword, vector and hybrid modes
☐ Resume upload produces a validated profile
☐ Ranked matches with grounded explanations
☐ Evaluation table generated by a script
☐ Tests for RRF, schema validation and the grounding check
☐ Live deployed link and a README with an architecture diagram
☐ No secrets committed
8. Numbers to capture for the resume
Number of jobs indexed, precision@10 and NDCG@10 for each mode (and the improvement of hybrid over the baselines), average search latency, how often the grounding check removes an item, and any user or demo counts.
9. Things the agent must not do
Do not build anything listed as out of scope.
Do not continue past a step without confirmation.
Do not fabricate data, labels or metrics.
Do not store uploaded resumes or commit API keys.
10. Stretch goals (only after the MVP is done and deployed)
LLM reranking of the top 20
Save and dislike signals that adjust future rankings
Filters for location and experience level
Scheduled ingestion from a live job source
Docker images for the backend and frontend