"""
Test suite for FHIR models and validation.

Tests FHIR R4 compliance and model validation functionality.
"""

import pytest
from pydantic import ValidationError
import uuid
from datetime import datetime

from src.api.models.fhir_models import (
    OperationOutcome, OperationOutcomeIssue, FHIRBundle, ProcessingRequest,
    ValidationRequest, ValidationResponse, SummaryResponse,
    HealthCheckResponse, APIResponse, IssueSeverity, IssueType,
    create_operation_outcome, create_success_response, create_error_response
)


class TestOperationOutcome:
    """Test FHIR OperationOutcome model."""
    
    def test_valid_operation_outcome(self):
        """Test creating a valid OperationOutcome."""
        issue = OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.INVALID,
            diagnostics="Test error message"
        )
        
        outcome = OperationOutcome(issue=[issue])
        
        assert outcome.resourceType == "OperationOutcome"
        assert len(outcome.issue) == 1
        assert outcome.issue[0].severity == IssueSeverity.ERROR
        assert outcome.issue[0].code == IssueType.INVALID
        assert outcome.issue[0].diagnostics == "Test error message"
    
    def test_operation_outcome_requires_issues(self):
        """Test that OperationOutcome requires at least one issue."""
        with pytest.raises(ValidationError):
            OperationOutcome(issue=[])
    
    def test_create_operation_outcome_helper(self):
        """Test the create_operation_outcome helper function."""
        outcome = create_operation_outcome(
            severity="error",
            code="invalid",
            details="Validation failed",
            diagnostics="Field 'status' is required"
        )
        
        assert isinstance(outcome, OperationOutcome)
        assert len(outcome.issue) == 1
        
        issue = outcome.issue[0]
        assert issue.severity == IssueSeverity.ERROR
        assert issue.code == IssueType.INVALID
        assert issue.details.text == "Validation failed"
        assert issue.diagnostics == "Field 'status' is required"


class TestFHIRBundle:
    """Test FHIR Bundle model."""
    
    def test_valid_bundle(self):
        """Test creating a valid FHIR Bundle."""
        bundle = FHIRBundle(
            type="document",
            entry=[
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-001"
                    }
                }
            ]
        )
        
        assert bundle.resourceType == "Bundle"
        assert bundle.type == "document"
        assert len(bundle.entry) == 1
    
    def test_bundle_type_validation(self):
        """Test bundle type validation."""
        with pytest.raises(ValidationError, match="Bundle type must be one of"):
            FHIRBundle(
                type="invalid-type",
                entry=[{"resource": {"resourceType": "Patient"}}]
            )
    
    def test_bundle_requires_entries(self):
        """Test that bundle requires entries."""
        with pytest.raises(ValidationError, match="Bundle must contain at least one entry"):
            FHIRBundle(type="document", entry=[])
    
    def test_valid_bundle_types(self):
        """Test all valid bundle types."""
        valid_types = ["document", "collection", "batch"]
        
        for bundle_type in valid_types:
            bundle = FHIRBundle(
                type=bundle_type,
                entry=[{"resource": {"resourceType": "Patient"}}]
            )
            assert bundle.type == bundle_type


class TestProcessingRequest:
    """Test ProcessingRequest model."""
    
    def test_valid_processing_request(self):
        """Test creating a valid processing request."""
        bundle = FHIRBundle(
            type="document",
            entry=[{"resource": {"resourceType": "MedicationRequest"}}]
        )
        
        request = ProcessingRequest(
            bundle=bundle,
            processing_options={"preserve_critical": True},
            patient_preferences={"format": "concise"}
        )
        
        assert request.bundle.type == "document"
        assert request.processing_options["preserve_critical"] == True
        assert request.patient_preferences["format"] == "concise"
    
    def test_unsafe_processing_options_rejected(self):
        """Test that unsafe processing options are rejected."""
        bundle = FHIRBundle(
            type="document",
            entry=[{"resource": {"resourceType": "MedicationRequest"}}]
        )
        
        with pytest.raises(ValidationError, match="Unsafe processing option not allowed"):
            ProcessingRequest(
                bundle=bundle,
                processing_options={"disable_safety": True}
            )
    
    def test_processing_request_defaults(self):
        """Test processing request with default values."""
        bundle = FHIRBundle(
            type="document",
            entry=[{"resource": {"resourceType": "MedicationRequest"}}]
        )
        
        request = ProcessingRequest(bundle=bundle)
        
        assert request.processing_options == {}
        assert request.patient_preferences == {}


