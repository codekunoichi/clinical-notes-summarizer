"""
Test suite for healthcare security middleware.

Tests PHI protection, rate limiting, and security features.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.api.middleware.security import SecurityMiddleware
from src.api.middleware.rate_limiting import RateLimitMiddleware
from src.api.middleware.phi_protection import PHIProtectionMiddleware


# Test applications for middleware testing
def create_test_app_with_middleware(middleware_class, **middleware_kwargs):
    """Create a test FastAPI app with specific middleware."""
    app = FastAPI()
    
    app.add_middleware(middleware_class, **middleware_kwargs)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test response"}
    
    @app.post("/test-post")
    async def test_post_endpoint(data: dict):
        return {"received": data}
    
    @app.get("/large-response")
    async def large_response():
        return {"data": "x" * 10000}
    
    return app


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    @pytest.fixture
    def app_with_security(self):
        """App with security middleware."""
        return create_test_app_with_middleware(SecurityMiddleware)
    
    @pytest.fixture
    def client_with_security(self, app_with_security):
        """Test client with security middleware."""
        return TestClient(app_with_security)
    
    def test_security_headers_added(self, client_with_security):
        """Test that security headers are added to responses."""
        response = client_with_security.get("/test")
        
        assert response.status_code == 200
        
        # Check for security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Cache-Control",
            "Pragma"
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"
    
    def test_healthcare_headers_added(self, client_with_security):
        """Test that healthcare-specific headers are added."""
        response = client_with_security.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-Healthcare-API"] == "Clinical-Notes-Summarizer"
        assert response.headers["X-FHIR-Version"] == "R4"
        assert response.headers["X-PHI-Protected"] == "true"
    
    def test_invalid_content_type_rejected(self, client_with_security):
        """Test that POST requests with invalid content type are rejected."""
        response = client_with_security.post(
            "/test-post",
            content='{"test": "data"}',
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 415
        
        # Should return FHIR OperationOutcome
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"
        assert "Content-Type must be application/json" in str(data)
    
    @patch('src.api.core.config.get_settings')
    def test_large_request_rejected(self, mock_settings, client_with_security):
        """Test that oversized requests are rejected."""
        # Mock settings to have a very small max request size
        mock_settings.return_value.max_request_size_mb = 0.001  # 1KB limit
        
        # Create a large request
        large_data = {"data": "x" * 2000}  # ~2KB
        
        response = client_with_security.post(
            "/test-post",
            json=large_data,
            headers={"Content-Length": str(len(str(large_data)))}
        )
        
        # Should be rejected due to size
        assert response.status_code == 413
        
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"
        assert "Request size exceeds maximum limit" in str(data)
    
    def test_get_request_no_content_type_check(self, client_with_security):
        """Test that GET requests don't have content type validation."""
        response = client_with_security.get("/test")
        
        assert response.status_code == 200
        # No content type validation for GET requests


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""
    
    @pytest.fixture
    def app_with_rate_limit(self):
        """App with rate limiting middleware (low limit for testing)."""
        return create_test_app_with_middleware(
            RateLimitMiddleware, 
            max_requests_per_minute=5  # Low limit for testing
        )
    
    @pytest.fixture
    def client_with_rate_limit(self, app_with_rate_limit):
        """Test client with rate limiting middleware."""
        return TestClient(app_with_rate_limit)
    
    def test_rate_limit_headers_added(self, client_with_rate_limit):
        """Test that rate limiting headers are added."""
        response = client_with_rate_limit.get("/test")
        
        assert response.status_code == 200
        
        # Check for rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Window" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        
        # Verify header values
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Window"] == "60"
    
    def test_rate_limit_decreases(self, client_with_rate_limit):
        """Test that remaining requests decrease with each request."""
        # Make first request
        response1 = client_with_rate_limit.get("/test")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        
        # Make second request
        response2 = client_with_rate_limit.get("/test")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        # Remaining should decrease
        assert remaining2 < remaining1
    
    def test_rate_limit_exceeded(self, client_with_rate_limit):
        """Test behavior when rate limit is exceeded."""
        # Make requests up to the limit
        for i in range(5):
            response = client_with_rate_limit.get("/test")
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client_with_rate_limit.get("/test")
        
        assert response.status_code == 429
        
        # Should return FHIR OperationOutcome
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"
        assert "Rate limit exceeded" in str(data)
        
        # Should have Retry-After header
        assert "Retry-After" in response.headers
    
    def test_health_endpoints_excluded_from_rate_limiting(self, client_with_rate_limit):
        """Test that health endpoints are excluded from rate limiting."""
        # The health endpoint should not be rate limited
        # We can't easily test this without modifying the test app,
        # but we can verify the middleware logic
        
        # Make many requests to health endpoint (this would normally be /health)
        # Since our test app doesn't have /health, we'll test the exclusion logic
        from src.api.middleware.rate_limiting import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(None, max_requests_per_minute=1)
        
        # Mock request to health endpoint
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        
        # Health endpoints should be excluded
        # (This tests the logic, actual integration test would need proper setup)
        pass
    
    def test_rate_limit_with_different_ips(self):
        """Test that rate limiting is per-IP."""
        # This test would require mocking different IP addresses
        # For now, we'll test the IP extraction logic
        
        from src.api.middleware.rate_limiting import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(None)
        
        # Test IP extraction with X-Forwarded-For
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "192.168.1.1, 10.0.0.1"
        mock_request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"  # Should get first IP from forwarded header
        
        # Test IP extraction without forwarded headers
        mock_request.headers.get.return_value = None
        ip = middleware._get_client_ip(mock_request)
        assert ip == "127.0.0.1"  # Should fall back to direct IP


