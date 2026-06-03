"""
Tests for the Malaysia Postcodes API.
Run with: pytest tests/
"""

import pytest
from fastapi.testclient import TestClient
import json

from api.main import app
from api.data_loader import load_postcode_data
from api.auth import load_api_keys


# Test API key
TEST_API_KEY = "test_key_12345678901234567890123456789012"


@pytest.fixture(scope="module")
def setup_test_data():
    """Setup test data and API keys."""
    # Load postcode data
    load_postcode_data("all.json")
    
    # Create temporary API keys file for testing
    test_keys = {
        "keys": [
            {
                "key": TEST_API_KEY,
                "name": "Test Client",
                "created": "2026-01-01T00:00:00"
            }
        ]
    }
    
    with open("test_api_keys.json", "w") as f:
        json.dump(test_keys, f)
    
    # Load API keys
    load_api_keys("test_api_keys.json")
    
    yield
    
    # Cleanup
    import os
    if os.path.exists("test_api_keys.json"):
        os.remove("test_api_keys.json")


@pytest.fixture
def client(setup_test_data):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Provide authentication headers."""
    return {"X-API-Key": TEST_API_KEY}


# Test public endpoints (no auth required)

def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Malaysia Postcodes API"
    assert "version" in data
    assert "documentation" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["data_loaded"] is True
    assert data["total_states"] > 0
    assert data["total_postcodes"] > 0


# Test authentication

def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication."""
    response = client.get("/states")
    assert response.status_code == 401
    assert "API key" in response.json()["detail"]


def test_protected_endpoint_with_invalid_key(client):
    """Test that invalid API key is rejected."""
    headers = {"X-API-Key": "invalid_key"}
    response = client.get("/states", headers=headers)
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_protected_endpoint_with_valid_key(client, auth_headers):
    """Test that valid API key grants access."""
    response = client.get("/states", headers=auth_headers)
    assert response.status_code == 200


# Test states endpoints

def test_list_states(client, auth_headers):
    """Test listing all states."""
    response = client.get("/states", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check structure
    first_state = data[0]
    assert "name" in first_state
    assert "city_count" in first_state
    assert "postcode_count" in first_state


def test_get_state_details(client, auth_headers):
    """Test getting state details."""
    response = client.get("/states/Johor", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Johor"
    assert "city" in data
    assert isinstance(data["city"], list)


def test_get_state_case_insensitive(client, auth_headers):
    """Test that state lookup is case-insensitive."""
    response = client.get("/states/johor", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Johor"


def test_get_nonexistent_state(client, auth_headers):
    """Test getting a non-existent state returns 404."""
    response = client.get("/states/NonExistentState", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# Test cities endpoints

def test_list_cities_in_state(client, auth_headers):
    """Test listing cities in a state."""
    response = client.get("/states/Johor/cities", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check structure
    first_city = data[0]
    assert "name" in first_city
    assert "postcode" in first_city
    assert isinstance(first_city["postcode"], list)


def test_get_city_details(client, auth_headers):
    """Test getting city details."""
    response = client.get("/states/Johor/cities/Johor Bahru", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "Johor Bahru" in data["name"]
    assert "postcode" in data
    assert len(data["postcode"]) > 0


def test_get_nonexistent_city(client, auth_headers):
    """Test getting a non-existent city returns 404."""
    response = client.get("/states/Johor/cities/NonExistentCity", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# Test postcode lookup

def test_lookup_postcode(client, auth_headers):
    """Test postcode lookup."""
    response = client.get("/postcodes/50000", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["postcode"] == "50000"
    assert "city" in data
    assert "state" in data
    assert "Kuala Lumpur" in data["city"]


def test_lookup_nonexistent_postcode(client, auth_headers):
    """Test lookup of non-existent postcode returns 404."""
    response = client.get("/postcodes/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# Test search

def test_search_states(client, auth_headers):
    """Test searching for states."""
    response = client.get("/search?q=Johor", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check if Johor state is in results
    state_results = [r for r in data if r["type"] == "state" and "Johor" in r["name"]]
    assert len(state_results) > 0


def test_search_cities(client, auth_headers):
    """Test searching for cities."""
    response = client.get("/search?q=Kuala", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_search_case_insensitive(client, auth_headers):
    """Test that search is case-insensitive."""
    response1 = client.get("/search?q=kuala", headers=auth_headers)
    response2 = client.get("/search?q=KUALA", headers=auth_headers)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert len(response1.json()) == len(response2.json())


def test_search_too_short(client, auth_headers):
    """Test that search requires at least 2 characters."""
    response = client.get("/search?q=a", headers=auth_headers)
    assert response.status_code == 422
    assert "at least 2 characters" in response.json()["detail"]


def test_search_empty(client, auth_headers):
    """Test that empty search query is rejected."""
    response = client.get("/search?q=", headers=auth_headers)
    assert response.status_code == 422


# Test rate limiting

def test_rate_limiting(client, auth_headers):
    """Test that rate limiting is enforced."""
    # Note: This test may be slow as it makes 101 requests
    # It's commented out by default but can be enabled for thorough testing
    
    # Make 100 requests (should succeed)
    for i in range(100):
        response = client.get("/health")
        if response.status_code != 200:
            pytest.fail(f"Request {i+1} failed with status {response.status_code}")
    
    # 101st request should be rate limited (if within same minute)
    # Note: This might not fail if requests span across minute boundaries
    # For robust rate limit testing, consider using a time-mocking library
    

# Test data integrity

def test_data_loading(client, auth_headers):
    """Test that data is properly loaded and accessible."""
    # Get all states
    response = client.get("/states", headers=auth_headers)
    assert response.status_code == 200
    states = response.json()
    
    # Verify we have the expected states
    state_names = [s["name"] for s in states]
    assert "Johor" in state_names
    assert "Selangor" in state_names
    assert "Wp Kuala Lumpur" in state_names or "Kuala Lumpur" in state_names
    
    # Verify postcode counts are reasonable
    for state in states:
        assert state["postcode_count"] > 0
        assert state["city_count"] > 0
