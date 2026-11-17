import pytest
from pathlib import Path
from backend.app.config import settings, EMBED_DIM, BASE_DIR
from scripts.load_jobs import clean_and_normalize_jobs, prepare_embedding_text, find_column
from backend.app.embeddings import EmbeddingManager

def test_config_defaults():
    assert EMBED_DIM == 768
    assert settings.EMBED_DIM == 768
    assert settings.EMBED_MODEL == "gemini-embedding-001"
    assert settings.GEMINI_MODEL == "gemini-2.5-flash"

def test_column_alias_detection():
    headers = ["Job Title", "Company_Name", "job_description", "Skills", "City"]
    assert find_column(headers, "title") == "Job Title"
    assert find_column(headers, "company") == "Company_Name"
    assert find_column(headers, "description") == "job_description"
    assert find_column(headers, "skills") == "Skills"
    assert find_column(headers, "location") == "City"

def test_synthetic_jobs_dataset_cleaning():
    csv_path = BASE_DIR / "data" / "raw" / "jobs.csv"
    if not csv_path.exists():
        pytest.skip("jobs.csv not generated yet")
    
    jobs = clean_and_normalize_jobs(csv_path, max_records=100, min_records=10)
    assert len(jobs) > 0
    first = jobs[0]
    assert "title" in first and len(first["title"]) > 0
    assert "company" in first and len(first["company"]) > 0
    assert "description" in first and len(first["description"]) > 0
    
    # Test embedding text preparation
    emb_text = prepare_embedding_text(first)
    assert first["title"] in emb_text
    assert first["company"] in emb_text
    assert len(emb_text) > 20

def test_embedding_manager_caching(tmp_path):
    mgr = EmbeddingManager()
    h1 = mgr._hash_text("test text for embedding")
    h2 = mgr._hash_text("test text for embedding")
    h3 = mgr._hash_text("different text")
    assert h1 == h2
    assert h1 != h3

def test_schema_sql_exists():
    schema_path = BASE_DIR / "schema.sql"
    assert schema_path.exists()
    content = schema_path.read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in content
    assert "vector(768)" in content
    assert "jobs_embedding_idx" in content
    assert "jobs_tsv_idx" in content
