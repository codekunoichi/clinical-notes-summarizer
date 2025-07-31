"""
Summary retrieval and management endpoint.

Provides endpoints for retrieving and managing processed clinical summaries.
Note: This implementation provides a foundation for summary management.
In production, summaries would typically be stored with proper PHI protection.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime, timedelta

from src.api.models.fhir_models import (
    SummaryResponse, OperationOutcome, create_operation_outcome,
    create_success_response, create_error_response
)
from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# In-memory storage for demonstration purposes
# In production, this would be a proper database with PHI protection
_summary_storage: Dict[str, Dict[str, Any]] = {}
_storage_metadata: Dict[str, Dict[str, Any]] = {}


def _generate_sample_summary(summary_id: str) -> Dict[str, Any]:
    """
    Generate a sample clinical summary for demonstration.
    
    Args:
        summary_id: Summary identifier
        
    Returns:
        Sample clinical summary
    """
    return {
        "summary_id": summary_id,
        "patient_id": "sample-patient-123",
        "generated_at": datetime.utcnow().isoformat(),
        "medications": [
            {
                "medication_name": "Lisinopril",
                "dosage": "10 mg",
                "frequency": "1 time(s) per 1 day",
                "route": "Oral",
                "instructions": "Take once daily in the morning",
                "purpose": None,
                "important_notes": None,
                "metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_version": "1.0.0",
                    "safety_level": "critical",
                    "processing_type": "preserved",
                    "ai_processed": False,
                    "validation_passed": True,
                    "validation_errors": []
                }
            }
        ],
        "lab_results": [],
        "appointments": [],
        "chief_complaint": None,
        "diagnosis_explanation": None,
        "care_instructions": None,
        "follow_up_guidance": None,
        "safety_validation": {
            "validation_id": str(uuid.uuid4()),
            "validated_at": datetime.utcnow().isoformat(),
            "data_type": "clinical_summary",
            "passed": True,
            "errors": [],
            "warnings": [],
            "critical_fields_preserved": {
                "medications": True
            },
            "ai_processing_flags": {
                "medications": False
            }
        },
        "disclaimers": [
            "This summary is for educational purposes only and does not replace professional medical advice.",
            "Always consult your healthcare provider before making any changes to your medications or treatment plan.",
            "In case of emergency, call 911 or go to the nearest emergency room."
        ],
        "processing_metadata": {
            "processed_at": datetime.utcnow().isoformat(),
            "processing_version": "1.0.0",
            "safety_level": "critical",
            "processing_type": "preserved",
            "ai_processed": False,
            "validation_passed": True,
            "validation_errors": []
        }
    }


def _is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.
    
    Args:
        value: String to check
        
    Returns:
        True if valid UUID
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def _log_summary_access(summary_id: str, success: bool, operation: str) -> None:
    """
    Log summary access (PHI-safe).
    
    Args:
        summary_id: Summary identifier
        success: Whether operation was successful
        operation: Type of operation performed
    """
    logger.info(
        f"Summary {operation}: summary_id={summary_id}, success={success}"
    )


@router.get("/summary/{summary_id}", response_model=SummaryResponse)
async def get_clinical_summary(summary_id: str):
    """
    Retrieve a processed clinical summary by ID.
    
    Args:
        summary_id: Unique identifier for the clinical summary
        
    Returns:
        SummaryResponse containing the clinical summary
        
    Raises:
        HTTPException: If summary not found or invalid ID format
    """
    try:
        # Validate summary ID format
        if not _is_valid_uuid(summary_id):
            _log_summary_access(summary_id, False, "get")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary ID format. Must be a valid UUID."
            )
        
        # Check if summary exists in storage
        if summary_id in _summary_storage:
            summary_data = _summary_storage[summary_id]
            metadata = _storage_metadata.get(summary_id, {})
            
            _log_summary_access(summary_id, True, "get")
            
            return SummaryResponse(
                summary=summary_data,
                processing_metadata={
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "summary_age_minutes": (
                        datetime.utcnow() - datetime.fromisoformat(
                            metadata.get("stored_at", datetime.utcnow().isoformat())
                        )
                    ).total_seconds() / 60,
                    "storage_type": "in_memory_demo",
                    **metadata
                },
                fhir_metadata={
                    "profile": "http://hl7.org/fhir/StructureDefinition/Bundle",
                    "version": "R4",
                    "last_updated": metadata.get("stored_at", datetime.utcnow().isoformat())
                }
            )
        
        # If not found, return 404 with FHIR-compliant response
        _log_summary_access(summary_id, False, "get")
        
        operation_outcome = create_operation_outcome(
            severity="error",
            code="not-found",
            details=f"Clinical summary with ID {summary_id} was not found",
            diagnostics="The summary may have expired or never existed"
        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=operation_outcome.model_dump()
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving summary {summary_id}: {type(e).__name__}")
        _log_summary_access(summary_id, False, "get")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error occurred while retrieving summary"
        )


@router.post("/summary/{summary_id}/store", response_model=Dict[str, Any])
async def store_clinical_summary(summary_id: str, summary_data: Dict[str, Any]):
    """
    Store a processed clinical summary (for demonstration purposes).
    
    Note: In production, this would require proper PHI protection,
    encryption, and compliance with healthcare data storage regulations.
    
    Args:
        summary_id: Unique identifier for the summary
        summary_data: Clinical summary data to store
        
    Returns:
        Storage confirmation response
    """
    try:
        # Validate summary ID format
        if not _is_valid_uuid(summary_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary ID format. Must be a valid UUID."
            )
        
        # Validate summary data structure
        required_fields = ["summary_id", "patient_id", "disclaimers"]
        for field in required_fields:
            if field not in summary_data:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Summary data missing required field: {field}"
                )
        
        # Store the summary (with metadata)
        storage_metadata = {
            "stored_at": datetime.utcnow().isoformat(),
            "storage_type": "in_memory_demo",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "summary_size_bytes": len(str(summary_data)),
            "storage_version": "1.0.0"
        }
        
        _summary_storage[summary_id] = summary_data
        _storage_metadata[summary_id] = storage_metadata
        
        _log_summary_access(summary_id, True, "store")
        
        return {
            "stored": True,
            "summary_id": summary_id,
            "storage_metadata": storage_metadata,
            "warnings": [
                "This is a demonstration implementation only",
                "Production systems require proper PHI protection and encryption",
                "Summary will expire in 24 hours"
            ]
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error storing summary {summary_id}: {type(e).__name__}")
        _log_summary_access(summary_id, False, "store")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error occurred while storing summary"
        )


@router.delete("/summary/{summary_id}", response_model=Dict[str, Any])
async def delete_clinical_summary(summary_id: str):
    """
    Delete a stored clinical summary.
    
    Args:
        summary_id: Unique identifier for the summary to delete
        
    Returns:
        Deletion confirmation response
    """
    try:
        # Validate summary ID format
        if not _is_valid_uuid(summary_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary ID format. Must be a valid UUID."
            )
        
        # Check if summary exists
        if summary_id in _summary_storage:
            # Remove from storage
            del _summary_storage[summary_id]
            if summary_id in _storage_metadata:
                del _storage_metadata[summary_id]
            
            _log_summary_access(summary_id, True, "delete")
            
            return {
                "deleted": True,
                "summary_id": summary_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
        
        # If not found, return 404
        _log_summary_access(summary_id, False, "delete")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary with ID {summary_id} was not found"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting summary {summary_id}: {type(e).__name__}")
        _log_summary_access(summary_id, False, "delete")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error occurred while deleting summary"
        )


@router.get("/summaries", response_model=Dict[str, Any])
async def list_clinical_summaries(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of summaries to return"),
    offset: int = Query(default=0, ge=0, description="Number of summaries to skip")
):
    """
    List stored clinical summaries (for demonstration purposes).
    
    Note: In production, this would include proper access controls,
    patient consent verification, and PHI protection.
    
    Args:
        limit: Maximum number of summaries to return
        offset: Number of summaries to skip for pagination
        
    Returns:
        List of summary metadata (without PHI)
    """
    try:
        # Get all summary IDs
        all_summary_ids = list(_summary_storage.keys())
        
        # Apply pagination
        paginated_ids = all_summary_ids[offset:offset + limit]
        
        # Create summary list (metadata only, no PHI)
        summaries = []
        for summary_id in paginated_ids:
            metadata = _storage_metadata.get(summary_id, {})
            summary_data = _summary_storage.get(summary_id, {})
            
            summaries.append({
                "summary_id": summary_id,
                "patient_id": summary_data.get("patient_id", "unknown"),  # In production, this would be anonymized
                "generated_at": summary_data.get("generated_at"),
                "stored_at": metadata.get("stored_at"),
                "expires_at": metadata.get("expires_at"),
                "summary_size_bytes": metadata.get("summary_size_bytes", 0),
                "medication_count": len(summary_data.get("medications", [])),
                "lab_result_count": len(summary_data.get("lab_results", [])),
                "appointment_count": len(summary_data.get("appointments", []))
            })
        
        logger.info(f"Listed summaries: total={len(all_summary_ids)}, returned={len(summaries)}")
        
        return {
            "summaries": summaries,
            "pagination": {
                "total": len(all_summary_ids),
                "limit": limit,
                "offset": offset,
                "returned": len(summaries)
            },
            "warnings": [
                "This is a demonstration implementation only",
                "Production systems require proper access controls and PHI protection"
            ]
        }
    
    except Exception as e:
        logger.error(f"Error listing summaries: {type(e).__name__}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error occurred while listing summaries"
        )


@router.get("/summary/{summary_id}/metadata", response_model=Dict[str, Any])
async def get_summary_metadata(summary_id: str):
    """
    Get metadata for a clinical summary without retrieving the full content.
    
    Args:
        summary_id: Unique identifier for the summary
        
    Returns:
        Summary metadata (PHI-free)
    """
    try:
        # Validate summary ID format
        if not _is_valid_uuid(summary_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary ID format. Must be a valid UUID."
            )
        
        # Check if summary exists
        if summary_id in _summary_storage:
            metadata = _storage_metadata.get(summary_id, {})
            summary_data = _summary_storage.get(summary_id, {})
            
            _log_summary_access(summary_id, True, "metadata")
            
            return {
                "summary_id": summary_id,
                "exists": True,
                "generated_at": summary_data.get("generated_at"),
                "stored_at": metadata.get("stored_at"),
                "expires_at": metadata.get("expires_at"),
                "summary_size_bytes": metadata.get("summary_size_bytes", 0),
                "content_counts": {
                    "medications": len(summary_data.get("medications", [])),
                    "lab_results": len(summary_data.get("lab_results", [])),
                    "appointments": len(summary_data.get("appointments", []))
                },
                "processing_metadata": summary_data.get("processing_metadata", {}),
                "safety_validation": {
                    "passed": summary_data.get("safety_validation", {}).get("passed", False),
                    "error_count": len(summary_data.get("safety_validation", {}).get("errors", [])),
                    "warning_count": len(summary_data.get("safety_validation", {}).get("warnings", []))
                }
            }
        
        # If not found
        _log_summary_access(summary_id, False, "metadata")
        
        return {
            "summary_id": summary_id,
            "exists": False,
            "message": "Summary not found"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting summary metadata {summary_id}: {type(e).__name__}")
        _log_summary_access(summary_id, False, "metadata")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error occurred while retrieving summary metadata"
        )