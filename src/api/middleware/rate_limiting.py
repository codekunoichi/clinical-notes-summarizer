"""
Rate limiting middleware for healthcare API protection.

Implements intelligent rate limiting to prevent abuse while allowing
legitimate healthcare applications to function properly.
"""

from typing import Callable, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with sliding window implementation.
    
    Provides per-IP rate limiting with healthcare-appropriate limits
    and graceful handling of rate limit violations.
    """
    
    def __init__(self, app, max_requests_per_minute: int = 60):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            max_requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.window_seconds = 60  # 1 minute sliding window
        
        logger.info(f"Rate limiting initialized: {max_requests_per_minute} requests/minute")
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address with support for proxies.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Check forwarded headers (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, request_times: deque, current_time: float) -> None:
        """
        Remove requests older than the sliding window.
        
        Args:
            request_times: Deque of request timestamps for a client
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_seconds
        
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """
        Check if client is rate limited.
        
        Args:
            client_ip: Client IP address
            current_time: Current timestamp
            
        Returns:
            True if client is rate limited
        """
        request_times = self.requests[client_ip]
        
        # Clean old requests
        self._clean_old_requests(request_times, current_time)
        
        # Check if at limit
        if len(request_times) >= self.max_requests_per_minute:
            return True
        
        # Add current request
        request_times.append(current_time)
        return False
    
    def _create_rate_limit_response(self, client_ip: str, retry_after: int) -> JSONResponse:
        """
        Create FHIR-compliant rate limit response.
        
        Args:
            client_ip: Client IP (for logging only, not included in response)
            retry_after: Seconds until client can retry
            
        Returns:
            FHIR OperationOutcome response
        """
        logger.warning(f"Rate limit exceeded for IP: {client_ip[:8]}...")  # Partial IP for privacy
        
        return JSONResponse(
            status_code=429,
            content={
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "throttled",
                    "details": {
                        "text": f"Rate limit exceeded. Maximum {self.max_requests_per_minute} requests per minute allowed."
                    },
                    "diagnostics": f"Please retry after {retry_after} seconds"
                }]
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.max_requests_per_minute),
                "X-RateLimit-Window": str(self.window_seconds),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str, current_time: float) -> None:
        """
        Add rate limit information headers to response.
        
        Args:
            response: HTTP response
            client_ip: Client IP address
            current_time: Current timestamp
        """
        request_times = self.requests[client_ip]
        self._clean_old_requests(request_times, current_time)
        
        remaining = max(0, self.max_requests_per_minute - len(request_times))
        
        response.headers["X-RateLimit-Limit"] = str(self.max_requests_per_minute)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        # Add reset time if applicable
        if request_times:
            reset_time = int(request_times[0] + self.window_seconds)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting to incoming requests.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint to call
            
        Returns:
            HTTP response with rate limiting applied
        """
        # Skip rate limiting for health checks and static content
        if request.url.path in ["/", "/health", "/api/v1/health"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            # Calculate retry after time
            request_times = self.requests[client_ip]
            if request_times:
                oldest_request = request_times[0]
                retry_after = max(1, int(oldest_request + self.window_seconds - current_time))
            else:
                retry_after = self.window_seconds
            
            return self._create_rate_limit_response(client_ip, retry_after)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        self._add_rate_limit_headers(response, client_ip, current_time)
        
        return response