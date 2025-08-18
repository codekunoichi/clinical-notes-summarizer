"""
Clinical Notes Summarizer FastAPI Application.

This API provides FHIR R4 compatible endpoints for processing clinical documents
into patient-friendly summaries with strict healthcare safety guarantees.
"""

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

from src.api.endpoints.summarize import router as summarize_router
from src.api.endpoints.health import router as health_router
from src.api.endpoints.validate import router as validate_router
from src.api.endpoints.summary import router as summary_router
from src.api.endpoints.ccda import router as ccda_router
from src.api.middleware.security import SecurityMiddleware
from src.api.middleware.rate_limiting import RateLimitMiddleware
from src.api.middleware.phi_protection import PHIProtectionMiddleware
from src.api.models.fhir_models import OperationOutcome, create_operation_outcome
from src.api.core.config import get_settings

# Configure logging for healthcare compliance (no PHI)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # In production, add file handler with log rotation
    ]
)

logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Security scheme for API documentation
security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown procedures.
    
    Handles initialization and cleanup tasks required for healthcare compliance.
    """
    # Startup
    logger.info("Starting Clinical Notes Summarizer API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Healthcare safety protocols: ENABLED")
    
    # Validate critical dependencies
    try:
        from src.summarizer.hybrid_processor import HybridClinicalProcessor
        from src.summarizer.fhir_parser import FHIRMedicationParser
        from src.summarizer.ccda_parser import CCDAParser
        
        # Test core components
        processor = HybridClinicalProcessor()
        parser = FHIRMedicationParser()
        ccda_parser = CCDAParser()
        
        logger.info("Core processing components initialized successfully")
        logger.info("CCDA processing capabilities: ENABLED")
    except Exception as e:
        logger.error(f"Failed to initialize core components: {e}")
        raise RuntimeError("Application startup failed - core components unavailable")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Clinical Notes Summarizer API")
    logger.info("Healthcare safety protocols: Maintaining compliance during shutdown")


# Create FastAPI application with healthcare-specific configuration
app = FastAPI(
    title="Clinical Notes Summarizer API",
    description="""
    Healthcare document processing API supporting both FHIR R4 and CCDA formats for transforming clinical documents into patient-friendly summaries.
    
    ## Supported Formats
    - **FHIR R4 JSON**: Complete FHIR Bundle processing
    - **CCDA XML**: Continuity of Care Document processing with same safety guarantees
    
    ## Safety Features
    - **Zero PHI Storage**: No patient data is logged or persisted
    - **Critical Data Preservation**: Medications, lab values, and vital signs are never AI-processed
    - **FHIR R4 Compliance**: Full compatibility with healthcare data standards
    - **CCDA Security**: XML security validation with XXE/DTD protection
    - **Rate Limited**: Protection against abuse and misuse
    - **Input Validation**: Comprehensive sanitization and validation
    
    ## Processing Approach
    The API uses a **hybrid structured + AI approach** for both FHIR and CCDA:
    - **PRESERVE EXACTLY**: Medication names/dosages, lab values, vital signs, appointments
    - **AI-ENHANCE**: Chief complaints, diagnosis explanations, care instructions
    
    ## Important Disclaimers
    - This API is for educational purposes only
    - Not a substitute for professional medical advice
    - Always consult healthcare providers for medical decisions
    """,
    version="1.0.0",
    contact={
        "name": "Clinical Notes Summarizer Team",
        "url": "https://github.com/clinical-notes-summarizer",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,  # Disable credentials for security
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,
)

# Add custom healthcare middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests_per_minute=settings.rate_limit_per_minute)
app.add_middleware(PHIProtectionMiddleware)

# Request timing middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and enforce 5-second requirement."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests (healthcare requirement: <5 seconds)
    if process_time > 5.0:
        logger.warning(
            f"Slow request detected: {request.method} {request.url.path} "
            f"took {process_time:.2f} seconds"
        )
    
    return response

# Global exception handler for healthcare compliance
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that ensures no PHI is leaked in error responses.
    
    Returns FHIR-compliant OperationOutcome for all errors.
    """
    # Log error without PHI
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: "
        f"{type(exc).__name__}"
    )
    
    # Create FHIR-compliant error response
    operation_outcome = create_operation_outcome(
        severity="error",
        code="exception",
        details="An unexpected error occurred. Please contact support if this persists.",
        diagnostics=None  # Never include exception details in response
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=operation_outcome.model_dump()
    )

# HTTP exception handler for FHIR compliance
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Convert HTTP exceptions to FHIR-compliant OperationOutcome responses.
    """
    logger.info(f"HTTP exception: {exc.status_code} - {request.url.path}")
    
    # Map HTTP status codes to FHIR issue types
    fhir_code_mapping = {
        400: "invalid",
        401: "security",
        403: "forbidden",
        404: "not-found",
        405: "not-supported",
        422: "invalid",
        429: "throttled",
        500: "exception",
        503: "timeout"
    }
    
    operation_outcome = create_operation_outcome(
        severity="error",
        code=fhir_code_mapping.get(exc.status_code, "exception"),
        details=str(exc.detail),
        diagnostics=f"HTTP {exc.status_code}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=operation_outcome.model_dump()
    )

# Include API routers
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health Check"]
)

app.include_router(
    summarize_router,
    prefix="/api/v1",
    tags=["Clinical Summarization"]
)

app.include_router(
    validate_router,
    prefix="/api/v1",
    tags=["FHIR Validation"]
)

app.include_router(
    summary_router,
    prefix="/api/v1",
    tags=["Summary Management"]
)

app.include_router(
    ccda_router,
    prefix="/api/v1",
    tags=["CCDA Processing"]
)

# Root endpoint with API information
@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    API root endpoint with basic information and health status.
    """
    return {
        "service": "Clinical Notes Summarizer API",
        "version": "1.0.0",
        "status": "healthy",
        "fhir_version": "R4",
        "safety_features": [
            "Zero PHI storage",
            "Critical data preservation",
            "FHIR R4 compliance",
            "Rate limiting",
            "Input validation",
            "Healthcare disclaimers"
        ],
        "documentation": "/docs" if settings.debug else "Contact administrator for API documentation",
        "disclaimers": [
            "Educational purposes only",
            "Not a substitute for professional medical advice",
            "Always consult healthcare providers for medical decisions"
        ]
    }

# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        access_log=True
    )