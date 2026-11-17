import logging
from typing import List, Optional
import psycopg
from pgvector.psycopg import register_vector

from backend.app.config import settings
from backend.app.db import get_db_connection
from backend.app.schemas import JobResult
from backend.app.embeddings import get_embedding

logger = logging.getLogger(__name__)

def vector_search(query_text: str, k: int = 10) -> List[JobResult]:
    """
    Executes semantic vector search in PostgreSQL using pgvector cosine similarity.
    1. Embeds the natural-language query with Gemini.
    2. Finds top-K jobs ordered by cosine distance (embedding <=> query_vec).
    3. Computes cosine similarity score = 1 - cosine_distance.
    """
    if not query_text or not query_text.strip():
        return []

    # 1. Embed query text into 768-dim vector
    query_vector = get_embedding(query_text.strip())

    # 2. Query Postgres
    results: List[JobResult] = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT 
                    id, 
                    title, 
                    company, 
                    location, 
                    ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS score,
                    LEFT(description, 250) AS snippet
                FROM jobs
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector ASC
                LIMIT %s;
            """
            cur.execute(sql, (query_vector, query_vector, k))
            rows = cur.fetchall()

            for row in rows:
                job_id, title, company, location, score, snippet = row
                results.append(
                    JobResult(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=location,
                        score=float(score),
                        snippet=snippet.strip() + ("..." if len(snippet) >= 250 else "")
                    )
                )

    return results
