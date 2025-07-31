"""
FHIR resource validation endpoint.

Provides comprehensive validation of FHIR resources for healthcare compliance.
"""

from fastapi import APIRouter, HTTPException, status
import logging
import time
import uuid
from typing import Dict, Any, List
from datetime import datetime

from src.api.models.fhir_models import (
    ValidationRequest, ValidationResponse, OperationOutcomeIssue,
    IssueSeverity, IssueType, create_operation_outcome
)
from src.summarizer.fhir_parser import FHIRMedicationParser
from src.models.medication import MedicationRequest
from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Global parser instance
fhir_parser = None


def _get_parser() -> FHIRMedicationParser:
    """Get or initialize the FHIR parser."""
    global fhir_parser
    if fhir_parser is None:
        try:
            fhir_parser = FHIRMedicationParser()
            logger.info("FHIR parser initialized for validation")
        except Exception as e:
            logger.error(f"Failed to initialize FHIR parser: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="FHIR validation service unavailable"
            )
    return fhir_parser


def _validate_basic_structure(resource: Dict[str, Any]) -> List[OperationOutcomeIssue]:
    """
    Validate basic FHIR resource structure.
    
    Args:
        resource: FHIR resource to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check if resource is a dictionary
    if not isinstance(resource, dict):
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.STRUCTURE,
            diagnostics="Resource must be a JSON object"
        ))
        return issues
    
    # Check for resourceType
    if "resourceType" not in resource:
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.REQUIRED,
            diagnostics="Resource must have a 'resourceType' field"
        ))
    
    # Check for valid resourceType
    resource_type = resource.get("resourceType")
    if resource_type and not isinstance(resource_type, str):
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.VALUE,
            diagnostics="ResourceType must be a string"
        ))
    
    return issues


def _validate_medication_request(resource: Dict[str, Any]) -> List[OperationOutcomeIssue]:
    """
    Validate MedicationRequest resource.
    
    Args:
        resource: MedicationRequest resource to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    parser = _get_parser()
    
    try:
        # Attempt to parse with Pydantic model
        med_request = parser.parse_medication_request(resource)
        
        # Additional validation checks
        try:
            # Test medication name extraction
            med_name = parser.extract_medication_name(med_request)
            if not med_name or len(med_name.strip()) < 2:
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.VALUE,
                    diagnostics="Medication name appears to be very short or empty"
                ))
        except ValueError as e:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code=IssueType.REQUIRED,
                diagnostics=f"Cannot extract medication name: {str(e)}"
            ))
        
        try:
            # Test dosage information extraction
            dosage_info = parser.extract_dosage_information(med_request)
            
            # Check if critical dosage fields are present
            if not dosage_info.get("dosage"):
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.INCOMPLETE,
                    diagnostics="Dosage amount not specified"
                ))
            
            if not dosage_info.get("frequency"):
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.INCOMPLETE,
                    diagnostics="Dosage frequency not specified"
                ))
                
        except Exception as e:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.WARNING,
                code=IssueType.INCOMPLETE,
                diagnostics=f"Dosage information may be incomplete: {str(e)}"
            ))
        
        # Test integrity validation
        try:
            integrity_ok = parser.validate_parsing_integrity(resource, med_request)
            if not integrity_ok:
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.ERROR,
                    code=IssueType.INVARIANT,
                    diagnostics="Data integrity validation failed"
                ))
        except Exception:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.WARNING,
                code=IssueType.PROCESSING,
                diagnostics="Could not perform integrity validation"
            ))
    
    except ValueError as e:
        # Pydantic validation failed
        error_msg = str(e)
        
        # Try to provide more specific error information
        if "medicationCodeableConcept" in error_msg or "medicationReference" in error_msg:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code=IssueType.REQUIRED,
                diagnostics="Either medicationCodeableConcept or medicationReference must be specified"
            ))
        elif "dosageInstruction" in error_msg:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code=IssueType.INVALID,
                diagnostics=f"Invalid dosage instruction: {error_msg}"
            ))
        else:
            issues.append(OperationOutcomeIssue(
                severity=IssueSeverity.ERROR,
                code=IssueType.INVALID,
                diagnostics=f"MedicationRequest validation failed: {error_msg}"
            ))
    
    except Exception as e:
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.EXCEPTION,
            diagnostics=f"Unexpected validation error: {type(e).__name__}"
        ))
    
    return issues


