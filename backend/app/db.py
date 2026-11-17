import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse
import psycopg
from pgvector.psycopg import register_vector

from backend.app.config import settings, BASE_DIR

logger = logging.getLogger(__name__)

def _resolve_host_ip(host: str) -> str | None:
    """Attempts to resolve host using public DNS servers (8.8.8.8, 1.1.1.1) if local DNS fails."""
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        answers = resolver.resolve(host, 'A')
        return str(answers[0])
    except Exception as e:
        logger.debug(f"Public DNS resolution error for {host}: {e}")
        return None

def get_connection_kwargs() -> dict:
    """Extracts connection parameters and provides fallback hostaddr if local DNS resolution fails."""
    kwargs = {}
    try:
        parsed = urlparse(settings.DATABASE_URL)
        host = parsed.hostname
        if host:
            import socket
            try:
                socket.getaddrinfo(host, parsed.port or 5432)
            except socket.gaierror:
                ip = _resolve_host_ip(host)
                if ip:
                    logger.info(f"Local DNS failed for {host}; resolved hostaddr {ip} via fallback DNS.")
                    kwargs["hostaddr"] = ip
    except Exception as e:
        logger.debug(f"DNS check skipped: {e}")
    return kwargs

def get_db_connection(autocommit: bool = False, register_pgvector: bool = True) -> psycopg.Connection:
    """Creates and returns a psycopg connection with pgvector registered."""
    extra_kwargs = get_connection_kwargs()
    conn = psycopg.connect(settings.DATABASE_URL, autocommit=autocommit, **extra_kwargs)
    if register_pgvector:
        register_vector(conn)
    return conn

@contextmanager
def get_db_cursor() -> Generator[psycopg.Cursor, None, None]:
    """Context manager for obtaining a database cursor with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()

def apply_schema(schema_file_path: Path | None = None) -> None:
    """Reads schema.sql and applies table and index definitions to PostgreSQL."""
    if schema_file_path is None:
        schema_file_path = BASE_DIR / "schema.sql"

    if not schema_file_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_file_path}")

    sql_content = schema_file_path.read_text(encoding="utf-8")
    masked_url = settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL
    logger.info(f"Applying schema from {schema_file_path} to {masked_url}...")

    with get_db_connection(autocommit=True, register_pgvector=False) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_content)

    logger.info("Database schema applied successfully with pgvector and indexes.")