class TestValidationRequest:
    """Test ValidationRequest model."""
    
    def test_valid_validation_request(self):
        """Test creating a valid validation request."""
        resource = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order"
        }
        
        request = ValidationRequest(
            resource=resource,
            validation_mode="strict"
        )
        
        assert request.resource == resource
        assert request.validation_mode == "strict"
    
    def test_validation_mode_validation(self):
        """Test validation mode validation."""
        resource = {"resourceType": "Patient"}
        
        # Valid modes
        valid_modes = ["strict", "lenient", "profile"]
        for mode in valid_modes:
            request = ValidationRequest(resource=resource, validation_mode=mode)
            assert request.validation_mode == mode
        
        # Invalid mode
        with pytest.raises(ValidationError, match="Validation mode must be one of"):
            ValidationRequest(resource=resource, validation_mode="invalid")
    
    def test_validation_request_defaults(self):
        """Test validation request with default values."""
        resource = {"resourceType": "Patient"}
        
        request = ValidationRequest(resource=resource)
        
        assert request.validation_mode == "strict"


class TestValidationResponse:
    """Test ValidationResponse model."""
    
    def test_valid_validation_response(self):
        """Test creating a valid validation response."""
        issues = [
            OperationOutcomeIssue(
                severity=IssueSeverity.WARNING,
                code=IssueType.INCOMPLETE,
                diagnostics="Optional field missing"
            )
        ]
        
        response = ValidationResponse(
            is_valid=True,
            issues=issues,
            resource_type="MedicationRequest",
            validation_metadata={"validated_at": datetime.utcnow().isoformat()}
        )
        
        assert response.is_valid == True
        assert len(response.issues) == 1
        assert response.resource_type == "MedicationRequest"
        assert "validated_at" in response.validation_metadata
    
    def test_validation_response_defaults(self):
        """Test validation response with default values."""
        response = ValidationResponse(is_valid=True)
        
        assert response.issues == []
        assert response.resource_type is None
        assert response.validation_metadata == {}


class TestSummaryResponse:
    """Test SummaryResponse model."""
    
    def test_valid_summary_response(self):
        """Test creating a valid summary response."""
        summary_data = {
            "summary_id": str(uuid.uuid4()),
            "patient_id": "patient-001",
            "disclaimers": ["Educational purposes only"]
        }
        
        processing_metadata = {
            "processed_at": datetime.utcnow().isoformat(),
            "processing_time_seconds": 2.5
        }
        
        response = SummaryResponse(
            summary=summary_data,
            processing_metadata=processing_metadata,
            fhir_metadata={"version": "R4"}
        )
        
        assert response.summary["summary_id"] == summary_data["summary_id"]
        assert response.processing_metadata["processing_time_seconds"] == 2.5
        assert response.fhir_metadata["version"] == "R4"
    
    def test_summary_response_validation(self):
        """Test summary response validation."""
        # Missing required fields
        invalid_summary = {
            "summary_id": str(uuid.uuid4())
            # Missing patient_id and disclaimers
        }
        
        with pytest.raises(ValidationError, match="Summary must contain required field"):
            SummaryResponse(
                summary=invalid_summary,
                processing_metadata={}
            )
    
    def test_summary_response_defaults(self):
        """Test summary response with default values."""
        summary_data = {
            "summary_id": str(uuid.uuid4()),
            "patient_id": "patient-001",
            "disclaimers": ["Test disclaimer"]
        }
        
        response = SummaryResponse(
            summary=summary_data,
            processing_metadata={}
        )
        
        assert response.fhir_metadata == {}


