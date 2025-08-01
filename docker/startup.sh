#!/bin/bash

# Clinical Notes Summarizer - Healthcare-Compliant Container Startup Script
# Performs comprehensive safety checks before starting the application

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Healthcare compliance logging
log_info() {
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [STARTUP-INFO] $1"
}

log_warn() {
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [STARTUP-WARN] $1" >&2
}

log_error() {
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [STARTUP-ERROR] $1" >&2
}

log_security() {
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") [STARTUP-SECURITY] $1"
}

# Healthcare startup banner
display_healthcare_banner() {
    log_info "=============================================================="
    log_info "Clinical Notes Summarizer - Healthcare Deployment Starting"
    log_info "=============================================================="
    log_info "FHIR Version: ${CLINICAL_FHIR_VERSION:-R4}"
    log_info "Environment: ${CLINICAL_ENVIRONMENT:-production}"
    log_info "PHI Protection: ${CLINICAL_ENABLE_PHI_PROTECTION:-true}"
    log_info "Debug Mode: ${CLINICAL_DEBUG:-false}"
    log_info "Healthcare Compliance: ACTIVE"
    log_info "=============================================================="
}

# Validate healthcare environment variables
validate_healthcare_environment() {
    log_info "Validating healthcare environment configuration..."
    
    local validation_errors=0
    
    # Critical healthcare settings validation
    if [[ "${CLINICAL_ENABLE_PHI_PROTECTION:-}" != "true" ]]; then
        log_error "CRITICAL: PHI protection must be enabled for healthcare compliance"
        ((validation_errors++))
    fi
    
    if [[ "${CLINICAL_ENVIRONMENT:-}" == "production" && "${CLINICAL_DEBUG:-}" == "true" ]]; then
        log_error "CRITICAL: Debug mode must be disabled in production"
        ((validation_errors++))
    fi
    
    if [[ "${CLINICAL_ENVIRONMENT:-}" == "production" && "${CLINICAL_ENABLE_REQUEST_LOGGING:-}" == "true" ]]; then
        log_error "CRITICAL: Request logging must be disabled in production for PHI protection"
        ((validation_errors++))
    fi
    
    # FHIR compliance validation
    if [[ "${CLINICAL_FHIR_VERSION:-}" != "R4" ]]; then
        log_warn "FHIR version is not R4, ensure compatibility"
    fi
    
    # Security validation
    local rate_limit="${CLINICAL_RATE_LIMIT_PER_MINUTE:-60}"
    if [[ "$rate_limit" -lt 10 ]]; then
        log_error "Rate limit too restrictive for healthcare operations"
        ((validation_errors++))
    fi
    
    if [[ "$rate_limit" -gt 1000 ]]; then
        log_error "Rate limit too permissive for security"
        ((validation_errors++))
    fi
    
    # Performance validation
    local max_time="${CLINICAL_MAX_PROCESSING_TIME_SECONDS:-5.0}"
    if (( $(echo "$max_time > 10.0" | bc -l) )); then
        log_error "Maximum processing time exceeds healthcare standards"
        ((validation_errors++))
    fi
    
    if [[ $validation_errors -gt 0 ]]; then
        log_error "Healthcare environment validation failed with $validation_errors errors"
        exit 1
    fi
    
    log_info "Healthcare environment validation: PASSED"
}

# Security and permission checks
perform_security_checks() {
    log_security "Performing container security validation..."
    
    # Check if running as non-root user
    if [[ "$(id -u)" == "0" ]]; then
        log_error "SECURITY: Container must not run as root user for healthcare compliance"
        exit 1
    fi
    
    # Validate file permissions
    if [[ ! -r "/app" ]]; then
        log_error "SECURITY: Application directory not readable"
        exit 1
    fi
    
    # Check for sensitive files
    if [[ -f "/app/.env" ]]; then
        log_warn "SECURITY: .env file detected, ensure no PHI or secrets are exposed"
    fi
    
    # Validate Python path and imports
    if ! python3 -c "import sys; print('Python path validation:', len(sys.path) > 0)" 2>/dev/null; then
        log_error "SECURITY: Python environment validation failed"
        exit 1
    fi
    
    log_security "Container security validation: PASSED"
}

# Healthcare component initialization checks
validate_healthcare_components() {
    log_info "Validating healthcare processing components..."
    
    # Test FHIR resources import
    if ! python3 -c "from fhir.resources.bundle import Bundle; print('FHIR resources: OK')" 2>/dev/null; then
        log_error "HEALTHCARE: FHIR resources library not available"
        exit 1
    fi
    
    # Test hybrid processor import
    if ! python3 -c "from src.summarizer.hybrid_processor import HybridClinicalProcessor; print('Hybrid processor: OK')" 2>/dev/null; then
        log_error "HEALTHCARE: Hybrid processor not available"
        exit 1
    fi
    
    # Test patient formatter import
    if ! python3 -c "from src.formatter.patient_friendly import PatientFriendlyFormatter; print('Patient formatter: OK')" 2>/dev/null; then
        log_error "HEALTHCARE: Patient formatter not available"
        exit 1
    fi
    
    # Test API models import
    if ! python3 -c "from src.api.models.fhir_models import OperationOutcome; print('API models: OK')" 2>/dev/null; then
        log_error "HEALTHCARE: API models not available"
        exit 1
    fi
    
    log_info "Healthcare processing components: VALIDATED"
}

