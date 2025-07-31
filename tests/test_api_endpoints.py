"""
Comprehensive test suite for API endpoints with clinical scenarios.

Tests all API endpoints with realistic healthcare data and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import uuid
from datetime import datetime

from src.api.main import app
from src.api.core.config import get_settings

# Test client for API testing
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""
    
    def test_health_check_success(self):
        """Test successful health check."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "fhir_version" in data
        assert "components" in data
        assert "performance_metrics" in data
        assert "safety_checks" in data
        
        # Verify FHIR version
        assert data["fhir_version"] == "R4"
        assert data["version"] == "1.0.0"
    
    def test_readiness_probe(self):
        """Test Kubernetes readiness probe."""
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    def test_liveness_probe(self):
        """Test Kubernetes liveness probe."""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_check" in data
    
    @patch('src.api.endpoints.health._check_core_components')
    def test_health_check_with_unhealthy_components(self, mock_components):
        """Test health check with unhealthy components."""
        mock_components.return_value = {
            "hybrid_processor": "unhealthy",
            "fhir_parser": "healthy"
        }
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["components"]["hybrid_processor"] == "unhealthy"


class TestSummarizeEndpoints:
    """Test clinical summarization endpoints."""
    
    @pytest.fixture
    def valid_medication_bundle(self):
        """Fixture providing a valid FHIR Bundle with MedicationRequest."""
        return {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "text": "Lisinopril 10mg tablets",
                            "coding": [
                                {
                                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                    "code": "314076",
                                    "display": "Lisinopril 10 MG Oral Tablet"
                                }
                            ]
                        },
                        "subject": {
                            "reference": "Patient/patient-001"
                        },
                        "dosageInstruction": [
                            {
                                "text": "Take 1 tablet by mouth once daily",
                                "patientInstruction": "Take once daily in the morning",
                                "timing": {
                                    "repeat": {
                                        "frequency": 1,
                                        "period": 1,
                                        "periodUnit": "d"
                                    }
                                },
                                "route": {
                                    "text": "Oral"
                                },
                                "doseAndRate": [
                                    {
                                        "doseQuantity": {
                                            "value": 10,
                                            "unit": "mg"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                },
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-001",
                        "name": [
                            {
                                "family": "Test",
                                "given": ["Patient"]
                            }
                        ]
                    }
                }
            ]
        }
    
    def test_summarize_valid_bundle(self, valid_medication_bundle):
        """Test successful summarization of valid bundle."""
        request_data = {
            "bundle": valid_medication_bundle,
            "processing_options": {},
            "patient_preferences": {}
        }
        
        response = client.post("/api/v1/summarize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "summary" in data
        assert "processing_metadata" in data
        assert "fhir_metadata" in data
        
        # Verify summary content
        summary = data["summary"]
        assert "summary_id" in summary
        assert "patient_id" in summary
        assert "medications" in summary
        assert "disclaimers" in summary
        
        # Verify medication preservation
        medications = summary["medications"]
        assert len(medications) > 0
        
        med = medications[0]
        assert "Lisinopril" in med["medication_name"]
        assert med["dosage"] == "10 mg"
        assert med["frequency"] == "1 time(s) per 1 d"
        assert med["route"] == "Oral"
        
        # Verify safety metadata
        assert med["metadata"]["ai_processed"] == False
        assert med["metadata"]["safety_level"] == "critical"
        
        # Verify processing metadata
        proc_metadata = data["processing_metadata"]
        assert "processing_time_seconds" in proc_metadata
        assert "safety_guarantees" in proc_metadata
        assert proc_metadata["safety_guarantees"]["critical_data_preserved"] == True
    
    def test_summarize_empty_bundle(self):
        """Test summarization with empty bundle."""
        request_data = {
            "bundle": {
                "resourceType": "Bundle",
                "type": "document",
                "entry": []
            }
        }
        
        response = client.post("/api/v1/summarize", json=request_data)
        
        assert response.status_code == 400
        # Should return FHIR OperationOutcome
        data = response.json()
        assert "resourceType" in data
        assert data["resourceType"] == "OperationOutcome"
    
    def test_summarize_invalid_bundle_type(self):
        """Test summarization with invalid bundle."""
        request_data = {
            "bundle": {
                "resourceType": "Patient",  # Wrong resource type
                "id": "test"
            }
        }
        
        response = client.post("/api/v1/summarize", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_summarize_no_processable_resources(self, valid_medication_bundle):
        """Test summarization with no processable resources."""
        # Remove MedicationRequest, keep only Patient
        bundle_no_meds = valid_medication_bundle.copy()
        bundle_no_meds["entry"] = [
            entry for entry in bundle_no_meds["entry"]
            if entry["resource"]["resourceType"] != "MedicationRequest"
        ]
        
        request_data = {
            "bundle": bundle_no_meds
        }
        
        response = client.post("/api/v1/summarize", json=request_data)
        
        assert response.status_code == 422
    
    def test_validate_bundle_only(self, valid_medication_bundle):
        """Test bundle validation without processing."""
        request_data = {
            "bundle": valid_medication_bundle
        }
        
        response = client.post("/api/v1/summarize/validate-only", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "bundle_valid" in data
        assert "entries_processed" in data
        assert "medication_requests_found" in data
        assert "processable" in data
        
        assert data["bundle_valid"] == True
        assert data["medication_requests_found"] > 0
        assert data["processable"] == True
    
    def test_processing_time_monitoring(self, valid_medication_bundle):
        """Test that processing time is monitored and reported."""
        request_data = {
            "bundle": valid_medication_bundle
        }
        
        response = client.post("/api/v1/summarize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check processing time metrics
        proc_metadata = data["processing_metadata"]
        assert "processing_time_seconds" in proc_metadata
        assert "performance_metrics" in proc_metadata
        
        perf_metrics = proc_metadata["performance_metrics"]
        assert "processing_time_ms" in perf_metrics
        assert "meets_5_second_requirement" in perf_metrics
        
        # Should meet 5-second requirement for test data
        assert perf_metrics["meets_5_second_requirement"] == True


class TestValidationEndpoints:
    """Test FHIR validation endpoints."""
    
    @pytest.fixture
    def valid_medication_request(self):
        """Fixture providing a valid MedicationRequest."""
        return {
            "resourceType": "MedicationRequest",
            "id": "med-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": "Aspirin 81mg tablets",
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "1191",
                        "display": "Aspirin"
                    }
                ]
            },
            "subject": {
                "reference": "Patient/patient-001"
            },
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily",
                    "timing": {
                        "repeat": {
                            "frequency": 1,
                            "period": 1,
                            "periodUnit": "d"
                        }
                    },
                    "route": {
                        "text": "Oral"
                    },
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": 81,
                                "unit": "mg"
                            }
                        }
                    ]
                }
            ]
        }
    
    def test_validate_medication_request_success(self, valid_medication_request):
        """Test successful validation of MedicationRequest."""
        request_data = {
            "resource": valid_medication_request,
            "validation_mode": "strict"
        }
        
        response = client.post("/api/v1/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "issues" in data
        assert "resource_type" in data
        assert "validation_metadata" in data
        
        assert data["is_valid"] == True
        assert data["resource_type"] == "MedicationRequest"
    
    def test_validate_medication_request_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_request = {
            "resourceType": "MedicationRequest",
            "id": "med-001"
            # Missing status, intent, medication, subject
        }
        
        request_data = {
            "resource": invalid_request,
            "validation_mode": "strict"
        }
        
        response = client.post("/api/v1/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] == False
        assert len(data["issues"]) > 0
        
        # Should have error-level issues
        error_issues = [issue for issue in data["issues"] if issue["severity"] == "error"]
        assert len(error_issues) > 0
    
    def test_validate_unsupported_resource_type(self):
        """Test validation of unsupported resource type."""
        unsupported_resource = {
            "resourceType": "Observation",
            "id": "obs-001",
            "status": "final",
            "code": {
                "text": "Heart Rate"
            }
        }
        
        request_data = {
            "resource": unsupported_resource,
            "validation_mode": "strict"
        }
        
        response = client.post("/api/v1/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have warning about limited support
        assert data["resource_type"] == "Observation"
        warning_issues = [issue for issue in data["issues"] if issue["severity"] == "warning"]
        assert len(warning_issues) > 0
    
    def test_validate_bundle_endpoint(self, valid_medication_request):
        """Test bundle-specific validation endpoint."""
        bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {
                    "resource": valid_medication_request
                }
            ]
        }
        
        response = client.post("/api/v1/validate/bundle", json=bundle)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["resource_type"] == "Bundle"
        assert "is_valid" in data
    
    def test_validate_medication_request_specific_endpoint(self, valid_medication_request):
        """Test medication-specific validation endpoint."""
        response = client.post("/api/v1/validate/medication-request", json=valid_medication_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["resource_type"] == "MedicationRequest"
        assert "is_valid" in data


class TestSummaryEndpoints:
    """Test summary retrieval and management endpoints."""
    
    def test_get_nonexistent_summary(self):
        """Test retrieving non-existent summary."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/summary/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_summary_invalid_id_format(self):
        """Test retrieving summary with invalid ID format."""
        response = client.get("/api/v1/summary/invalid-id")
        
        assert response.status_code == 400
    
    def test_store_and_retrieve_summary(self):
        """Test storing and retrieving a summary."""
        summary_id = str(uuid.uuid4())
        
        # Sample summary data
        summary_data = {
            "summary_id": summary_id,
            "patient_id": "test-patient-001",
            "generated_at": datetime.utcnow().isoformat(),
            "medications": [],
            "lab_results": [],
            "appointments": [],
            "disclaimers": [
                "This is a test summary for educational purposes only."
            ],
            "processing_metadata": {
                "processed_at": datetime.utcnow().isoformat(),
                "processing_version": "1.0.0"
            }
        }
        
        # Store the summary
        store_response = client.post(f"/api/v1/summary/{summary_id}/store", json=summary_data)
        
        assert store_response.status_code == 200
        store_data = store_response.json()
        assert store_data["stored"] == True
        assert store_data["summary_id"] == summary_id
        
        # Retrieve the summary
        get_response = client.get(f"/api/v1/summary/{summary_id}")
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        
        assert "summary" in get_data
        assert get_data["summary"]["summary_id"] == summary_id
        assert get_data["summary"]["patient_id"] == "test-patient-001"
    
    def test_list_summaries(self):
        """Test listing stored summaries."""
        response = client.get("/api/v1/summaries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summaries" in data
        assert "pagination" in data
        assert isinstance(data["summaries"], list)
    
    def test_list_summaries_with_pagination(self):
        """Test listing summaries with pagination parameters."""
        response = client.get("/api/v1/summaries?limit=5&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        pagination = data["pagination"]
        assert pagination["limit"] == 5
        assert pagination["offset"] == 0
    
    def test_get_summary_metadata(self):
        """Test retrieving summary metadata."""
        # Use any UUID for testing
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/summary/{fake_id}/metadata")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary_id" in data
        assert "exists" in data
        assert data["exists"] == False  # Since it doesn't exist
    
    def test_delete_summary(self):
        """Test deleting a summary."""
        summary_id = str(uuid.uuid4())
        
        # First store a summary
        summary_data = {
            "summary_id": summary_id,
            "patient_id": "test-patient-002",
            "disclaimers": ["Test disclaimer"]
        }
        
        store_response = client.post(f"/api/v1/summary/{summary_id}/store", json=summary_data)
        assert store_response.status_code == 200
        
        # Then delete it
        delete_response = client.delete(f"/api/v1/summary/{summary_id}")
        
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["deleted"] == True
        
        # Verify it's gone
        get_response = client.get(f"/api/v1/summary/{summary_id}")
        assert get_response.status_code == 404


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are added."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        # Check for rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Window" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.skip(reason="Rate limiting test requires multiple requests")
    def test_rate_limit_exceeded(self):
        """Test rate limiting when limit is exceeded."""
        # This test would require making many requests quickly
        # Skipped for normal test runs to avoid impacting other tests
        pass


class TestSecurityFeatures:
    """Test security and PHI protection features."""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        # Check for security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "X-Healthcare-API",
            "X-FHIR-Version",
            "X-PHI-Protected"
        ]
        
        for header in expected_headers:
            assert header in response.headers
    
    def test_large_request_rejected(self):
        """Test that oversized requests are rejected."""
        # Create a very large request payload
        large_bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": []
        }
        
        # Add many entries to make it large
        for i in range(1000):
            large_bundle["entry"].append({
                "resource": {
                    "resourceType": "Patient",
                    "id": f"patient-{i}",
                    "name": [{"family": f"TestPatient{i}" * 100}]  # Make names long
                }
            })
        
        request_data = {"bundle": large_bundle}
        
        # This should be rejected due to size
        response = client.post("/api/v1/summarize", json=request_data)
        
        # Should either be rejected by middleware or by validation
        assert response.status_code in [413, 422, 400]


class TestErrorHandling:
    """Test error handling and FHIR compliance."""
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/summarize",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test handling of missing content type."""
        response = client.post("/api/v1/summarize", content='{"test": "data"}')
        
        assert response.status_code == 415
        # Should return FHIR OperationOutcome
        data = response.json()
        assert "resourceType" in data
        assert data["resourceType"] == "OperationOutcome"
    
    def test_method_not_allowed(self):
        """Test handling of unsupported HTTP methods."""
        response = client.put("/api/v1/health")
        
        assert response.status_code == 405
    
    def test_not_found_endpoint(self):
        """Test handling of non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404


class TestRootEndpoint:
    """Test the root API endpoint."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "fhir_version" in data
        assert "safety_features" in data
        assert "disclaimers" in data
        
        assert data["service"] == "Clinical Notes Summarizer API"
        assert data["version"] == "1.0.0"
        assert data["fhir_version"] == "R4"
        
        # Verify safety features are listed
        safety_features = data["safety_features"]
        assert "Zero PHI storage" in safety_features
        assert "Critical data preservation" in safety_features
        assert "FHIR R4 compliance" in safety_features
        
        # Verify disclaimers are present
        disclaimers = data["disclaimers"]
        assert len(disclaimers) > 0
        assert any("Educational purposes only" in disclaimer for disclaimer in disclaimers)