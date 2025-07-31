"""
Configuration management for the Clinical Notes Summarizer API.

Handles environment-specific settings with healthcare compliance requirements.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with healthcare compliance defaults.
    
    All settings can be overridden via environment variables.
    """
    
    # API Configuration
    app_name: str = Field(default="Clinical Notes Summarizer API", description="Application name")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=True, description="Enable debug mode")
    
    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Host to bind the server")
    port: int = Field(default=8000, description="Port to bind the server")
    
    # Security Configuration
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0", "testserver"],
        description="Allowed host headers"
    )
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],
        description="CORS allowed origins"
    )
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Rate Limiting (Healthcare Security)
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP"
    )
    
    # Processing Configuration
    max_processing_time_seconds: float = Field(
        default=5.0,
        description="Maximum processing time for requests (healthcare requirement)"
    )
    max_request_size_mb: int = Field(
        default=10,
        description="Maximum request size in MB"
    )
    
    # Healthcare Compliance
    enable_phi_protection: bool = Field(
        default=True,
        description="Enable PHI protection middleware"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    enable_request_logging: bool = Field(
        default=False,
        description="Enable request logging (disabled for PHI protection)"
    )
    
    # FHIR Configuration
    fhir_version: str = Field(default="R4", description="FHIR version")
    fhir_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for FHIR server (if applicable)"
    )
    
    # Database Configuration (for summary storage if implemented)
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL for summary storage"
    )
    enable_summary_storage: bool = Field(
        default=False,
        description="Enable summary storage (requires proper PHI handling)"
    )
    
    # AI/ML Configuration
    model_cache_dir: Optional[str] = Field(
        default=None,
        description="Directory for caching AI models"
    )
    enable_ai_processing: bool = Field(
        default=False,
        description="Enable AI processing for narrative enhancement (not implemented yet)"
    )
    
    # Development Configuration
    reload_on_changes: bool = Field(
        default=True,
        description="Reload server on code changes (development only)"
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment values."""
        allowed_environments = ['development', 'staging', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @field_validator('debug')
    @classmethod
    def validate_debug_environment(cls, v, info):
        """Ensure debug is disabled in production."""
        environment = info.data.get('environment') if info.data else None
        if environment == 'production' and v:
            raise ValueError('Debug mode must be disabled in production')
        return v
    
    @field_validator('rate_limit_per_minute')
    @classmethod
    def validate_rate_limit(cls, v):
        """Ensure reasonable rate limiting for healthcare applications."""
        if v < 10:
            raise ValueError('Rate limit too restrictive for healthcare applications')
        if v > 1000:
            raise ValueError('Rate limit too permissive for security')
        return v
    
    @field_validator('max_processing_time_seconds')
    @classmethod
    def validate_processing_time(cls, v):
        """Ensure processing time meets healthcare requirements."""
        if v > 10.0:
            raise ValueError('Maximum processing time exceeds healthcare standards (10 seconds)')
        if v < 1.0:
            raise ValueError('Minimum processing time too restrictive')
        return v
    
    @field_validator('max_request_size_mb')
    @classmethod
    def validate_request_size(cls, v):
        """Validate request size limits."""
        if v > 100:
            raise ValueError('Request size limit too large for security')
        if v < 1:
            raise ValueError('Request size limit too small for clinical documents')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate logging level."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @field_validator('fhir_version')
    @classmethod
    def validate_fhir_version(cls, v):
        """Validate FHIR version."""
        allowed_versions = ['R4', 'R5']
        if v not in allowed_versions:
            raise ValueError(f'FHIR version must be one of: {allowed_versions}')
        return v
    
    def get_model_cache_path(self) -> Path:
        """Get the path for model caching."""
        if self.model_cache_dir:
            return Path(self.model_cache_dir)
        else:
            # Default to project cache directory
            project_root = Path(__file__).parent.parent.parent.parent
            return project_root / "cache" / "models"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration based on environment."""
        if self.is_production():
            return {
                "allow_origins": self.allowed_origins,
                "allow_credentials": False,
                "allow_methods": ["GET", "POST"],
                "allow_headers": ["Content-Type", "Authorization"],
                "max_age": 3600,
            }
        else:
            return {
                "allow_origins": ["*"],
                "allow_credentials": False,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
                "max_age": 3600,
            }
    
    def get_security_headers(self) -> dict:
        """Get security headers for healthcare compliance."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
        }
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "CLINICAL_",  # Environment variables prefixed with CLINICAL_
        "extra": "ignore"  # Ignore extra fields from .env file
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    This function uses LRU cache to ensure settings are loaded only once
    during the application lifecycle.
    """
    return Settings()


# Healthcare compliance validation
def validate_production_settings(settings: Settings) -> None:
    """
    Validate settings for production healthcare environments.
    
    Ensures all security and compliance requirements are met.
    """
    if not settings.is_production():
        return
    
    errors = []
    
    # Security validations
    if settings.debug:
        errors.append("Debug mode must be disabled in production")
    
    if not settings.enable_phi_protection:
        errors.append("PHI protection must be enabled in production")
    
    if settings.enable_request_logging:
        errors.append("Request logging must be disabled in production for PHI protection")
    
    if settings.rate_limit_per_minute > 300:
        errors.append("Rate limiting too permissive for production healthcare environment")
    
    if "localhost" in settings.allowed_hosts or "127.0.0.1" in settings.allowed_hosts:
        errors.append("Development hosts must be removed from production allowed_hosts")
    
    # Environment validations
    if not os.getenv("SECRET_KEY"):
        errors.append("SECRET_KEY environment variable must be set in production")
    
    if settings.database_url and settings.enable_summary_storage:
        if "localhost" in settings.database_url or "127.0.0.1" in settings.database_url:
            errors.append("Production database cannot use localhost addresses")
    
    if errors:
        raise ValueError(f"Production validation failed: {'; '.join(errors)}")


# Initialize settings on import for validation
_settings = get_settings()
if _settings.is_production():
    validate_production_settings(_settings)