class TestHealthCheckResponse:
    """Test HealthCheckResponse model."""
    
    def test_valid_health_response(self):
        """Test creating a valid health check response."""
        response = HealthCheckResponse(
            status="healthy",
            components={"processor": "healthy", "parser": "healthy"},
            performance_metrics={"response_time_ms": 150},
            safety_checks={"phi_protection": True, "rate_limiting": True}
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.fhir_version == "R4"
        assert response.components["processor"] == "healthy"
        assert response.performance_metrics["response_time_ms"] == 150
        assert response.safety_checks["phi_protection"] == True
    
    def test_health_response_defaults(self):
        """Test health response with default values."""
        response = HealthCheckResponse(status="healthy")
        
        assert response.components == {}
        assert response.performance_metrics == {}
        assert response.safety_checks == {}
        assert isinstance(response.timestamp, datetime)


class TestAPIResponse:
    """Test generic APIResponse model."""
    
    def test_successful_api_response(self):
        """Test creating a successful API response."""
        response = APIResponse(
            success=True,
            data={"result": "success"},
            metadata={"request_id": "test-123"}
        )
        
        assert response.success == True
        assert response.data["result"] == "success"
        assert response.errors is None
        assert response.metadata["request_id"] == "test-123"
    
    def test_error_api_response(self):
        """Test creating an error API response."""
        from src.api.models.fhir_models import ErrorDetail
        
        error = ErrorDetail(
            error_code="VALIDATION_FAILED",
            error_message="Required field missing"
        )
        
        response = APIResponse(
            success=False,
            errors=[error],
            metadata={"request_id": "test-456"}
        )
        
        assert response.success == False
        assert response.data is None
        assert len(response.errors) == 1
        assert response.errors[0].error_code == "VALIDATION_FAILED"
    
    def test_api_response_validation(self):
        """Test API response validation rules."""
        from src.api.models.fhir_models import ErrorDetail
        
        # Should fail: success=False but no errors provided
        with pytest.raises(ValidationError, match="Errors must be provided when success is False"):
            APIResponse(success=False)
    
    def test_api_response_defaults(self):
        """Test API response with default values."""
        response = APIResponse(success=True)
        
        assert response.data is None
        assert response.errors is None
        assert response.metadata == {}


class TestHelperFunctions:
    """Test helper functions for creating responses."""
    
    def test_create_success_response(self):
        """Test create_success_response helper."""
        data = {"message": "Operation completed successfully"}
        metadata = {"operation_time": "2.5s"}
        
        response = create_success_response(data, metadata)
        
        assert isinstance(response, APIResponse)
        assert response.success == True
        assert response.data == data
        assert response.metadata == metadata
        assert response.errors is None
    
    def test_create_error_response(self):
        """Test create_error_response helper."""
        response = create_error_response(
            error_code="INVALID_INPUT",
            error_message="The provided input is invalid",
            error_context={"field": "medication_name"}
        )
        
        assert isinstance(response, APIResponse)
        assert response.success == False
        assert response.data is None
        assert len(response.errors) == 1
        
        error = response.errors[0]
        assert error.error_code == "INVALID_INPUT"
        assert error.error_message == "The provided input is invalid"
        assert error.error_context["field"] == "medication_name"
    
    def test_create_error_response_without_context(self):
        """Test create_error_response without context."""
        response = create_error_response(
            error_code="SYSTEM_ERROR",
            error_message="An internal error occurred"
        )
        
        assert isinstance(response, APIResponse)
        assert response.success == False
        assert len(response.errors) == 1
        
        error = response.errors[0]
        assert error.error_code == "SYSTEM_ERROR"
        assert error.error_context is None


class TestEnumValidation:
    """Test enum validation in models."""
    
    def test_issue_severity_enum(self):
        """Test IssueSeverity enum validation."""
        # Valid values
        valid_severities = ["fatal", "error", "warning", "information"]
        
        for severity in valid_severities:
            issue = OperationOutcomeIssue(
                severity=severity,
                code=IssueType.INVALID
            )
            assert issue.severity == severity
        
        # Invalid value
        with pytest.raises(ValidationError):
            OperationOutcomeIssue(
                severity="invalid-severity",
                code=IssueType.INVALID
            )
    
    def test_issue_type_enum(self):
        """Test IssueType enum validation."""
        # Test a few key issue types
        valid_types = ["invalid", "required", "not-found", "security"]
        
        for issue_type in valid_types:
            issue = OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code=issue_type
            )
            assert issue.code == issue_type
        
        # Invalid value
        with pytest.raises(ValidationError):
            OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code="invalid-code"
            )


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_operation_outcome_serialization(self):
        """Test OperationOutcome model serialization."""
        outcome = create_operation_outcome(
            severity="error",
            code="invalid",
            details="Test error"
        )
        
        # Serialize to dict
        data = outcome.model_dump()
        
        assert data["resourceType"] == "OperationOutcome"
        assert len(data["issue"]) == 1
        assert data["issue"][0]["severity"] == "error"
        assert data["issue"][0]["code"] == "invalid"
    
    def test_bundle_serialization(self):
        """Test FHIRBundle model serialization."""
        bundle = FHIRBundle(
            type="document",
            entry=[
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-001"
                    }
                }
            ]
        )
        
        data = bundle.model_dump()
        
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "document"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["resourceType"] == "Patient"
    
    def test_model_deserialization(self):
        """Test model deserialization from dict."""
        bundle_data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest"
                    }
                }
            ]
        }
        
        bundle = FHIRBundle(**bundle_data)
        
        assert bundle.resourceType == "Bundle"
        assert bundle.type == "collection"
        assert len(bundle.entry) == 1