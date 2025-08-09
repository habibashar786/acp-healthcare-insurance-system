"""
Corrected test_api.py - Fix the failing authentication test
"""

import pytest
from fastapi.testclient import TestClient
from main_system import app

client = TestClient(app)

def test_health_endpoint():
    """Test that health endpoint works without auth"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_root_endpoint():
    """Test that root endpoint works without auth"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_unauthenticated_query_fails():
    """Test that protected endpoints fail without authentication"""
    
    # Test /me endpoint (should require auth)
    response = client.get("/me")
    assert response.status_code == 401  # Unauthorized, not 403 or 404
    
    # Test /policies endpoint (should require auth)  
    response = client.get("/policies")
    assert response.status_code == 401  # Unauthorized
    
    # Test /claims endpoint (should require auth)
    response = client.get("/claims")
    assert response.status_code == 401  # Unauthorized
    
    # Test creating a policy without auth (should require auth)
    policy_data = {
        "plan_id": 1,
        "start_date": "2024-01-01T00:00:00",
        "payment_frequency": "monthly"
    }
    response = client.post("/policies", json=policy_data)
    assert response.status_code == 401  # Unauthorized

def test_admin_endpoints_require_admin():
    """Test that admin endpoints require admin role"""
    
    # Test admin endpoint without auth
    response = client.get("/admin/users")
    assert response.status_code == 401  # Should be unauthorized first
    
def test_documentation_accessible():
    """Test that API documentation is accessible"""
    
    # Test docs endpoint
    response = client.get("/api/docs")
    assert response.status_code == 200
    
    # Test redoc endpoint  
    response = client.get("/api/redoc")
    assert response.status_code == 200

if __name__ == "__main__":
    # Run individual tests
    test_health_endpoint()
    test_root_endpoint() 
    test_unauthenticated_query_fails()
    print("✅ All tests passed!")