#!/bin/bash

# Clinical Notes Summarizer - Security Scanning Script
# Healthcare-compliant container security validation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Healthcare compliance logging
log_info() {
    echo -e "${BLUE}[SECURITY-INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[SECURITY-WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[SECURITY-ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SECURITY-OK]${NC} $1"
}

# Check if required tools are available
check_security_tools() {
    log_info "Checking availability of security scanning tools..."
    
    local tools_available=0
    
    # Check for Docker security scanning tools
    if command -v docker &> /dev/null; then
        log_success "Docker CLI available"
        ((tools_available++))
    else
        log_error "Docker CLI not found"
    fi
    
    # Check for Trivy (vulnerability scanner)
    if command -v trivy &> /dev/null; then
        log_success "Trivy vulnerability scanner available"
        ((tools_available++))
    else
        log_warn "Trivy not found - install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
    fi
    
    # Check for Hadolint (Dockerfile linter)
    if command -v hadolint &> /dev/null; then
        log_success "Hadolint Dockerfile linter available"
        ((tools_available++))
    else
        log_warn "Hadolint not found - install with: wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 && chmod +x /usr/local/bin/hadolint"
    fi
    
    # Check for Docker Bench Security
    if [[ -f "/usr/local/bin/docker-bench-security.sh" ]]; then
        log_success "Docker Bench Security available"
        ((tools_available++))
    else
        log_warn "Docker Bench Security not found - clone from: https://github.com/docker/docker-bench-security"
    fi
    
    if [[ $tools_available -lt 2 ]]; then
        log_error "Insufficient security tools available for comprehensive scanning"
        exit 1
    fi
    
    log_info "Security tools check completed"
}

# Dockerfile security analysis
analyze_dockerfile() {
    log_info "Analyzing Dockerfile for healthcare security compliance..."
    
    local dockerfile_path="${1:-Dockerfile}"
    
    if [[ ! -f "$dockerfile_path" ]]; then
        log_error "Dockerfile not found at $dockerfile_path"
        return 1
    fi
    
    # Run Hadolint if available
    if command -v hadolint &> /dev/null; then
        log_info "Running Hadolint security analysis..."
        
        # Healthcare-specific Hadolint rules
        local hadolint_config="/tmp/hadolint_healthcare.yaml"
        cat > "$hadolint_config" << EOF
ignored:
  - DL3008  # Allow apt-get without version pinning for base images
  - DL3009  # Allow apt-get clean in same layer
trustedRegistries:
  - docker.io
  - python
EOF
        
        if hadolint --config "$hadolint_config" "$dockerfile_path"; then
            log_success "Dockerfile passes Hadolint security checks"
        else
            log_error "Dockerfile security issues found"
            return 1
        fi
        
        rm -f "$hadolint_config"
    fi
    
    # Manual healthcare-specific Dockerfile checks
    log_info "Running healthcare-specific Dockerfile validation..."
    
    # Check for non-root user
    if grep -q "USER.*clinical" "$dockerfile_path"; then
        log_success "Non-root user configured correctly"
    else
        log_error "Healthcare compliance requires non-root user execution"
    fi
    
    # Check for PHI protection environment variables
    if grep -q "CLINICAL_ENABLE_PHI_PROTECTION=true" "$dockerfile_path"; then
        log_success "PHI protection enabled in container"
    else
        log_warn "PHI protection should be explicitly enabled in Dockerfile"
    fi
    
    # Check for healthcare labels
    if grep -q "healthcare.compliance" "$dockerfile_path"; then
        log_success "Healthcare compliance labels present"
    else
        log_warn "Consider adding healthcare compliance labels"
    fi
    
    log_info "Dockerfile security analysis completed"
}

# Container image vulnerability scanning
scan_image_vulnerabilities() {
    local image_name="${1:-clinical-notes-summarizer}"
    
    log_info "Scanning container image for vulnerabilities..."
    
    if command -v trivy &> /dev/null; then
        log_info "Running Trivy vulnerability scan..."
        
        # High and critical vulnerabilities only for healthcare
        if trivy image --severity HIGH,CRITICAL --exit-code 1 "$image_name"; then
            log_success "No high or critical vulnerabilities found"
        else
            log_error "High or critical vulnerabilities detected - healthcare compliance requires resolution"
            return 1
        fi
        
        # Full report for documentation
        log_info "Generating comprehensive vulnerability report..."
        trivy image --format json --output "/tmp/clinical-security-report.json" "$image_name"
        
        if [[ -f "/tmp/clinical-security-report.json" ]]; then
            log_success "Security report generated: /tmp/clinical-security-report.json"
        fi
    else
        log_warn "Trivy not available - manual vulnerability assessment required"
    fi
}

