"""
Translation endpoints for multilingual fridge magnet summaries.

Provides endpoints for translating patient-friendly clinical summaries
to Spanish and Mandarin while preserving critical medical data.
"""

from fastapi import APIRouter, HTTPException, status, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional, Union, Literal
import logging
import json
from datetime import datetime
from pydantic import BaseModel, Field

from src.api.models.fhir_models import (
    SummaryResponse, OperationOutcome, create_operation_outcome,
    create_success_response, create_error_response
)
from src.api.core.config import get_settings
from src.formatter.patient_friendly import PatientFriendlyFormatter
from src.formatter.models import OutputFormat
from src.summarizer.hybrid_processor import HybridClinicalProcessor

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Translation language options
TranslationLanguage = Literal["spanish", "mandarin"]


class TranslationRequest(BaseModel):
    """Request model for translating existing fridge magnet content."""
    english_content: str = Field(..., description="English fridge magnet content to translate")
    target_language: TranslationLanguage = Field(..., description="Target language for translation")
    output_format: str = Field("html", description="Output format (html or text)")


class TranslateAndFormatRequest(BaseModel):
    """Request model for processing clinical data and translating to target language."""
    fhir_data: Dict[str, Any] = Field(..., description="FHIR clinical data")
    target_language: TranslationLanguage = Field(..., description="Target language for translation")
    output_format: str = Field("html", description="Output format (html or text)")


class TranslationResponse(BaseModel):
    """Response model for translation operations."""
    success: bool
    translated_content: str
    metadata: Dict[str, Any]
    original_language: str = "english"
    target_language: str
    translation_timestamp: str
    critical_data_preserved: bool = True


@router.post("/translate", 
             response_model=TranslationResponse,
             summary="Translate existing fridge magnet content",
             description="Translate already-formatted English fridge magnet to Spanish or Mandarin")
async def translate_fridge_magnet(request: TranslationRequest) -> TranslationResponse:
    """
    Translate existing English fridge magnet content to target language.
    
    This endpoint takes completed English fridge magnet content and translates it
    while preserving all critical medical data (medications, dosages, lab values).
    """
    try:
        logger.info(f"Translating fridge magnet content to {request.target_language}")
        
        # Initialize formatter with translation capability
        formatter = PatientFriendlyFormatter()
        
        if not formatter.translation_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Translation service not available - missing translation models"
            )
        
        # Create a mock FormattedOutput object for translation
        from src.formatter.models import FormattedOutput
        
        output_format = OutputFormat.HTML if request.output_format.lower() == "html" else OutputFormat.PLAIN_TEXT
        
        formatted_output = FormattedOutput(
            content=request.english_content,
            output_format=output_format,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "content_length": len(request.english_content)
            }
        )
        
        # Translate the content
        translated_output = formatter.translate_formatted_output(
            formatted_output, 
            request.target_language
        )
        
        return TranslationResponse(
            success=True,
            translated_content=translated_output.content,
            metadata=translated_output.metadata,
            target_language=request.target_language,
            translation_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/process-and-translate",
             response_model=TranslationResponse,
             summary="Process clinical data and translate to target language",
             description="One-step processing: FHIR/CCDA data → English fridge magnet → Translated fridge magnet")
async def process_and_translate(request: TranslateAndFormatRequest) -> TranslationResponse:
    """
    Process clinical data and translate directly to target language.
    
    This endpoint combines the full pipeline:
    1. Process FHIR clinical data
    2. Generate English fridge magnet
    3. Translate to target language
    """
    try:
        logger.info(f"Processing clinical data and translating to {request.target_language}")
        
        # Step 1: Process clinical data
        processor = HybridClinicalProcessor()
        clinical_summary = processor.process_clinical_data(request.fhir_data)
        
        # Step 2: Format and translate in one step
        formatter = PatientFriendlyFormatter()
        
        if not formatter.translation_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Translation service not available - missing translation models"
            )
        
        output_format = OutputFormat.HTML if request.output_format.lower() == "html" else OutputFormat.PLAIN_TEXT
        
        # Use the combined format and translate method
        translated_output = formatter.format_and_translate(
            clinical_summary,
            output_format,
            request.target_language
        )
        
        return TranslationResponse(
            success=True,
            translated_content=translated_output.content,
            metadata=translated_output.metadata,
            target_language=request.target_language,
            translation_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Process and translate failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Process and translate failed: {str(e)}"
        )


