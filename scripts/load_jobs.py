import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tqdm import tqdm
import psycopg

from backend.app.config import settings, BASE_DIR, EMBED_DIM
from backend.app.db import get_db_connection
from backend.app.embeddings import get_embeddings_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_jobs")

RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "jobs.csv"

# Potential column name aliases for flexible CSV ingestion
COLUMN_ALIASES = {
    "title": ["title", "job_title", "jobtitle", "role", "position"],
    "company": ["company", "company_name", "companyname", "employer", "organization"],
    "location": ["location", "job_location", "city", "state", "workplace_type"],
    "experience_level": ["experience_level", "experience", "seniority", "level", "formatted_experience_level"],
    "skills": ["skills", "skills_desc", "job_skills", "tech_stack", "tags", "keywords"],
    "description": ["description", "job_description", "jobdescription", "details", "summary", "text"],
}

def normalize_header(name: str) -> str:
    """Normalizes header string by lowercasing and replacing spaces/dashes with underscores."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def find_column(headers: List[str], target: str) -> Optional[str]:
    """Finds matching column name among headers based on alias mappings."""
    norm_headers = {normalize_header(h): h for h in headers}
    for alias in COLUMN_ALIASES[target]:
        norm_alias = normalize_header(alias)
        if norm_alias in norm_headers:
            return norm_headers[norm_alias]
    return None

def clean_and_normalize_jobs(csv_path: Path, max_records: int = 2000, min_records: int = 500) -> List[Dict[str, Any]]:
    """Reads CSV, maps columns, drops empty descriptions, deduplicates, and limits record count."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. Please place your CSV at data/raw/jobs.csv "
            f"or run 'python scripts/make_synthetic_jobs.py' to generate synthetic data."
        )

    cleaned_jobs: List[Dict[str, Any]] = []
    seen_keys = set()
    skipped_empty_desc = 0
    skipped_duplicate = 0

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        
        # Map required and optional columns
        title_col = find_column(headers, "title")
        company_col = find_column(headers, "company")
        desc_col = find_column(headers, "description")
        loc_col = find_column(headers, "location")
        exp_col = find_column(headers, "experience_level")
        skills_col = find_column(headers, "skills")

        if not title_col or not desc_col:
            raise ValueError(
                f"CSV must contain at least a title and description column. Found headers: {headers}"
            )

        logger.info(
            f"Detected column mapping: title='{title_col}', company='{company_col}', "
            f"description='{desc_col}', location='{loc_col}', skills='{skills_col}'"
        )

        for row in reader:
            title = (row.get(title_col) or "").strip()
            desc = (row.get(desc_col) or "").strip()
            company = (row.get(company_col) or "").strip() if company_col else "Unknown"
            location = (row.get(loc_col) or "").strip() if loc_col else "Remote"
            exp = (row.get(exp_col) or "").strip() if exp_col else "Not Specified"
            skills = (row.get(skills_col) or "").strip() if skills_col else ""

            # Rule: Drop rows with empty descriptions or titles
            if not desc or not title:
                skipped_empty_desc += 1
                continue

            # Rule: Deduplicate on (title + company)
            dedup_key = (title.lower(), company.lower())
            if dedup_key in seen_keys:
                skipped_duplicate += 1
                continue
            seen_keys.add(dedup_key)

            cleaned_jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "experience_level": exp,
                "skills": skills,
                "description": desc,
            })

            if len(cleaned_jobs) >= max_records:
                break

    logger.info(
        f"Read and cleaned {len(cleaned_jobs)} jobs. "
        f"Skipped {skipped_empty_desc} with empty description/title, {skipped_duplicate} duplicates."
    )

    if len(cleaned_jobs) < min_records:
        logger.warning(
            f"Cleaned job count ({len(cleaned_jobs)}) is less than recommended minimum ({min_records})."
        )

    return cleaned_jobs

def prepare_embedding_text(job: Dict[str, Any]) -> str:
    """
    Constructs the text to embed for each job per SPEC.md:
    title, company, skills, and the first ~1,500 characters of the description.
    """
    title = job["title"]
    company = job["company"]
    skills = job["skills"]
    desc_snippet = job["description"][:1500]
    return f"{title} at {company}. Skills: {skills}. Description: {desc_snippet}"

def insert_jobs_into_db(jobs: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
    """Inserts cleaned jobs and their 768-dim embeddings into PostgreSQL."""
    if len(jobs) != len(embeddings):
        raise ValueError("Mismatch between number of jobs and generated embeddings.")

    inserted_count = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            insert_query = """
                INSERT INTO jobs (title, company, location, experience_level, skills, description, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            for job, emb in zip(jobs, embeddings):
                cur.execute(
                    insert_query,
                    (
                        job["title"],
                        job["company"],
                        job["location"],
                        job["experience_level"],
                        job["skills"],
                        job["description"],
                        emb,
                    )
                )
                inserted_count += 1
        conn.commit()

    return inserted_count

def main():
    logger.info(f"Loading jobs from {RAW_DATA_PATH}...")
    
    # 1. Clean and normalize records (targeting exactly 500 jobs for initial MVP index)
    jobs = clean_and_normalize_jobs(RAW_DATA_PATH, max_records=500, min_records=500)
    logger.info(f"Preparing embeddings for {len(jobs)} jobs...")

    # 2. Build text representation for embedding
    embedding_texts = [prepare_embedding_text(job) for job in jobs]

    # 3. Generate embeddings with batching, retries, and disk caching
    logger.info("Generating embeddings via Google Gemini API...")
    embeddings = get_embeddings_batch(embedding_texts, batch_size=25)
    
    # Validate embedding dimensions
    for idx, emb in enumerate(embeddings):
        if len(emb) != EMBED_DIM:
            raise ValueError(
                f"Embedding at index {idx} has dimension {len(emb)}, expected {EMBED_DIM}."
            )

    logger.info(f"Successfully generated {len(embeddings)} embeddings of dimension {EMBED_DIM}.")

    # 4. Insert into database
    logger.info("Inserting jobs and embeddings into PostgreSQL...")
    inserted = insert_jobs_into_db(jobs, embeddings)
    logger.info(f"SUCCESS: Inserted {inserted} jobs with pgvector embeddings into database.")

    # 5. Quick verification query
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(embedding) as embedded_jobs,
                    COUNT(tsv) as fts_jobs
                FROM jobs;
            """)
            stats = cur.fetchone()
            logger.info(f"Database Verification -> Total: {stats[0]}, With Vector: {stats[1]}, With FTS: {stats[2]}")

if __name__ == "__main__":
    main()
