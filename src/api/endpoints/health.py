"""
Health check endpoint for system monitoring and status verification.

Provides comprehensive health information for healthcare compliance monitoring.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging
import time
import psutil
import sys
from typing import Dict, Any

from src.api.models.fhir_models import HealthCheckResponse
from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _check_core_components() -> Dict[str, str]:
    """
    Check the health of core application components.
    
    Returns:
        Dictionary with component health status
    """
    components = {}
    
    # Check hybrid processor
    try:
        from src.summarizer.hybrid_processor import HybridClinicalProcessor
        processor = HybridClinicalProcessor()
        components["hybrid_processor"] = "healthy"
    except Exception as e:
        logger.error(f"Hybrid processor health check failed: {e}")
        components["hybrid_processor"] = "unhealthy"
    
    # Check FHIR parser
    try:
        from src.summarizer.fhir_parser import FHIRMedicationParser
        parser = FHIRMedicationParser()
        components["fhir_parser"] = "healthy"
    except Exception as e:
        logger.error(f"FHIR parser health check failed: {e}")
        components["fhir_parser"] = "unhealthy"
    
    # Check API models
    try:
        from src.api.models.fhir_models import OperationOutcome, FHIRBundle
        # Try to create a simple model instance
        outcome = OperationOutcome(issue=[])
        components["api_models"] = "healthy"
    except Exception as e:
        logger.error(f"API models health check failed: {e}")
        components["api_models"] = "unhealthy"
    
    # Check clinical models
    try:
        from src.models.clinical import ClinicalSummary, ProcessingMetadata, SafetyValidation
        from src.models.medication import MedicationRequest
        components["clinical_models"] = "healthy"
    except Exception as e:
        logger.error(f"Clinical models health check failed: {e}")
        components["clinical_models"] = "unhealthy"
    
    return components


def _get_performance_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics for monitoring.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        # System memory usage
        memory = psutil.virtual_memory()
        
        # System CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage for the current directory
        disk = psutil.disk_usage('/')
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "system_memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "system_cpu": {
                "percent_used": cpu_percent,
                "count": psutil.cpu_count()
            },
            "system_disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 2)
            },
            "process_memory": {
                "rss_mb": round(process_memory.rss / (1024**2), 2),
                "vms_mb": round(process_memory.vms / (1024**2), 2)
            },
            "python_version": sys.version,
            "uptime_seconds": time.time() - psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Error collecting performance metrics: {e}")
        return {
            "error": "Unable to collect performance metrics",
            "python_version": sys.version
        }


def _check_safety_requirements() -> Dict[str, bool]:
    """
    Validate healthcare safety requirements are met.
    
    Returns:
        Dictionary with safety check results
    """
    safety_checks = {}
    
    # Check if PHI protection is enabled
    safety_checks["phi_protection_enabled"] = settings.enable_phi_protection
    
    # Check if debug is disabled in production
    if settings.is_production():
        safety_checks["debug_disabled_in_prod"] = not settings.debug
        safety_checks["request_logging_disabled"] = not settings.enable_request_logging
    else:
        safety_checks["debug_disabled_in_prod"] = True  # N/A in non-prod
        safety_checks["request_logging_disabled"] = True  # N/A in non-prod
    
    # Check rate limiting
    safety_checks["rate_limiting_enabled"] = settings.rate_limit_per_minute > 0
    
    # Check processing time limits
    safety_checks["processing_time_limited"] = settings.max_processing_time_seconds <= 10.0
    
    # Check request size limits
    safety_checks["request_size_limited"] = settings.max_request_size_mb <= 50
    
    # Check FHIR compliance
    safety_checks["fhir_r4_support"] = settings.fhir_version == "R4"
    
    return safety_checks


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Comprehensive health check endpoint for system monitoring.
    
    Returns detailed health information including:
    - Overall system status
    - Component health status
    - Performance metrics
    - Healthcare safety compliance checks
    
    This endpoint is essential for healthcare applications to ensure
    system reliability and compliance monitoring.
    """
    start_time = time.time()
    
    try:
        # Check core components
        components = _check_core_components()
        
        # Get performance metrics
        performance_metrics = _get_performance_metrics()
        
        # Check safety requirements
        safety_checks = _check_safety_requirements()
        
        # Determine overall status
        unhealthy_components = [name for name, status in components.items() if status != "healthy"]
        failed_safety_checks = [name for name, passed in safety_checks.items() if not passed]
        
        if unhealthy_components:
            overall_status = "unhealthy"
            logger.warning(f"Unhealthy components detected: {unhealthy_components}")
        elif failed_safety_checks:
            overall_status = "degraded"
            logger.warning(f"Safety checks failed: {failed_safety_checks}")
        else:
            overall_status = "healthy"
        
        # Add response time to performance metrics
        response_time = time.time() - start_time
        performance_metrics["health_check_response_time_ms"] = round(response_time * 1000, 2)
        
        # Log health check (safe for PHI compliance)
        logger.info(f"Health check completed: status={overall_status}, components={len(components)}, response_time={response_time:.3f}s")
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            fhir_version=settings.fhir_version,
            components=components,
            performance_metrics=performance_metrics,
            safety_checks=safety_checks
        )
    
    except Exception as e:
        logger.error(f"Health check failed with error: {type(e).__name__}")
        
        # Return minimal health response on error
        return HealthCheckResponse(
            status="error",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            fhir_version=settings.fhir_version,
            components={"health_check": "failed"},
            performance_metrics={"error": "Unable to collect metrics"},
            safety_checks={"health_check_functional": False}
        )


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if the service is ready to handle requests,
    503 if not ready.
    """
    try:
        # Quick check of essential components
        from src.summarizer.hybrid_processor import HybridClinicalProcessor
        from src.summarizer.fhir_parser import FHIRMedicationParser
        
        # Try to instantiate core components
        processor = HybridClinicalProcessor()
        parser = FHIRMedicationParser()
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    
    except Exception as e:
        logger.error(f"Readiness check failed: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the service is alive and functioning,
    500 if the service should be restarted.
    """
    try:
        # Basic liveness check - ensure we can respond
        current_time = datetime.utcnow()
        
        # Check if we can access basic Python functionality
        test_dict = {"test": "value"}
        test_list = [1, 2, 3]
        
        return {
            "status": "alive",
            "timestamp": current_time.isoformat(),
            "uptime_check": "passed"
        }
    
    except Exception as e:
        logger.error(f"Liveness check failed: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service not alive"
        )