# System resource validation for healthcare workloads
validate_system_resources() {
    log_info "Validating system resources for healthcare operations..."
    
    # Check available memory (minimum 512MB for healthcare processing)
    local available_memory_kb
    available_memory_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo "0")
    local available_memory_mb=$((available_memory_kb / 1024))
    
    if [[ $available_memory_mb -lt 512 ]]; then
        log_error "RESOURCE: Insufficient memory for healthcare operations (${available_memory_mb}MB < 512MB)"
        exit 1
    fi
    
    # Check disk space for temporary files and caching
    local available_disk_mb
    available_disk_mb=$(df /app | awk 'NR==2 {print int($4/1024)}')
    
    if [[ $available_disk_mb -lt 100 ]]; then
        log_error "RESOURCE: Insufficient disk space for healthcare operations (${available_disk_mb}MB < 100MB)"
        exit 1
    fi
    
    log_info "System resources validation: PASSED (Memory: ${available_memory_mb}MB, Disk: ${available_disk_mb}MB)"
}

# Create necessary directories with proper permissions
setup_healthcare_directories() {
    log_info "Setting up healthcare-compliant directory structure..."
    
    # Create directories if they don't exist
    local directories=("/app/logs" "/app/cache" "/app/temp")
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
        
        # Ensure proper permissions (readable/writable by clinical user only)
        chmod 750 "$dir" 2>/dev/null || log_warn "Could not set permissions for $dir"
    done
    
    log_info "Healthcare directory structure: READY"
}

# Validate AI/ML model availability (if enabled)
validate_ai_models() {
    if [[ "${CLINICAL_ENABLE_AI_PROCESSING:-false}" == "true" ]]; then
        log_info "Validating AI/ML models for narrative enhancement..."
        
        # Test transformers library
        if ! python3 -c "import transformers; print('Transformers library: OK')" 2>/dev/null; then
            log_warn "AI: Transformers library not available, AI processing will be limited"
        else
            log_info "AI/ML models: AVAILABLE"
        fi
    else
        log_info "AI processing disabled - using structured data only (safer for healthcare)"
    fi
}

# Final healthcare compliance check
perform_final_compliance_check() {
    log_info "Performing final healthcare compliance verification..."
    
    # Verify no PHI can be inadvertently logged
    if [[ -f "/app/logs/debug.log" ]] || [[ -f "/app/logs/request.log" ]]; then
        log_error "COMPLIANCE: Potential PHI logging files detected"
        exit 1
    fi
    
    # Ensure healthcare disclaimers are enabled
    if [[ "${CLINICAL_SHOW_DISCLAIMERS:-true}" != "true" ]]; then
        log_error "COMPLIANCE: Healthcare disclaimers must be enabled"
        exit 1
    fi
    
    # Verify educational use only flag
    if [[ "${CLINICAL_EDUCATIONAL_USE_ONLY:-true}" != "true" ]]; then
        log_error "COMPLIANCE: Educational use only flag must be enabled"
        exit 1
    fi
    
    log_info "Healthcare compliance verification: COMPLETE"
}

# Graceful shutdown handler
cleanup() {
    log_info "Healthcare-compliant shutdown initiated..."
    
    # Give processes time to complete current requests
    if [[ -n "${app_pid:-}" ]]; then
        log_info "Gracefully stopping application (PID: $app_pid)..."
        kill -TERM "$app_pid" 2>/dev/null || true
        
        # Wait up to 30 seconds for graceful shutdown
        local timeout=30
        while [[ $timeout -gt 0 ]] && kill -0 "$app_pid" 2>/dev/null; do
            sleep 1
            ((timeout--))
        done
        
        # Force kill if still running
        if kill -0 "$app_pid" 2>/dev/null; then
            log_warn "Force stopping application after timeout"
            kill -KILL "$app_pid" 2>/dev/null || true
        fi
    fi
    
    log_info "Healthcare-compliant shutdown complete"
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# Main startup sequence
main() {
    display_healthcare_banner
    validate_healthcare_environment
    perform_security_checks
    validate_system_resources
    setup_healthcare_directories
    validate_healthcare_components
    validate_ai_models
    perform_final_compliance_check
    
    log_info "All healthcare startup validations completed successfully"
    log_info "Starting Clinical Notes Summarizer API..."
    
    # Start the application
    if [[ $# -eq 0 ]]; then
        log_error "No command provided to startup script"
        exit 1
    fi
    
    # Execute the provided command and capture PID for graceful shutdown
    exec "$@" &
    app_pid=$!
    
    # Wait for the application to finish
    wait $app_pid
}

# Execute main function with all arguments
main "$@"