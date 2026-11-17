-- Enable the pgvector extension for dense vector storage and similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Jobs table storing job postings, metadata, full-text tsvector, and 768-dim vector embeddings
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    experience_level TEXT,
    skills TEXT,
    description TEXT NOT NULL,
    embedding vector(768),
    tsv tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(skills, '') || ' ' || coalesce(description, ''))
    ) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW index for fast approximate nearest neighbor (ANN) cosine distance queries
CREATE INDEX IF NOT EXISTS jobs_embedding_idx ON jobs USING hnsw (embedding vector_cosine_ops);

-- GIN index for fast full-text keyword search
CREATE INDEX IF NOT EXISTS jobs_tsv_idx ON jobs USING gin (tsv);
