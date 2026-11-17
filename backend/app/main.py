import logging
from typing import List
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings, EMBED_DIM
from backend.app.schemas import JobResult
from backend.app.search import vector_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

app = FastAPI(
    title="Semantic Job Matching Engine API",
    version="1.0.0",
    description="Hybrid semantic job search and resume matching engine using PostgreSQL, pgvector, and Google Gemini."
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint to verify backend status and configuration."""
    return {
        "status": "healthy",
        "embed_model": settings.EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "gemini_model": settings.GEMINI_MODEL,
    }

@app.get(
    "/search",
    response_model=List[JobResult],
    summary="Semantic Vector Job Search",
    description="Performs semantic cosine similarity search across job postings using pgvector."
)
def search_jobs(
    q: str = Query(..., min_length=1, description="Natural-language search query"),
    k: int = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """
    Search jobs semantically based on a natural-language query.
    Generates a 768-dim query embedding using Gemini and retrieves top-k closest jobs.
    """
    cleaned_query = q.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty or whitespace only."
        )

    try:
        results = vector_search(query_text=cleaned_query, k=k)
        return results
    except Exception as e:
        logger.error(f"Search failed for query '{cleaned_query}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while performing search: {str(e)}"
        )
