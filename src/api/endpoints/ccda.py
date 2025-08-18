"""
CCDA API Endpoints

This module provides FastAPI endpoints for processing CCDA (Continuity of Care Document)
XML files with the same safety guarantees as FHIR processing.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse

from src.api.models.fhir_models import (
    SummaryResponse,
    ValidationResponse
)
from src.models.clinical import ClinicalSummary
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.summarizer.ccda_parser import CCDAParsingError, CCDASecurityError, CCDAValidationError
from src.formatter.patient_friendly import PatientFriendlyFormatter

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ccda", tags=["ccda"])


async def get_ccda_processor() -> HybridClinicalProcessor:
    """Dependency to get CCDA processor instance."""
    return HybridClinicalProcessor(enable_ai_enhancement=True)


async def get_formatter() -> PatientFriendlyFormatter:
    """Dependency to get patient-friendly formatter instance."""
    return PatientFriendlyFormatter()


@router.post("/validate")
async def validate_ccda_document(
    ccda_file: UploadFile = File(...),
    processor: HybridClinicalProcessor = Depends(get_ccda_processor)
) -> ValidationResponse:
    """
    Validate CCDA document structure and security.
    
    This endpoint performs comprehensive validation of CCDA XML including:
    - XML security validation (XXE, DTD protection)
    - CCDA schema validation
    - Section presence validation
    - Data integrity validation
    
    Args:
        ccda_file: CCDA XML file upload
        
    Returns:
        ValidationResponse with validation results
        
    Raises:
        HTTPException: If validation fails or file processing errors occur
    """
    logger.info(f"CCDA validation request received for file: {ccda_file.filename}")
    
    try:
        # Validate file type
        if not ccda_file.filename.lower().endswith(('.xml', '.ccda')):
            raise HTTPException(
                status_code=400,
                detail="File must be XML or CCDA format"
            )
        
        # Read file content
        content = await ccda_file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="Empty file provided"
            )
        
        ccda_xml = content.decode('utf-8')
        
        # Perform validation through parser
        ccda_data = processor.ccda_parser.parse_ccda_document(ccda_xml)
        
        # Extract validation information
        sections_found = list(ccda_data.get('sections', {}).keys())
        metadata = ccda_data.get('metadata', {})
        
        # Check for required sections
        required_sections = ['medications', 'results', 'vital_signs', 'allergies']
        missing_sections = [section for section in required_sections if section not in sections_found]
        
        validation_warnings = []
        if missing_sections:
            validation_warnings.append(f"Missing recommended sections: {', '.join(missing_sections)}")
        
        logger.info(f"CCDA validation completed successfully. Sections found: {sections_found}")
        
        return ValidationResponse(
            is_valid=True,
            document_type="ccda",
            sections_found=sections_found,
            validation_errors=[],
            validation_warnings=validation_warnings,
            document_metadata={
                "document_id": metadata.get('document_id'),
                "title": metadata.get('title'),
                "effective_time": metadata.get('effective_time'),
                "template_ids": metadata.get('template_ids', [])
            },
            security_validated=ccda_data.get('security_validated', False)
        )
        
    except CCDASecurityError as e:
        logger.warning(f"CCDA security validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Security validation failed: {str(e)}"
        )
    except CCDAValidationError as e:
        logger.warning(f"CCDA structure validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Document validation failed: {str(e)}"
        )
    except CCDAParsingError as e:
        logger.error(f"CCDA parsing failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Document parsing failed: {str(e)}"
        )
    except UnicodeDecodeError:
        logger.error("File encoding error")
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        logger.error(f"Unexpected error during CCDA validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during validation"
        )


@router.post("/summarize")
async def summarize_ccda_document(
    ccda_file: UploadFile = File(...),
    processor: HybridClinicalProcessor = Depends(get_ccda_processor)
) -> SummaryResponse:
    """
    Process CCDA document into patient-friendly summary.
    
    This endpoint provides the same functionality as FHIR processing but accepts
    CCDA XML input. The safety guarantees and processing approach are identical:
    - Critical data (medications, labs, vitals) preserved exactly
    - Narrative content enhanced for patient comprehension
    - Complete audit trail and safety validation
    
    Args:
        ccda_file: CCDA XML file upload
        processing_options: Optional processing configuration
        
    Returns:
        ClinicalSummaryResponse with patient-friendly summary
        
    Raises:
        HTTPException: If processing fails or validation errors occur
    """
    logger.info(f"CCDA summarization request received for file: {ccda_file.filename}")
    
    try:
        # Validate file type
        if not ccda_file.filename.lower().endswith(('.xml', '.ccda')):
            raise HTTPException(
                status_code=400,
                detail="File must be XML or CCDA format"
            )
        
        # Read and validate file content
        content = await ccda_file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="Empty file provided"
            )
        
        # Check file size (50MB limit for security)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            )
        
        ccda_xml = content.decode('utf-8')
        
        # Process CCDA document
        clinical_summary = processor.process_ccda_document(ccda_xml)
        
        logger.info(f"CCDA processing completed successfully. Summary ID: {clinical_summary.summary_id}")
        
        # Convert to response format
        return SummaryResponse(
            summary=clinical_summary.model_dump(),
            processing_metadata=clinical_summary.processing_metadata.model_dump(),
            fhir_metadata={
                "source_document_type": "ccda",
                "processing_version": "1.0.0",
                "ccda_sections_processed": clinical_summary.processing_metadata.ccda_sections_processed
            }
        )
        
    except CCDASecurityError as e:
        logger.warning(f"CCDA security validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Security validation failed: {str(e)}"
        )
    except CCDAValidationError as e:
        logger.warning(f"CCDA structure validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Document validation failed: {str(e)}"
        )
    except CCDAParsingError as e:
        logger.error(f"CCDA parsing failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Document parsing failed: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Processing validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Processing failed safety validation: {str(e)}"
        )
    except UnicodeDecodeError:
        logger.error("File encoding error")
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        logger.error(f"Unexpected error during CCDA processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during processing"
        )


@router.post("/summarize/html")
async def summarize_ccda_to_html(
    ccda_file: UploadFile = File(...),
    processor: HybridClinicalProcessor = Depends(get_ccda_processor),
    formatter: PatientFriendlyFormatter = Depends(get_formatter)
) -> HTMLResponse:
    """
    Process CCDA document and return patient-friendly HTML summary.
    
    This endpoint processes CCDA documents and returns a formatted HTML
    summary in the "fridge magnet" format for patient use.
    
    Args:
        ccda_file: CCDA XML file upload
        processing_options: Optional processing configuration
        
    Returns:
        HTMLResponse with formatted patient summary
        
    Raises:
        HTTPException: If processing fails or validation errors occur
    """
    logger.info(f"CCDA HTML summarization request received for file: {ccda_file.filename}")
    
    try:
        # Validate file type
        if not ccda_file.filename.lower().endswith(('.xml', '.ccda')):
            raise HTTPException(
                status_code=400,
                detail="File must be XML or CCDA format"
            )
        
        # Read and validate file content
        content = await ccda_file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="Empty file provided"
            )
        
        ccda_xml = content.decode('utf-8')
        
        # Process CCDA document
        clinical_summary = processor.process_ccda_document(ccda_xml)
        
        # Format as patient-friendly HTML
        html_summary = formatter.format_summary(clinical_summary)
        
        logger.info(f"CCDA HTML processing completed successfully. Summary ID: {clinical_summary.summary_id}")
        
        return HTMLResponse(
            content=html_summary,
            status_code=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "X-Summary-ID": clinical_summary.summary_id,
                "X-Source-Type": "ccda"
            }
        )
        
    except Exception as e:
        logger.error(f"Error during CCDA HTML processing: {str(e)}")
        # Create error HTML response
        error_html = f"""
        <html>
        <head><title>Processing Error</title></head>
        <body>
            <h1>Error Processing CCDA Document</h1>
            <p>Unable to process the uploaded CCDA document: {str(e)}</p>
            <p>Please check your document format and try again.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)


@router.get("/health")
async def ccda_health_check():
    """
    Health check for CCDA processing capabilities.
    
    Returns:
        Dict indicating CCDA service health status
    """
    try:
        # Test CCDA parser initialization
        processor = HybridClinicalProcessor()
        ccda_parser_healthy = processor.ccda_parser is not None
        ccda_transformer_healthy = processor.ccda_transformer is not None
        
        return {
            "service": "ccda_processor",
            "status": "healthy" if ccda_parser_healthy and ccda_transformer_healthy else "degraded",
            "components": {
                "ccda_parser": "healthy" if ccda_parser_healthy else "error",
                "ccda_transformer": "healthy" if ccda_transformer_healthy else "error",
                "xml_processing": "available",
                "security_validation": "active"
            },
            "supported_formats": ["CCDA XML", "CCD"],
            "max_file_size_mb": 50
        }
        
    except Exception as e:
        logger.error(f"CCDA health check failed: {str(e)}")
        return {
            "service": "ccda_processor",
            "status": "error", 
            "error": str(e)
        }