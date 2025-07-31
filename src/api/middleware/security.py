"""
Security middleware for healthcare compliance.

Implements security headers and request validation for healthcare applications.
"""

from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from src.api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware that adds healthcare-compliant security headers
    and performs basic security validations.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers and perform security validations.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint to call
            
        Returns:
            HTTP response with security headers
        """
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                max_size = settings.max_request_size_mb * 1024 * 1024  # Convert MB to bytes
                
                if content_length > max_size:
                    logger.warning(f"Request size {content_length} exceeds limit {max_size}")
                    return JSONResponse(
                        status_code=413,
                        content={
                            "resourceType": "OperationOutcome",
                            "issue": [{
                                "severity": "error",
                                "code": "too-long",
                                "details": {
                                    "text": f"Request size exceeds maximum limit of {settings.max_request_size_mb}MB"
                                }
                            }]
                        }
                    )
            except ValueError:
                logger.warning("Invalid content-length header")
        
        # Validate content type for POST requests
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                logger.warning(f"Invalid content type: {content_type}")
                return JSONResponse(
                    status_code=415,
                    content={
                        "resourceType": "OperationOutcome",
                        "issue": [{
                            "severity": "error",
                            "code": "not-supported",
                            "details": {
                                "text": "Content-Type must be application/json"
                            }
                        }]
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        security_headers = settings.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add custom healthcare compliance headers
        response.headers["X-Healthcare-API"] = "Clinical-Notes-Summarizer"
        response.headers["X-FHIR-Version"] = settings.fhir_version
        response.headers["X-PHI-Protected"] = "true"
        
        return response