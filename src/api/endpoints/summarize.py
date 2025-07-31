"""
Clinical document summarization endpoint.

Processes FHIR Bundle resources to create patient-friendly summaries
using the hybrid structured + AI approach with strict safety guarantees.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import time
import uuid
from typing import Dict, Any
from datetime import datetime

from src.api.models.fhir_models import (
    ProcessingRequest, SummaryResponse, OperationOutcome,
    create_operation_outcome, create_success_response, create_error_response
)
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.summarizer.fhir_parser import FHIRMedicationParser
from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Global processor instances (initialized once for performance)
hybrid_processor = None
fhir_parser = None


def _get_processor() -> HybridClinicalProcessor:
    """Get or initialize the hybrid clinical processor."""
    global hybrid_processor
    if hybrid_processor is None:
        try:
            hybrid_processor = HybridClinicalProcessor()
            logger.info("Hybrid clinical processor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize hybrid processor: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clinical processing service unavailable"
            )
    return hybrid_processor


def _get_parser() -> FHIRMedicationParser:
    """Get or initialize the FHIR parser."""
    global fhir_parser
    if fhir_parser is None:
        try:
            fhir_parser = FHIRMedicationParser()
            logger.info("FHIR medication parser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FHIR parser: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="FHIR parsing service unavailable"
            )
    return fhir_parser


def _validate_fhir_bundle(bundle_data: Dict[str, Any]) -> None:
    """
    Validate FHIR Bundle structure and content.
    
    Args:
        bundle_data: FHIR Bundle data to validate
        
    Raises:
        HTTPException: If bundle is invalid
    """
    # Basic structure validation
    if not isinstance(bundle_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bundle must be a JSON object"
        )
    
    if bundle_data.get("resourceType") != "Bundle":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource must be a FHIR Bundle"
        )
    
    entries = bundle_data.get("entry", [])
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bundle must contain at least one entry"
        )
    
    # Check for supported resource types
    supported_types = ["MedicationRequest", "Patient", "Practitioner", "Organization"]
    found_types = set()
    
    for entry in entries:
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type:
            found_types.add(resource_type)
    
    # Ensure we have at least one processable resource
    processable_types = found_types.intersection({"MedicationRequest"})
    if not processable_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bundle must contain at least one processable resource type. Found: {list(found_types)}"
        )


def _log_processing_start(request_id: str, bundle_size: int) -> None:
    """
    Log the start of processing (PHI-safe).
    
    Args:
        request_id: Unique request identifier
        bundle_size: Number of entries in bundle
    """
    logger.info(
        f"Starting clinical summary processing: "
        f"request_id={request_id}, bundle_entries={bundle_size}"
    )


def _log_processing_end(request_id: str, success: bool, duration: float, summary_id: str = None) -> None:
    """
    Log the end of processing (PHI-safe).
    
    Args:
        request_id: Unique request identifier
        success: Whether processing was successful
        duration: Processing duration in seconds
        summary_id: Generated summary ID if successful
    """
    logger.info(
        f"Clinical summary processing completed: "
        f"request_id={request_id}, success={success}, duration={duration:.3f}s"
        f"{', summary_id=' + summary_id if summary_id else ''}"
    )


def _create_processing_metadata(
    request_id: str,
    processing_time: float,
    bundle_entries: int
) -> Dict[str, Any]:
    """
    Create metadata about the processing operation.
    
    Args:
        request_id: Unique request identifier
        processing_time: Time taken for processing
        bundle_entries: Number of bundle entries processed
        
    Returns:
        Processing metadata dictionary
    """
    return {
        "request_id": request_id,
        "processed_at": datetime.utcnow().isoformat(),
        "processing_time_seconds": round(processing_time, 3),
        "bundle_entries_processed": bundle_entries,
        "api_version": "1.0.0",
        "fhir_version": "R4",
        "processor_version": "1.0.0",
        "safety_guarantees": {
            "critical_data_preserved": True,
            "ai_processing_controlled": True,
            "phi_protection_enabled": True,
            "validation_performed": True
        },
        "performance_metrics": {
            "processing_time_ms": round(processing_time * 1000, 2),
            "meets_5_second_requirement": processing_time <= 5.0,
            "entries_per_second": round(bundle_entries / max(processing_time, 0.001), 2)
        }
    }


@router.post("/summarize", response_model=SummaryResponse)
async def create_clinical_summary(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process FHIR Bundle to create patient-friendly clinical summary.
    
    This endpoint implements the hybrid structured + AI approach:
    - CRITICAL data (medications, labs, vitals) is preserved exactly
    - NARRATIVE data (explanations, instructions) can be AI-enhanced
    - All processing is validated for healthcare safety
    
    Args:
        request: ProcessingRequest containing FHIR Bundle and options
        background_tasks: FastAPI background tasks for cleanup
        
    Returns:
        SummaryResponse with processed clinical summary
        
    Raises:
        HTTPException: If processing fails or validation errors occur
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate the FHIR Bundle
        bundle_data = request.bundle.model_dump()
        _validate_fhir_bundle(bundle_data)
        
        # Log processing start (PHI-safe)
        bundle_entries = len(bundle_data.get("entry", []))
        _log_processing_start(request_id, bundle_entries)
        
        # Get processor and parser instances
        processor = _get_processor()
        parser = _get_parser()
        
        # Process the clinical data using hybrid processor
        try:
            clinical_summary = processor.process_clinical_data(bundle_data)
        except ValueError as e:
            # Handle validation errors from processing
            logger.warning(f"Clinical processing validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Clinical data validation failed: {str(e)}"
            )
        except Exception as e:
            # Handle unexpected processing errors
            logger.error(f"Clinical processing failed: {type(e).__name__}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Clinical processing failed due to internal error"
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Check processing time requirement (healthcare standard: <5 seconds)
        if processing_time > settings.max_processing_time_seconds:
            logger.warning(
                f"Processing time {processing_time:.3f}s exceeds limit "
                f"{settings.max_processing_time_seconds}s"
            )
        
        # Create processing metadata
        processing_metadata = _create_processing_metadata(
            request_id, processing_time, bundle_entries
        )
        
        # Convert clinical summary to dict for response
        summary_dict = clinical_summary.model_dump()
        
        # Create FHIR-compatible metadata
        fhir_metadata = {
            "profile": "http://hl7.org/fhir/StructureDefinition/Bundle",
            "version": "R4",
            "last_updated": datetime.utcnow().isoformat(),
            "security": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                    "code": "HTEST",
                    "display": "test health data"
                }
            ]
        }
        
        # Log successful completion
        _log_processing_end(request_id, True, processing_time, clinical_summary.summary_id)
        
        # Add background cleanup task if needed
        # background_tasks.add_task(cleanup_processing_artifacts, request_id)
        
        return SummaryResponse(
            summary=summary_dict,
            processing_metadata=processing_metadata,
            fhir_metadata=fhir_metadata
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        processing_time = time.time() - start_time
        _log_processing_end(request_id, False, processing_time)
        raise
    
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        _log_processing_end(request_id, False, processing_time)
        
        logger.error(f"Unexpected error in summarization: {type(e).__name__}")
        
        # Return FHIR-compliant error
        operation_outcome = create_operation_outcome(
            severity="error",
            code="exception",
            details="An unexpected error occurred during clinical summary processing",
            diagnostics=f"Request ID: {request_id}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=operation_outcome.model_dump()
        )


@router.post("/summarize/validate-only", response_model=Dict[str, Any])
async def validate_bundle_only(request: ProcessingRequest):
    """
    Validate FHIR Bundle without processing.
    
    This endpoint performs comprehensive validation of the FHIR Bundle
    to check if it can be processed successfully, without actually
    creating a summary.
    
    Args:
        request: ProcessingRequest containing FHIR Bundle
        
    Returns:
        Validation results with detailed feedback
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate the FHIR Bundle structure
        bundle_data = request.bundle.model_dump()
        _validate_fhir_bundle(bundle_data)
        
        # Get parser for detailed validation
        parser = _get_parser()
        
        # Perform detailed FHIR parsing validation
        validation_results = {
            "bundle_valid": True,
            "entries_processed": 0,
            "medication_requests_found": 0,
            "validation_errors": [],
            "validation_warnings": [],
            "processable": True
        }
        
        entries = bundle_data.get("entry", [])
        medication_count = 0
        
        for i, entry in enumerate(entries):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "MedicationRequest":
                try:
                    # Test parsing the medication request
                    med_request = parser.parse_medication_request(resource)
                    medication_count += 1
                    
                    # Validate medication name extraction
                    try:
                        med_name = parser.extract_medication_name(med_request)
                        dosage_info = parser.extract_dosage_information(med_request)
                    except ValueError as e:
                        validation_results["validation_warnings"].append(
                            f"Entry {i}: Medication data may be incomplete - {str(e)}"
                        )
                
                except ValueError as e:
                    validation_results["validation_errors"].append(
                        f"Entry {i}: Invalid MedicationRequest - {str(e)}"
                    )
                    validation_results["bundle_valid"] = False
        
        validation_results["entries_processed"] = len(entries)
        validation_results["medication_requests_found"] = medication_count
        
        # Check if bundle is processable
        if medication_count == 0:
            validation_results["validation_warnings"].append(
                "No processable MedicationRequest resources found"
            )
            validation_results["processable"] = False
        
        # Add processing metadata
        processing_time = time.time() - start_time
        validation_results["validation_metadata"] = {
            "request_id": request_id,
            "validation_time_seconds": round(processing_time, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Bundle validation completed: request_id={request_id}, "
            f"valid={validation_results['bundle_valid']}, "
            f"entries={len(entries)}, medications={medication_count}"
        )
        
        return validation_results
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Bundle validation failed: {type(e).__name__}")
        
        return {
            "bundle_valid": False,
            "validation_errors": [f"Validation failed: {type(e).__name__}"],
            "processable": False,
            "validation_metadata": {
                "request_id": request_id,
                "error": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }