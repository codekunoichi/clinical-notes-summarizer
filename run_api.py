#!/usr/bin/env python3
"""
Clinical Notes Summarizer API Server Launcher

This script starts the FastAPI server with healthcare-compliant configuration.
"""

import uvicorn
import logging
from src.api.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the Clinical Notes Summarizer API server."""
    settings = get_settings()
    
    logger.info("Starting Clinical Notes Summarizer API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"FHIR Version: {settings.fhir_version}")
    logger.info("Healthcare safety protocols: ENABLED")
    
    # Production safety check
    if settings.is_production():
        logger.info("Production mode: Enhanced security enabled")
        if settings.debug:
            logger.error("SECURITY WARNING: Debug mode should be disabled in production!")
            return
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug and not settings.is_production(),
        log_level="info",
        access_log=not settings.is_production(),  # Disable access logs in production for PHI protection
        server_header=False,  # Don't reveal server details
        date_header=False,    # Don't add date headers
    )

if __name__ == "__main__":
    main()