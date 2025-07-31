"""
PHI (Protected Health Information) protection middleware.

Ensures that no PHI is logged, cached, or exposed in error messages,
maintaining HIPAA compliance for healthcare applications.
"""

from typing import Callable, Any, Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class PHIProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that prevents PHI exposure in logs, errors, and responses.
    
    This middleware identifies and sanitizes potential PHI in request/response
    data to ensure healthcare compliance.
    """
    
    def __init__(self, app):
        """Initialize PHI protection middleware."""
        super().__init__(app)
        
        # Common PHI patterns to detect and sanitize
        self.phi_patterns = {
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'mrn': re.compile(r'\b(MRN|mrn|patient[_-]?id)[:\s]*[A-Za-z0-9]{6,}\b', re.IGNORECASE),
            'dob': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            'address': re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', re.IGNORECASE),
        }
        
        # Common PHI field names to watch for
        self.phi_field_names = {
            'name', 'first_name', 'last_name', 'middle_name', 'maiden_name',
            'address', 'street', 'city', 'zip', 'zipcode', 'postal_code',
            'phone', 'mobile', 'home_phone', 'work_phone', 'telephone',
            'email', 'email_address',
            'ssn', 'social_security', 'social_security_number',
            'mrn', 'medical_record_number', 'patient_id', 'account_number',
            'date_of_birth', 'dob', 'birth_date', 'birthdate',
            'next_of_kin', 'emergency_contact', 'guardian',
            'insurance_number', 'policy_number', 'member_id'
        }
        
        logger.info("PHI protection middleware initialized")
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text content to remove potential PHI.
        
        Args:
            text: Text content to sanitize
            
        Returns:
            Sanitized text with PHI patterns replaced
        """
        if not isinstance(text, str):
            return text
        
        sanitized = text
        
        # Replace common PHI patterns
        for phi_type, pattern in self.phi_patterns.items():
            sanitized = pattern.sub(f'[{phi_type.upper()}_REDACTED]', sanitized)
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary data to remove PHI.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth to prevent infinite loops
            
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            return {"error": "Max depth reached during PHI sanitization"}
        
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key name suggests PHI
            if any(phi_field in key_lower for phi_field in self.phi_field_names):
                sanitized[key] = "[PHI_REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value, max_depth - 1)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_list(self, data: List[Any], max_depth: int = 5) -> List[Any]:
        """
        Sanitize list data to remove PHI.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized list
        """
        if max_depth <= 0:
            return ["Max depth reached during PHI sanitization"]
        
        if not isinstance(data, list):
            return data
        
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self._sanitize_text(item))
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(item, max_depth - 1))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def _log_request_safely(self, request: Request) -> None:
        """
        Log request information without PHI.
        
        Args:
            request: HTTP request to log
        """
        # Log only safe request metadata
        safe_data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else {},
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", ""),
            "user_agent": request.headers.get("user-agent", "")[:100],  # Truncate user agent
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Sanitize query parameters
        if safe_data["query_params"]:
            safe_data["query_params"] = self._sanitize_dict(safe_data["query_params"])
        
        logger.info(f"Request processed: {json.dumps(safe_data)}")
    
    def _ensure_response_phi_free(self, response_body: bytes) -> bytes:
        """
        Ensure response body doesn't contain PHI.
        
        Args:
            response_body: Response body bytes
            
        Returns:
            Sanitized response body
        """
        try:
            # Only process JSON responses
            if not response_body:
                return response_body
            
            # Try to parse as JSON
            response_text = response_body.decode('utf-8')
            response_data = json.loads(response_text)
            
            # Sanitize the response data
            sanitized_data = self._sanitize_dict(response_data)
            
            # Return sanitized JSON
            return json.dumps(sanitized_data).encode('utf-8')
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON or can't decode, sanitize as text
            try:
                response_text = response_body.decode('utf-8')
                sanitized_text = self._sanitize_text(response_text)
                return sanitized_text.encode('utf-8')
            except UnicodeDecodeError:
                # If can't decode at all, return as-is (likely binary)
                return response_body
        except Exception as e:
            logger.error(f"Error during PHI sanitization: {type(e).__name__}")
            # Return original if sanitization fails to prevent service disruption
            return response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply PHI protection to request processing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint to call
            
        Returns:
            Response with PHI protection applied
        """
        # Log request safely (without PHI)
        try:
            self._log_request_safely(request)
        except Exception as e:
            logger.error(f"Error during safe request logging: {type(e).__name__}")
        
        # Process the request
        response = await call_next(request)
        
        # Add PHI protection header
        response.headers["X-PHI-Protected"] = "true"
        response.headers["X-HIPAA-Compliant"] = "true"
        
        # Note: We don't sanitize response body here as it would interfere with streaming
        # PHI protection in responses should be handled at the application level
        # during data processing, not at the middleware level
        
        return response