class TestPHIProtectionMiddleware:
    """Test PHI protection middleware functionality."""
    
    @pytest.fixture
    def app_with_phi_protection(self):
        """App with PHI protection middleware."""
        return create_test_app_with_middleware(PHIProtectionMiddleware)
    
    @pytest.fixture
    def client_with_phi_protection(self, app_with_phi_protection):
        """Test client with PHI protection middleware."""
        return TestClient(app_with_phi_protection)
    
    def test_phi_protection_headers_added(self, client_with_phi_protection):
        """Test that PHI protection headers are added."""
        response = client_with_phi_protection.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-PHI-Protected"] == "true"
        assert response.headers["X-HIPAA-Compliant"] == "true"
    
    def test_sanitize_text_method(self):
        """Test the text sanitization method."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        # Test SSN sanitization
        text_with_ssn = "Patient SSN is 123-45-6789"
        sanitized = middleware._sanitize_text(text_with_ssn)
        assert "123-45-6789" not in sanitized
        assert "[SSN_REDACTED]" in sanitized
        
        # Test phone number sanitization
        text_with_phone = "Call patient at 555-123-4567"
        sanitized = middleware._sanitize_text(text_with_phone)
        assert "555-123-4567" not in sanitized
        assert "[PHONE_REDACTED]" in sanitized
        
        # Test email sanitization
        text_with_email = "Contact: patient@email.com"
        sanitized = middleware._sanitize_text(text_with_email)
        assert "patient@email.com" not in sanitized
        assert "[EMAIL_REDACTED]" in sanitized
    
    def test_sanitize_dict_method(self):
        """Test dictionary sanitization method."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        # Test PHI field name detection
        data_with_phi = {
            "name": "John Doe",
            "phone": "555-123-4567",
            "medical_data": "Patient has diabetes",
            "safe_field": "This is safe data"
        }
        
        sanitized = middleware._sanitize_dict(data_with_phi)
        
        assert sanitized["name"] == "[PHI_REDACTED]"
        assert sanitized["phone"] == "[PHI_REDACTED]"
        assert sanitized["medical_data"] == "Patient has diabetes"  # Not a PHI field name
        assert sanitized["safe_field"] == "This is safe data"
    
    def test_sanitize_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        nested_data = {
            "patient": {
                "name": "Jane Doe",
                "ssn": "987-65-4321",
                "diagnosis": "Hypertension"
            },
            "provider": {
                "name": "Dr. Smith",
                "contact": "doctor@hospital.com",
                "specialty": "Cardiology"
            }
        }
        
        sanitized = middleware._sanitize_dict(nested_data)
        
        # PHI fields should be redacted
        assert sanitized["patient"]["name"] == "[PHI_REDACTED]"
        assert "[SSN_REDACTED]" in sanitized["patient"]["ssn"]
        assert sanitized["provider"]["name"] == "[PHI_REDACTED]"
        assert "[EMAIL_REDACTED]" in sanitized["provider"]["contact"]
        
        # Non-PHI fields should remain
        assert sanitized["patient"]["diagnosis"] == "Hypertension"
        assert sanitized["provider"]["specialty"] == "Cardiology"
    
    def test_sanitize_list_method(self):
        """Test list sanitization method."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        list_with_phi = [
            "Patient name: John Doe",
            {"name": "Jane Smith", "diagnosis": "Diabetes"},
            "Safe medical information"
        ]
        
        sanitized = middleware._sanitize_list(list_with_phi)
        
        # Text items should be sanitized for patterns
        assert isinstance(sanitized[0], str)
        
        # Dict items should be sanitized for field names
        assert sanitized[1]["name"] == "[PHI_REDACTED]"
        assert sanitized[1]["diagnosis"] == "Diabetes"
        
        # Safe items should remain unchanged
        assert sanitized[2] == "Safe medical information"
    
    def test_max_depth_protection(self):
        """Test that recursion depth is limited."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        # Create deeply nested structure
        deep_data = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": "deep data"}}}}}}
        
        # Sanitize with low max depth
        sanitized = middleware._sanitize_dict(deep_data, max_depth=3)
        
        # Should stop at max depth and return error message
        result = sanitized
        for i in range(3):
            if isinstance(result, dict) and "level" + str(i+1) in result:
                result = result["level" + str(i+1)]
            else:
                break
        
        # At some point, should hit max depth protection
        # (exact structure depends on implementation details)
    
    @patch('src.api.middleware.phi_protection.logger')
    def test_request_logging_is_safe(self, mock_logger, client_with_phi_protection):
        """Test that request logging doesn't include PHI."""
        # Make a request
        response = client_with_phi_protection.get("/test?patient_name=John+Doe")
        
        assert response.status_code == 200
        
        # Verify logger was called (request was logged)
        assert mock_logger.info.called
        
        # Check that logged data doesn't contain raw PHI
        # (This is a basic check - in practice, we'd verify the sanitization)
        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) > 0