def _validate_bundle(resource: Dict[str, Any]) -> List[OperationOutcomeIssue]:
    """
    Validate Bundle resource.
    
    Args:
        resource: Bundle resource to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check bundle type
    bundle_type = resource.get("type")
    if not bundle_type:
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.REQUIRED,
            diagnostics="Bundle must have a 'type' field"
        ))
    elif bundle_type not in ["document", "message", "transaction", "transaction-response", 
                           "batch", "batch-response", "history", "searchset", "collection"]:
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.WARNING,
            code=IssueType.VALUE,
            diagnostics=f"Unusual bundle type: {bundle_type}"
        ))
    
    # Check entries
    entries = resource.get("entry", [])
    if not entries:
        issues.append(OperationOutcomeIssue(
            severity=IssueSeverity.WARNING,
            code=IssueType.INCOMPLETE,
            diagnostics="Bundle contains no entries"
        ))
    else:
        # Validate each entry
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.ERROR,
                    code=IssueType.STRUCTURE,
                    diagnostics=f"Entry {i} is not a valid object"
                ))
                continue
            
            # Check if entry has a resource
            entry_resource = entry.get("resource")
            if not entry_resource:
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.INCOMPLETE,
                    diagnostics=f"Entry {i} has no resource"
                ))
                continue
            
            # Validate the contained resource
            entry_resource_type = entry_resource.get("resourceType")
            if entry_resource_type == "MedicationRequest":
                entry_issues = _validate_medication_request(entry_resource)
                # Add entry context to issues
                for issue in entry_issues:
                    issue.diagnostics = f"Entry {i}: {issue.diagnostics}"
                    issues.extend([issue])
    
    return issues


def _create_validation_metadata(
    resource_type: str,
    validation_time: float,
    validation_mode: str,
    request_id: str
) -> Dict[str, Any]:
    """
    Create validation metadata.
    
    Args:
        resource_type: Type of resource validated
        validation_time: Time taken for validation
        validation_mode: Validation mode used
        request_id: Unique request identifier
        
    Returns:
        Validation metadata dictionary
    """
    return {
        "request_id": request_id,
        "validated_at": datetime.utcnow().isoformat(),
        "validation_time_seconds": round(validation_time, 3),
        "validation_mode": validation_mode,
        "resource_type": resource_type,
        "validator_version": "1.0.0",
        "fhir_version": "R4",
        "validation_profile": "Clinical Notes Summarizer"
    }


@router.post("/validate", response_model=ValidationResponse)
async def validate_fhir_resource(request: ValidationRequest):
    """
    Validate FHIR resource for healthcare compliance.
    
    Performs comprehensive validation of FHIR resources including:
    - Basic structure validation
    - Resource-specific validation
    - Healthcare safety checks
    - Data integrity verification
    
    Args:
        request: ValidationRequest containing resource and validation options
        
    Returns:
        ValidationResponse with detailed validation results
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        resource = request.resource
        validation_mode = request.validation_mode
        
        # Basic structure validation
        issues = _validate_basic_structure(resource)
        
        # Resource-specific validation
        resource_type = resource.get("resourceType")
        
        if resource_type == "MedicationRequest":
            resource_issues = _validate_medication_request(resource)
            issues.extend(resource_issues)
        elif resource_type == "Bundle":
            bundle_issues = _validate_bundle(resource)
            issues.extend(bundle_issues)
        elif resource_type in ["Patient", "Practitioner", "Organization"]:
            # Basic validation for supported but not fully implemented resources
            if validation_mode == "strict":
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.NOT_SUPPORTED,
                    diagnostics=f"Detailed validation for {resource_type} not fully implemented"
                ))
        else:
            # Unsupported resource type
            if validation_mode == "strict":
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.ERROR,
                    code=IssueType.NOT_SUPPORTED,
                    diagnostics=f"Resource type {resource_type} is not supported for processing"
                ))
            else:
                issues.append(OperationOutcomeIssue(
                    severity=IssueSeverity.WARNING,
                    code=IssueType.NOT_SUPPORTED,
                    diagnostics=f"Resource type {resource_type} has limited validation support"
                ))
        
        # Determine overall validation result
        error_issues = [issue for issue in issues if issue.severity == IssueSeverity.ERROR]
        is_valid = len(error_issues) == 0
        
        # Calculate validation time
        validation_time = time.time() - start_time
        
        # Create validation metadata
        validation_metadata = _create_validation_metadata(
            resource_type or "unknown",
            validation_time,
            validation_mode,
            request_id
        )
        
        # Log validation result (PHI-safe)
        logger.info(
            f"FHIR validation completed: request_id={request_id}, "
            f"resource_type={resource_type}, valid={is_valid}, "
            f"issues={len(issues)}, time={validation_time:.3f}s"
        )
        
        return ValidationResponse(
            is_valid=is_valid,
            issues=issues,
            resource_type=resource_type,
            validation_metadata=validation_metadata
        )
    
    except Exception as e:
        validation_time = time.time() - start_time
        logger.error(f"Validation failed with error: {type(e).__name__}")
        
        # Return error response
        error_issue = OperationOutcomeIssue(
            severity=IssueSeverity.ERROR,
            code=IssueType.EXCEPTION,
            diagnostics=f"Validation failed due to internal error"
        )
        
        return ValidationResponse(
            is_valid=False,
            issues=[error_issue],
            resource_type=resource.get("resourceType") if isinstance(resource, dict) else None,
            validation_metadata={
                "request_id": request_id,
                "error": True,
                "validation_time_seconds": round(validation_time, 3),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.post("/validate/medication-request", response_model=ValidationResponse)
async def validate_medication_request_specific(medication_request: Dict[str, Any]):
    """
    Specialized validation endpoint for MedicationRequest resources.
    
    Provides detailed validation specifically for medication data with
    healthcare safety focus.
    
    Args:
        medication_request: MedicationRequest resource to validate
        
    Returns:
        ValidationResponse with medication-specific validation results
    """
    # Create a validation request
    request = ValidationRequest(
        resource=medication_request,
        validation_mode="strict"
    )
    
    # Use the main validation endpoint
    return await validate_fhir_resource(request)


@router.post("/validate/bundle", response_model=ValidationResponse)
async def validate_bundle_specific(bundle: Dict[str, Any]):
    """
    Specialized validation endpoint for Bundle resources.
    
    Provides detailed validation for FHIR Bundles with focus on
    clinical document processing requirements.
    
    Args:
        bundle: Bundle resource to validate
        
    Returns:
        ValidationResponse with bundle-specific validation results
    """
    # Create a validation request
    request = ValidationRequest(
        resource=bundle,
        validation_mode="strict"
    )
    
    # Use the main validation endpoint
    return await validate_fhir_resource(request)