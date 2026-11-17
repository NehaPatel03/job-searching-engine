import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import JobResult
from backend.app.search import vector_search

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["embed_dim"] == 768

def test_vector_search_direct():
    results = vector_search("Python backend developer", k=5)
    assert isinstance(results, list)
    assert len(results) == 5
    first = results[0]
    assert isinstance(first, JobResult)
    assert first.job_id > 0
    assert first.title
    assert 0.0 <= first.score <= 1.0
    assert len(first.snippet) > 0

def test_search_api_endpoint_success():
    response = client.get("/search?q=React+TypeScript+frontend&k=4")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 4
    
    first = data[0]
    assert "job_id" in first
    assert "title" in first
    assert "company" in first
    assert "location" in first
    assert "score" in first
    assert "snippet" in first
    assert first["score"] > 0.4

def test_search_api_semantic_relevance():
    # Semantic test: query about building REST APIs should match backend engineering
    response = client.get("/search?q=building+microservices+in+flask&k=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Check that returned titles relate to Backend, API, or Engineering
    titles_combined = " ".join([d["title"].lower() for d in data])
    assert any(keyword in titles_combined for keyword in ["backend", "api", "engineer", "developer", "fastapi"])

def test_search_api_empty_query_validation():
    # Empty query should fail validation
    response = client.get("/search?q=")
    assert response.status_code in [400, 422]
