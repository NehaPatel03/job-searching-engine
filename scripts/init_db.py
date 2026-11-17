import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings, EMBED_DIM
from backend.app.db import apply_schema, get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")

def main():
    logger.info("Initializing database schema...")
    try:
        apply_schema()
        
        # Verify database setup
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check vector extension
                cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
                row = cur.fetchone()
                if not row:
                    logger.error("pgvector extension was not created.")
                    sys.exit(1)
                logger.info(f"Confirmed: pgvector extension active (version: {row[0]}).")

                # Check jobs table
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'jobs';
                """)
                columns = cur.fetchall()
                column_names = [c[0] for c in columns]
                logger.info(f"Confirmed: 'jobs' table exists with columns: {', '.join(column_names)}")
                
                # Check row count
                cur.execute("SELECT COUNT(*) FROM jobs;")
                count = cur.fetchone()[0]
                logger.info(f"Current jobs count in database: {count}")

        logger.info(f"SUCCESS: Database initialized. Configured EMBED_DIM: {EMBED_DIM}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
