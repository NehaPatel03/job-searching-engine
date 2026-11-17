import os
import json
import time
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict

from google import genai
from google.genai import types
from google.genai import errors
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.config import settings, BASE_DIR, EMBED_DIM

logger = logging.getLogger(__name__)

CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_FILE = CACHE_DIR / "embeddings.json"

class EmbeddingManager:
    """Manages text embedding generation via Google Gemini API with local caching, rate-limit awareness, and retries."""

    def __init__(self):
        self.cache: Dict[str, List[float]] = {}
        self._load_cache()
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please set it in your .env file or environment."
                )
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _hash_text(self, text: str) -> str:
        """Computes a SHA-256 hash of the input text for fast cache lookup."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def _load_cache(self) -> None:
        """Loads cached embeddings from disk if the cache file exists."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached embeddings from {CACHE_FILE}")
            except Exception as e:
                logger.warning(f"Could not load embedding cache ({e}); starting with empty cache.")
                self.cache = {}

    def _save_cache(self) -> None:
        """Persists the in-memory embedding cache to disk."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.error(f"Failed to save embedding cache to {CACHE_FILE}: {e}")

    def _call_api_with_backoff(self, texts: List[str], max_retries: int = 8) -> List[List[float]]:
        """
        Calls Gemini embed_content API with adaptive rate-limit backoff.
        Automatically handles Free Tier 100 requests/minute quota limit.
        """
        config = types.EmbedContentConfig(output_dimensionality=EMBED_DIM)
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.embed_content(
                    model=settings.EMBED_MODEL,
                    contents=texts,
                    config=config,
                )
                return [item.values for item in response.embeddings]
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    # Extract suggested retry delay from error if present
                    delay = 60  # Default to 60s for per-minute quota resets
                    match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str)
                    if match:
                        delay = int(float(match.group(1))) + 3
                    logger.warning(
                        f"Free Tier rate limit (429) hit on attempt {attempt}/{max_retries}. "
                        f"Waiting {delay} seconds for quota reset..."
                    )
                    time.sleep(delay)
                else:
                    if attempt == max_retries:
                        logger.error(f"Failed to embed batch after {max_retries} attempts: {e}")
                        raise
                    wait_time = min(2 ** attempt, 30)
                    logger.warning(f"API error ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        raise RuntimeError(f"Failed to generate embeddings after {max_retries} retries.")

    def embed_texts(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """
        Embeds a list of texts using Gemini API with batching, retries, and disk cache.
        Returns a list of embedding vectors matching the input order.
        """
        if not texts:
            return []

        results: List[List[float] | None] = [None] * len(texts)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        # 1. Check local cache
        for idx, text in enumerate(texts):
            h = self._hash_text(text)
            if h in self.cache:
                results[idx] = self.cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(text)

        cached_count = len(texts) - len(missing_texts)
        if cached_count > 0:
            logger.info(f"Reusing {cached_count} pre-cached embeddings from disk.")

        # 2. Fetch missing embeddings in batches
        if missing_texts:
            logger.info(
                f"Embedding {len(missing_texts)} uncached items (out of {len(texts)} total) "
                f"in batches of {batch_size}..."
            )
            for i in range(0, len(missing_texts), batch_size):
                batch_texts = missing_texts[i : i + batch_size]
                batch_indices = missing_indices[i : i + batch_size]
                
                try:
                    embeddings = self._call_api_with_backoff(batch_texts)
                    for text, orig_idx, emb in zip(batch_texts, batch_indices, embeddings):
                        h = self._hash_text(text)
                        self.cache[h] = emb
                        results[orig_idx] = emb
                    
                    # Save immediately after each successful batch
                    self._save_cache()
                    done = cached_count + i + len(batch_texts)
                    logger.info(f"Embedded batch ({len(batch_texts)} items). Total progress: {done}/{len(texts)} cached.")
                    
                    # Brief pause between batches
                    time.sleep(1.0)
                except Exception as e:
                    # Save whatever progress we have so far
                    self._save_cache()
                    logger.error(f"Failed to embed batch starting at index {i}: {e}")
                    raise

        # Guarantee no None values
        for idx, val in enumerate(results):
            if val is None:
                raise RuntimeError(f"Embedding generation failed for item at index {idx}")

        return results  # type: ignore

    def embed_text(self, text: str) -> List[float]:
        """Convenience method to embed a single string."""
        return self.embed_texts([text])[0]

# Global singleton
embedding_manager = EmbeddingManager()

def get_embedding(text: str) -> List[float]:
    """Generates a single 768-dim embedding vector."""
    return embedding_manager.embed_text(text)

def get_embeddings_batch(texts: List[str], batch_size: int = 50) -> List[List[float]]:
    """Generates 768-dim embedding vectors for a list of strings."""
    return embedding_manager.embed_texts(texts, batch_size=batch_size)
