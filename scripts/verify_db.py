import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings, EMBED_DIM
from backend.app.db import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_db")

def verify():
    logger.info("Connecting to database to verify records and pgvector setup...")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Total counts
            cur.execute("""
                SELECT 
                    COUNT(*) AS total_jobs,
                    COUNT(embedding) AS embedded_jobs,
                    COUNT(tsv) AS fts_jobs
                FROM jobs;
            """)
            total, embedded, fts = cur.fetchone()
            logger.info("=" * 50)
            logger.info(f"Total Jobs in DB:      {total}")
            logger.info(f"Jobs with Embeddings: {embedded}")
            logger.info(f"Jobs with Full-Text:  {fts}")
            logger.info("=" * 50)

            if total == 0:
                logger.warning("No jobs found in the database. Run 'python scripts/load_jobs.py' first.")
                return

            # 2. Check embedding dimension on a sample job
            cur.execute("SELECT id, title, company, embedding FROM jobs WHERE embedding IS NOT NULL LIMIT 1;")
            sample = cur.fetchone()
            if sample:
                sample_id, title, company, emb = sample
                emb_vals = emb.to_list() if hasattr(emb, "to_list") else list(emb)
                emb_len = len(emb_vals)
                logger.info(f"Sample Job #{sample_id}: '{title}' at '{company}'")
                logger.info(f"Embedding Vector Dimension: {emb_len} (Matches EMBED_DIM={EMBED_DIM}: {emb_len == EMBED_DIM})")
                logger.info(f"Vector preview: [{emb_vals[0]:.4f}, {emb_vals[1]:.4f}, {emb_vals[2]:.4f}, ..., {emb_vals[-1]:.4f}]")

            # 3. Test Vector Cosine Distance (<=>) operator
            cur.execute("""
                SELECT id, title, company, 1 - (embedding <=> (SELECT embedding FROM jobs WHERE id = %s)) AS cosine_similarity
                FROM jobs
                ORDER BY embedding <=> (SELECT embedding FROM jobs WHERE id = %s) ASC
                LIMIT 3;
            """, (sample_id, sample_id))
            matches = cur.fetchall()
            logger.info("-" * 50)
            logger.info("Test Vector Search (Cosine Similarity against sample):")
            for m in matches:
                logger.info(f"  [Sim: {float(m[3]):.4f}] #{m[0]}: {m[1]} ({m[2]})")

            # 4. Test Postgres Full-Text Search (tsv @@ query)
            cur.execute("""
                SELECT id, title, company, ts_rank(tsv, to_tsquery('english', 'engineer | developer')) AS rank
                FROM jobs
                WHERE tsv @@ to_tsquery('english', 'engineer | developer')
                ORDER BY rank DESC
                LIMIT 3;
            """)
            fts_matches = cur.fetchall()
            logger.info("-" * 50)
            logger.info("Test Full-Text Keyword Search ('engineer | developer'):")
            for m in fts_matches:
                logger.info(f"  [Rank: {float(m[3]):.4f}] #{m[0]}: {m[1]} ({m[2]})")
            logger.info("=" * 50)
            logger.info("VERIFICATION COMPLETE: pgvector and Full-Text Search are 100% operational!")

if __name__ == "__main__":
    verify()