@router.post("/translate-ccda",
             response_model=TranslationResponse,
             summary="Process CCDA document and translate to target language",
             description="Process CCDA XML document and translate to Spanish or Mandarin")
async def translate_ccda_document(
    ccda_file: UploadFile = File(..., description="CCDA XML document"),
    target_language: TranslationLanguage = Form(..., description="Target language"),
    output_format: str = Form("html", description="Output format")
) -> TranslationResponse:
    """
    Process CCDA document and translate to target language.
    
    This endpoint handles CCDA XML upload, processing, and translation.
    """
    try:
        logger.info(f"Processing CCDA document and translating to {target_language}")
        
        # Read CCDA content
        ccda_content = await ccda_file.read()
        ccda_text = ccda_content.decode('utf-8')
        
        # Step 1: Process CCDA document
        processor = HybridClinicalProcessor()
        clinical_summary = processor.process_ccda_document(ccda_text)
        
        # Step 2: Format and translate
        formatter = PatientFriendlyFormatter()
        
        if not formatter.translation_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Translation service not available - missing translation models"
            )
        
        output_fmt = OutputFormat.HTML if output_format.lower() == "html" else OutputFormat.PLAIN_TEXT
        
        translated_output = formatter.format_and_translate(
            clinical_summary,
            output_fmt,
            target_language
        )
        
        return TranslationResponse(
            success=True,
            translated_content=translated_output.content,
            metadata=translated_output.metadata,
            target_language=target_language,
            translation_timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"CCDA translate failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CCDA translation failed: {str(e)}"
        )


@router.get("/supported-languages",
            response_model=Dict[str, Any],
            summary="Get supported translation languages",
            description="List all supported languages for translation")
async def get_supported_languages():
    """Get list of supported translation languages."""
    return {
        "supported_languages": [
            {
                "code": "spanish",
                "name": "Spanish",
                "description": "Medical Spanish (Mexican/Central American)",
                "available": True
            },
            {
                "code": "mandarin", 
                "name": "Mandarin Chinese",
                "description": "Simplified Chinese",
                "available": True
            }
        ],
        "translation_engine": "mBART-50",
        "medical_safety": "Zero-tolerance medication/dosage preservation",
        "service_status": "ready"
    }


@router.get("/translation-status",
            response_model=Dict[str, Any],
            summary="Check translation service status",
            description="Get current status of translation service and models")
async def get_translation_status():
    """Check translation service status."""
    try:
        # Check if translation is available
        formatter = PatientFriendlyFormatter()
        
        return {
            "translation_available": formatter.translation_enabled,
            "supported_languages": ["spanish", "mandarin"],
            "model_status": "ready" if formatter.translation_enabled else "not_loaded",
            "safety_features": {
                "medication_preservation": True,
                "lab_value_preservation": True,
                "dosage_preservation": True,
                "phi_protection": True
            },
            "service_version": "1.0.0",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Translation status check failed: {str(e)}")
        return {
            "translation_available": False,
            "error": str(e),
            "service_status": "error"
        }


@router.get("/health",
            summary="Translation service health check",
            description="Health check endpoint for translation service")
async def translation_health_check():
    """Translation service health check."""
    try:
        formatter = PatientFriendlyFormatter()
        
        return {
            "service": "translation",
            "status": "healthy" if formatter.translation_enabled else "degraded",
            "translation_enabled": formatter.translation_enabled,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Translation health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Translation service unhealthy: {str(e)}"
        )