"""
ACP Healthcare Insurance System - Comprehensive Test Suite
Testing Sequential Workflow Engine with Real Healthcare Data
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import your main application
try:
    from main_system import app
    from workflow_engine import WorkflowEngine
    from data_models import Patient, InsurancePlan, CPTCode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure your src directory has the main modules")

# Test client
client = TestClient(app)

# Test configuration
TEST_API_KEY = "demo-api-key-2024"
TEST_HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}

class TestACPSystemHealth:
    """Test basic system health and setup"""
    
    def test_health_endpoint(self):
        """Test system health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint with system info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "ACP Healthcare Insurance System" in str(data)
    
    def test_api_authentication(self):
        """Test API authentication requirement"""
        # Test without auth header
        response = client.post("/query", json={})
        assert response.status_code == 401
        
        # Test with invalid auth
        headers = {"Authorization": "Bearer invalid-key"}
        response = client.post("/query", headers=headers, json={})
        assert response.status_code == 401

class TestPatientDataIntegration:
    """Test Synthea patient data integration"""
    
    def test_patient_lookup(self):
        """Test patient data retrieval"""
        response = client.get("/patients", headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert len(data["patients"]) > 0
        
        # Check patient structure
        patient = data["patients"][0]
        assert "patient_id" in patient
        assert "demographics" in patient
        assert "insurance_plan" in patient
    
    def test_patient_anonymization(self):
        """Test HIPAA compliance - patient data anonymization"""
        response = client.get("/patients", headers=TEST_HEADERS)
        data = response.json()
        
        for patient in data["patients"]:
            # Ensure no real identifiers
            assert "ssn" not in patient
            assert "phone" not in patient
            assert "address" not in patient
            # Should have anonymized IDs
            assert patient["patient_id"].startswith("PT")

class TestCPTCodeIntegration:
    """Test CMS CPT code integration"""
    
    def test_service_catalog(self):
        """Test CPT code service catalog"""
        response = client.get("/services", headers=TEST_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert len(data["services"]) > 0
        
        # Check CPT code structure
        service = data["services"][0]
        assert "cpt_code" in service
        assert "description" in service
        assert "rvu_work" in service
        assert "medicare_rate" in service

class TestSequentialWorkflow:
    """Test 7-step sequential workflow engine"""
    
    def test_routine_primary_care_workflow(self):
        """Test routine primary care visit workflow"""
        query_data = {
            "patient_id": "PT000001",
            "cpt_codes": ["99213"],  # Office visit
            "facility_type": "outpatient",
            "urgency": "routine"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "workflow_id" in data
        assert "data" in data
        
        # Check workflow completion
        workflow_data = data["data"]
        assert "approval_status" in workflow_data
        assert "financial_summary" in workflow_data
        assert "processing_time_ms" in workflow_data
        
        # Should be auto-approved for routine care
        assert workflow_data["approval_status"] in ["auto_approved", "approved"]
    
    def test_high_cost_procedure_workflow(self):
        """Test high-cost procedure requiring prior auth"""
        query_data = {
            "patient_id": "PT000001",
            "cpt_codes": ["29881"],  # Arthroscopy knee
            "facility_type": "outpatient"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # High-cost procedures may require prior auth
        workflow_data = data["data"]
        assert "approval_status" in workflow_data
        # Status could be approved, pending, or requires_prior_auth
        assert workflow_data["approval_status"] in [
            "approved", "pending", "requires_prior_auth", "auto_approved"
        ]
    
    def test_multi_service_workflow(self):
        """Test workflow with multiple CPT codes"""
        query_data = {
            "patient_id": "PT000002",
            "cpt_codes": ["99213", "80053", "71020"],  # Visit + Lab + X-ray
            "facility_type": "outpatient"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Check financial calculation for multiple services
        financial = data["data"]["financial_summary"]
        assert "total_cost" in financial
        assert "insurance_pays" in financial
        assert "patient_pays" in financial
        assert financial["total_cost"] > 0

class TestWorkflowStatusTracking:
    """Test workflow status and tracking"""
    
    def test_workflow_creation_and_tracking(self):
        """Test workflow creation and status tracking"""
        # Create a workflow
        query_data = {
            "patient_id": "PT000001",
            "cpt_codes": ["99213"],
            "facility_type": "outpatient"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        assert response.status_code == 200
        
        workflow_id = response.json()["workflow_id"]
        
        # Check workflow status
        status_response = client.get(f"/workflow/{workflow_id}", headers=TEST_HEADERS)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "workflow_id" in status_data
        assert "status" in status_data
        assert "steps_completed" in status_data

class TestInsurancePlans:
    """Test insurance plan integration"""
    
    def test_different_insurance_plans(self):
        """Test processing with different insurance plans"""
        test_cases = [
            {"patient_id": "PT000001", "expected_plan": "BCBS Gold PPO"},
            {"patient_id": "PT000002", "expected_plan": "Aetna Silver HMO"},
            {"patient_id": "PT000003", "expected_plan": "Kaiser Bronze"}
        ]
        
        for case in test_cases:
            query_data = {
                "patient_id": case["patient_id"],
                "cpt_codes": ["99213"],
                "facility_type": "outpatient"
            }
            
            response = client.post("/query", headers=TEST_HEADERS, json=query_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True

class TestPerformanceMetrics:
    """Test system performance and analytics"""
    
    def test_analytics_endpoint(self):
        """Test system analytics endpoint"""
        response = client.get("/analytics", headers=TEST_HEADERS)
        assert response.status_code == 200
        
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "total_queries" in metrics
        assert "average_processing_time" in metrics
        assert "success_rate" in metrics
    
    def test_response_time_performance(self):
        """Test API response time performance"""
        import time
        
        query_data = {
            "patient_id": "PT000001",
            "cpt_codes": ["99213"],
            "facility_type": "outpatient"
        }
        
        start_time = time.time()
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # Should respond within 1 second for production readiness
        assert response_time_ms < 1000

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_patient_id(self):
        """Test handling of invalid patient ID"""
        query_data = {
            "patient_id": "INVALID_ID",
            "cpt_codes": ["99213"],
            "facility_type": "outpatient"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        # Should handle gracefully
        assert response.status_code in [200, 400, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is False
    
    def test_invalid_cpt_code(self):
        """Test handling of invalid CPT code"""
        query_data = {
            "patient_id": "PT000001",
            "cpt_codes": ["INVALID"],
            "facility_type": "outpatient"
        }
        
        response = client.post("/query", headers=TEST_HEADERS, json=query_data)
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            # Should handle invalid codes gracefully
            assert "success" in data

class TestDataValidation:
    """Test Pydantic data validation"""
    
    def test_request_validation(self):
        """Test request data validation"""
        # Missing required fields
        response = client.post("/query", headers=TEST_HEADERS, json={})
        assert response.status_code == 422  # Validation error
        
        # Invalid data types
        invalid_data = {
            "patient_id": 123,  # Should be string
            "cpt_codes": "99213",  # Should be list
        }
        response = client.post("/query", headers=TEST_HEADERS, json=invalid_data)
        assert response.status_code == 422

# Pytest configuration and fixtures
@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "patient_id": "PT000001",
        "demographics": {
            "age": 45,
            "gender": "F",
            "state": "MA"
        },
        "insurance_plan": "BCBS Gold PPO"
    }

@pytest.fixture
def sample_cpt_codes():
    """Sample CPT codes for testing"""
    return [
        {"cpt_code": "99213", "description": "Office visit", "rvu_work": 1.3},
        {"cpt_code": "80053", "description": "Comprehensive metabolic panel", "rvu_work": 0.17},
        {"cpt_code": "71020", "description": "Chest X-ray", "rvu_work": 0.22}
    ]

# Run specific test groups
if __name__ == "__main__":
    # Run health tests first
    print("Running ACP Healthcare System Tests...")
    pytest.main([
        __file__ + "::TestACPSystemHealth",
        "-v", "--tb=short"
    ])