@router.get("/health/startup")
async def startup_check():
    """
    Container startup probe for healthcare environments.
    
    Validates that all critical healthcare components are properly initialized
    before the container is marked as ready to receive traffic.
    
    Returns 200 when all startup requirements are met, 503 otherwise.
    """
    try:
        startup_checks = {}
        
        # Check core processing components
        try:
            from src.summarizer.hybrid_processor import HybridClinicalProcessor
            processor = HybridClinicalProcessor()
            startup_checks["hybrid_processor"] = "initialized"
        except Exception as e:
            logger.error(f"Hybrid processor startup failed: {type(e).__name__}")
            startup_checks["hybrid_processor"] = "failed"
        
        # Check FHIR parser
        try:
            from src.summarizer.fhir_parser import FHIRMedicationParser
            parser = FHIRMedicationParser()
            startup_checks["fhir_parser"] = "initialized"
        except Exception as e:
            logger.error(f"FHIR parser startup failed: {type(e).__name__}")
            startup_checks["fhir_parser"] = "failed"
        
        # Check patient formatter
        try:
            from src.formatter.patient_friendly import PatientFriendlyFormatter
            formatter = PatientFriendlyFormatter()
            startup_checks["patient_formatter"] = "initialized"
        except Exception as e:
            logger.error(f"Patient formatter startup failed: {type(e).__name__}")
            startup_checks["patient_formatter"] = "failed"
        
        # Check API models
        try:
            from src.api.models.fhir_models import OperationOutcome, FHIRBundle
            startup_checks["api_models"] = "initialized"
        except Exception as e:
            logger.error(f"API models startup failed: {type(e).__name__}")
            startup_checks["api_models"] = "failed"
        
        # Check healthcare safety requirements
        safety_requirements = _check_safety_requirements()
        failed_safety = [name for name, passed in safety_requirements.items() if not passed]
        
        if failed_safety:
            startup_checks["safety_requirements"] = f"failed: {failed_safety}"
        else:
            startup_checks["safety_requirements"] = "validated"
        
        # Determine if startup is successful
        failed_components = [name for name, status in startup_checks.items() 
                           if status not in ["initialized", "validated"]]
        
        if failed_components:
            logger.error(f"Startup check failed: {failed_components}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "startup_failed",
                    "failed_components": failed_components,
                    "checks": startup_checks,
                    "message": "Service not ready for healthcare operations"
                }
            )
        
        return {
            "status": "startup_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "components": startup_checks,
            "healthcare_compliance": "validated",
            "ready_for_traffic": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Startup validation failed"
        )


@router.get("/health/dependencies")
async def dependencies_check():
    """
    Check external dependencies and integrations for healthcare operations.
    
    Validates connectivity and functionality of external systems required
    for healthcare data processing.
    """
    try:
        dependencies = {}
        
        # Check AI/ML model availability
        try:
            from transformers import pipeline
            # Test BART model loading (used for narrative enhancement)
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            dependencies["bart_model"] = "available"
        except Exception as e:
            logger.warning(f"BART model check failed: {type(e).__name__}")
            dependencies["bart_model"] = "unavailable"
        
        # Check FHIR resources library
        try:
            from fhir.resources.bundle import Bundle
            from fhir.resources.patient import Patient
            dependencies["fhir_resources"] = "available"
        except Exception as e:
            logger.error(f"FHIR resources check failed: {type(e).__name__}")
            dependencies["fhir_resources"] = "unavailable"
        
        # Check clinical data processing libraries
        try:
            import textstat
            import dateutil.parser
            dependencies["clinical_processing"] = "available"
        except Exception as e:
            logger.error(f"Clinical processing libraries check failed: {type(e).__name__}")
            dependencies["clinical_processing"] = "unavailable"
        
        # Check system resources for healthcare workloads
        try:
            memory = psutil.virtual_memory()
            if memory.available < (1024**3):  # Less than 1GB available
                dependencies["system_memory"] = "insufficient"
            else:
                dependencies["system_memory"] = "sufficient"
        except Exception as e:
            logger.error(f"System resources check failed: {type(e).__name__}")
            dependencies["system_memory"] = "unknown"
        
        # Determine overall dependency status
        critical_deps = ["fhir_resources", "clinical_processing", "system_memory"]
        failed_critical = [name for name in critical_deps 
                          if dependencies.get(name) not in ["available", "sufficient"]]
        
        if failed_critical:
            overall_status = "degraded"
            logger.warning(f"Critical dependencies failed: {failed_critical}")
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": dependencies,
            "critical_failures": failed_critical,
            "healthcare_ready": len(failed_critical) == 0
        }
    
    except Exception as e:
        logger.error(f"Dependencies check failed: {type(e).__name__}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {"check": "failed"},
            "healthcare_ready": False
        }