# Container runtime security checks
check_runtime_security() {
    local container_name="${1:-clinical-notes-api}"
    
    log_info "Checking container runtime security configuration..."
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        # Check if container is running as non-root
        local container_user
        container_user=$(docker exec "$container_name" id -u 2>/dev/null || echo "unknown")
        
        if [[ "$container_user" != "0" ]]; then
            log_success "Container running as non-root user (UID: $container_user)"
        else
            log_error "CRITICAL: Container running as root - healthcare compliance violation"
        fi
        
        # Check security options
        local security_opts
        security_opts=$(docker inspect "$container_name" --format '{{.HostConfig.SecurityOpt}}' 2>/dev/null || echo "[]")
        
        if echo "$security_opts" | grep -q "no-new-privileges"; then
            log_success "no-new-privileges security option enabled"
        else
            log_warn "Consider enabling no-new-privileges security option"
        fi
        
        # Check read-only root filesystem
        local readonly_root
        readonly_root=$(docker inspect "$container_name" --format '{{.HostConfig.ReadonlyRootfs}}' 2>/dev/null || echo "false")
        
        if [[ "$readonly_root" == "true" ]]; then
            log_success "Read-only root filesystem enabled"
        else
            log_warn "Consider enabling read-only root filesystem for security"
        fi
        
        # Check resource limits
        local memory_limit
        memory_limit=$(docker inspect "$container_name" --format '{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
        
        if [[ "$memory_limit" != "0" ]]; then
            log_success "Memory limits configured for container"
        else
            log_warn "Consider setting memory limits for healthcare workloads"
        fi
        
    else
        log_warn "Container $container_name not running - skipping runtime checks"
    fi
}

# Network security validation
check_network_security() {
    log_info "Validating network security configuration..."
    
    # Check for custom networks (better than default bridge)
    if docker network ls | grep -q "clinical_network"; then
        log_success "Custom network configured for isolation"
        
        # Check network configuration
        local network_driver
        network_driver=$(docker network inspect clinical_network --format '{{.Driver}}' 2>/dev/null || echo "unknown")
        
        if [[ "$network_driver" == "bridge" ]]; then
            log_success "Bridge network driver configured"
        else
            log_info "Network driver: $network_driver"
        fi
    else
        log_warn "Consider using custom networks for better security isolation"
    fi
    
    # Check exposed ports
    log_info "Checking exposed ports..."
    
    if docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -q "clinical.*8000"; then
        log_success "API port 8000 properly exposed"
    else
        log_warn "API port configuration should be verified"
    fi
}

# Healthcare-specific compliance checks
check_healthcare_compliance() {
    log_info "Validating healthcare-specific security compliance..."
    
    # Check environment variables for PHI protection
    local container_name="${1:-clinical-notes-api}"
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        # Check PHI protection environment variable
        local phi_protection
        phi_protection=$(docker exec "$container_name" printenv CLINICAL_ENABLE_PHI_PROTECTION 2>/dev/null || echo "unknown")
        
        if [[ "$phi_protection" == "true" ]]; then
            log_success "PHI protection enabled in runtime"
        else
            log_error "CRITICAL: PHI protection not enabled - healthcare compliance violation"
        fi
        
        # Check debug mode
        local debug_mode
        debug_mode=$(docker exec "$container_name" printenv CLINICAL_DEBUG 2>/dev/null || echo "unknown")
        
        if [[ "$debug_mode" == "false" ]]; then
            log_success "Debug mode properly disabled"
        else
            log_warn "Debug mode should be disabled in production"
        fi
        
        # Check request logging
        local request_logging
        request_logging=$(docker exec "$container_name" printenv CLINICAL_ENABLE_REQUEST_LOGGING 2>/dev/null || echo "unknown")
        
        if [[ "$request_logging" == "false" ]]; then
            log_success "Request logging properly disabled for PHI protection"
        else
            log_error "Request logging should be disabled to prevent PHI exposure"
        fi
    fi
}

# Generate security report
generate_security_report() {
    local report_file="/tmp/clinical-security-assessment-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "Generating healthcare security assessment report..."
    
    cat > "$report_file" << EOF
# Clinical Notes Summarizer - Security Assessment Report
Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Healthcare Compliance Status
- PHI Protection: REQUIRED
- FHIR R4 Compliance: REQUIRED
- Non-root Execution: REQUIRED
- Vulnerability Management: REQUIRED

## Security Scan Summary
$(date -u +"%Y-%m-%d %H:%M:%S UTC"): Security assessment completed

## Recommendations for Healthcare Deployment

### Critical Actions Required:
1. Ensure PHI protection is enabled in all environments
2. Resolve any HIGH or CRITICAL vulnerabilities
3. Verify non-root container execution
4. Implement proper access controls

### Recommended Security Enhancements:
1. Enable read-only root filesystem
2. Configure resource limits
3. Use custom networks for isolation
4. Implement network segmentation
5. Regular security scanning automation
6. Healthcare-specific incident response procedures

### Compliance Notes:
- This system handles healthcare data and must comply with applicable regulations
- Regular security assessments are required for healthcare systems
- All security findings should be documented and remediated
- Incident response procedures must be tested regularly

## Next Steps:
1. Review and remediate identified security issues
2. Implement recommended security enhancements  
3. Schedule regular security assessments
4. Update security documentation
5. Train staff on healthcare security requirements

EOF

    log_success "Security assessment report generated: $report_file"
    
    # Display summary
    log_info "=== SECURITY ASSESSMENT SUMMARY ==="
    log_info "Report location: $report_file"
    log_info "Assessment completed at: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    log_info "Next assessment recommended: $(date -u -d '+30 days' +"%Y-%m-%d")"
}

# Main security scanning function
main() {
    log_info "========================================================"
    log_info "Clinical Notes Summarizer - Healthcare Security Scan"
    log_info "========================================================"
    
    local image_name="${1:-clinical-notes-summarizer}"
    local container_name="${2:-clinical-notes-api}"
    
    # Run security checks
    check_security_tools
    analyze_dockerfile "Dockerfile"
    
    # Only run image/container scans if they exist
    if docker images | grep -q "$image_name"; then
        scan_image_vulnerabilities "$image_name"
    else
        log_warn "Image $image_name not found - skipping image vulnerability scan"
    fi
    
    check_runtime_security "$container_name"
    check_network_security
    check_healthcare_compliance "$container_name"
    
    # Generate comprehensive report
    generate_security_report
    
    log_success "Healthcare security assessment completed"
    log_info "Review the generated report and address any identified issues"
}

# Execute main function
main "$@"