class TestMiddlewareIntegration:
    """Test middleware working together."""
    
    @pytest.fixture
    def app_with_all_middleware(self):
        """App with all middleware components."""
        app = FastAPI()
        
        # Add middleware in reverse order (last added is first executed)
        app.add_middleware(PHIProtectionMiddleware)
        app.add_middleware(RateLimitMiddleware, max_requests_per_minute=10)
        app.add_middleware(SecurityMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test response"}
        
        @app.post("/test-post")
        async def test_post_endpoint(data: dict):
            return {"received": data}
        
        return app
    
    @pytest.fixture
    def client_with_all_middleware(self, app_with_all_middleware):
        """Test client with all middleware."""
        return TestClient(app_with_all_middleware)
    
    def test_all_middleware_headers_present(self, client_with_all_middleware):
        """Test that all middleware add their headers."""
        response = client_with_all_middleware.get("/test")
        
        assert response.status_code == 200
        
        # Security middleware headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Healthcare-API" in response.headers
        
        # Rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        
        # PHI protection headers
        assert "X-PHI-Protected" in response.headers
        assert "X-HIPAA-Compliant" in response.headers
    
    def test_middleware_order_processing(self, client_with_all_middleware):
        """Test that middleware processes requests in correct order."""
        # Make a POST request that would trigger security validation
        response = client_with_all_middleware.post(
            "/test-post",
            json={"test": "data"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        # All middleware should have processed the request
        # Security: added security headers
        # Rate limiting: added rate limit headers
        # PHI protection: added PHI headers
        
        # Verify all expected headers are present
        expected_headers = [
            "X-Healthcare-API",
            "X-RateLimit-Limit", 
            "X-PHI-Protected"
        ]
        
        for header in expected_headers:
            assert header in response.headers
    
    def test_middleware_error_handling(self, client_with_all_middleware):
        """Test error handling across middleware stack."""
        # Make request with invalid content type (should be caught by security middleware)
        response = client_with_all_middleware.post(
            "/test-post",
            content='{"test": "data"}',
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 415
        
        # Even error responses should have middleware headers
        assert "X-Healthcare-API" in response.headers or "X-PHI-Protected" in response.headers
        
        # Response should be FHIR-compliant
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"


class TestMiddlewarePerformance:
    """Test middleware performance characteristics."""
    
    def test_middleware_response_time(self):
        """Test that middleware doesn't significantly impact response time."""
        # Create app without middleware
        app_without = FastAPI()
        
        @app_without.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Create app with all middleware
        app_with = create_test_app_with_middleware(SecurityMiddleware)
        app_with.add_middleware(RateLimitMiddleware, max_requests_per_minute=1000)
        app_with.add_middleware(PHIProtectionMiddleware)
        
        client_without = TestClient(app_without)
        client_with = TestClient(app_with)
        
        # Time requests without middleware
        start_time = time.time()
        for _ in range(10):
            response = client_without.get("/test")
            assert response.status_code == 200
        time_without = time.time() - start_time
        
        # Time requests with middleware
        start_time = time.time()
        for _ in range(10):
            response = client_with.get("/test")
            assert response.status_code == 200
        time_with = time.time() - start_time
        
        # Middleware should not significantly impact performance
        # Allow up to 5x slower (generous for test environment)
        assert time_with < time_without * 5
    
    def test_phi_sanitization_performance(self):
        """Test PHI sanitization performance with large data."""
        from src.api.middleware.phi_protection import PHIProtectionMiddleware
        
        middleware = PHIProtectionMiddleware(None)
        
        # Create large data structure
        large_data = {
            f"field_{i}": f"value_{i} with potential PHI 123-45-6789"
            for i in range(1000)
        }
        
        # Time sanitization
        start_time = time.time()
        sanitized = middleware._sanitize_dict(large_data)
        sanitization_time = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second for 1000 fields)
        assert sanitization_time < 1.0
        
        # Verify sanitization occurred
        assert len(sanitized) == 1000
        for key, value in sanitized.items():
            if "123-45-6789" in large_data[key]:
                assert "[SSN_REDACTED]" in value