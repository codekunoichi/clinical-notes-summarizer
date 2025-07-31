# Clinical Notes Summarizer API Documentation

## Overview

The Clinical Notes Summarizer API is a FHIR R4 compatible REST API that transforms complex clinical documents into patient-friendly summaries. It implements a **hybrid structured + AI approach** with strict healthcare safety guarantees.

### Key Features

- **Zero PHI Storage**: No patient data is logged or persisted
- **Critical Data Preservation**: Medications, lab values, and vital signs are never AI-processed
- **FHIR R4 Compliance**: Full compatibility with healthcare data standards
- **Rate Limited**: Protection against abuse and misuse
- **Input Validation**: Comprehensive sanitization and validation
- **Healthcare Safety**: Built-in disclaimers and safety measures

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production environments, implement proper authentication and authorization mechanisms.

## API Endpoints

### Health Check Endpoints

#### GET /api/v1/health

Comprehensive health check with system status, component health, and performance metrics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-31T13:17:10.821454Z",
  "version": "1.0.0",
  "fhir_version": "R4",
  "components": {
    "hybrid_processor": "healthy",
    "fhir_parser": "healthy",
    "api_models": "healthy",
    "clinical_models": "healthy"
  },
  "performance_metrics": {
    "system_memory": {
      "total_gb": 8.0,
      "available_gb": 4.2,
      "percent_used": 47.5
    },
    "system_cpu": {
      "percent_used": 15.2,
      "count": 8
    },
    "health_check_response_time_ms": 45.23
  },
  "safety_checks": {
    "phi_protection_enabled": true,
    "debug_disabled_in_prod": true,
    "rate_limiting_enabled": true,
    "processing_time_limited": true,
    "fhir_r4_support": true
  }
}
```

#### GET /api/v1/health/ready

Kubernetes-style readiness probe.

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2025-07-31T13:17:10.821454Z"
}
```

#### GET /api/v1/health/live

Kubernetes-style liveness probe.

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2025-07-31T13:17:10.821454Z",
  "uptime_check": "passed"
}
```

### Clinical Summarization Endpoints

#### POST /api/v1/summarize

Process FHIR Bundle to create patient-friendly clinical summary.

**Request Body:**
```json
{
  "bundle": {
    "resourceType": "Bundle",
    "type": "document",
    "entry": [
      {
        "resource": {
          "resourceType": "MedicationRequest",
          "id": "med-001",
          "status": "active",
          "intent": "order",
          "medicationCodeableConcept": {
            "text": "Lisinopril 10mg tablets",
            "coding": [
              {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "314076",
                "display": "Lisinopril 10 MG Oral Tablet"
              }
            ]
          },
          "subject": {
            "reference": "Patient/patient-001"
          },
          "dosageInstruction": [
            {
              "text": "Take 1 tablet by mouth once daily",
              "patientInstruction": "Take once daily in the morning",
              "timing": {
                "repeat": {
                  "frequency": 1,
                  "period": 1,
                  "periodUnit": "d"
                }
              },
              "route": {
                "text": "Oral"
              },
              "doseAndRate": [
                {
                  "doseQuantity": {
                    "value": 10,
                    "unit": "mg"
                  }
                }
              ]
            }
          ]
        }
      }
    ]
  },
  "processing_options": {},
  "patient_preferences": {}
}
```

**Response:**
```json
{
  "summary": {
    "summary_id": "123e4567-e89b-12d3-a456-426614174000",
    "patient_id": "patient-001",
    "generated_at": "2025-07-31T13:17:10.821454Z",
    "medications": [
      {
        "medication_name": "Lisinopril 10mg tablets",
        "dosage": "10 mg",
        "frequency": "1 time(s) per 1 d",
        "route": "Oral",
        "instructions": "Take 1 tablet by mouth once daily | Take once daily in the morning",
        "purpose": null,
        "important_notes": null,
        "metadata": {
          "processed_at": "2025-07-31T13:17:10.821454Z",
          "processing_version": "1.0.0",
          "safety_level": "critical",
          "processing_type": "preserved",
          "ai_processed": false,
          "validation_passed": true,
          "validation_errors": []
        }
      }
    ],
    "lab_results": [],
    "appointments": [],
    "disclaimers": [
      "This summary is for educational purposes only and does not replace professional medical advice.",
      "Always consult your healthcare provider before making any changes to your medications or treatment plan.",
      "In case of emergency, call 911 or go to the nearest emergency room."
    ],
    "safety_validation": {
      "validation_id": "456e7890-e89b-12d3-a456-426614174000",
      "validated_at": "2025-07-31T13:17:10.821454Z",
      "data_type": "clinical_summary",
      "passed": true,
      "errors": [],
      "warnings": [],
      "critical_fields_preserved": {
        "medications": true
      },
      "ai_processing_flags": {
        "medications": false
      }
    }
  },
  "processing_metadata": {
    "request_id": "789e0123-e89b-12d3-a456-426614174000",
    "processed_at": "2025-07-31T13:17:10.821454Z",
    "processing_time_seconds": 2.345,
    "bundle_entries_processed": 1,
    "api_version": "1.0.0",
    "fhir_version": "R4",
    "processor_version": "1.0.0",
    "safety_guarantees": {
      "critical_data_preserved": true,
      "ai_processing_controlled": true,
      "phi_protection_enabled": true,
      "validation_performed": true
    },
    "performance_metrics": {
      "processing_time_ms": 2345.67,
      "meets_5_second_requirement": true,
      "entries_per_second": 0.43
    }
  },
  "fhir_metadata": {
    "profile": "http://hl7.org/fhir/StructureDefinition/Bundle",
    "version": "R4",
    "last_updated": "2025-07-31T13:17:10.821454Z",
    "security": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "HTEST",
        "display": "test health data"
      }
    ]
  }
}
```

#### POST /api/v1/summarize/validate-only

Validate FHIR Bundle without processing.

**Request Body:** Same as `/api/v1/summarize`

**Response:**
```json
{
  "bundle_valid": true,
  "entries_processed": 1,
  "medication_requests_found": 1,
  "validation_errors": [],
  "validation_warnings": [],
  "processable": true,
  "validation_metadata": {
    "request_id": "abc123-def456-ghi789",
    "validation_time_seconds": 0.123,
    "timestamp": "2025-07-31T13:17:10.821454Z"
  }
}
```

### Validation Endpoints

#### POST /api/v1/validate

Validate FHIR resource for healthcare compliance.

**Request Body:**
```json
{
  "resource": {
    "resourceType": "MedicationRequest",
    "id": "med-001",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {
      "text": "Aspirin 81mg tablets"
    },
    "subject": {
      "reference": "Patient/patient-001"
    }
  },
  "validation_mode": "strict"
}
```

**Response:**
```json
{
  "is_valid": true,
  "issues": [],
  "resource_type": "MedicationRequest",
  "validation_metadata": {
    "request_id": "validation-123",
    "validated_at": "2025-07-31T13:17:10.821454Z",
    "validation_time_seconds": 0.045,
    "validation_mode": "strict",
    "resource_type": "MedicationRequest",
    "validator_version": "1.0.0",
    "fhir_version": "R4"
  }
}
```

#### POST /api/v1/validate/medication-request

Specialized validation for MedicationRequest resources.

#### POST /api/v1/validate/bundle

Specialized validation for Bundle resources.

### Summary Management Endpoints

#### GET /api/v1/summary/{summary_id}

Retrieve a stored clinical summary by ID.

**Response:**
```json
{
  "summary": {
    "summary_id": "123e4567-e89b-12d3-a456-426614174000",
    "patient_id": "patient-001",
    "medications": [...],
    "disclaimers": [...]
  },
  "processing_metadata": {
    "retrieved_at": "2025-07-31T13:17:10.821454Z",
    "summary_age_minutes": 15.5,
    "storage_type": "in_memory_demo"
  },
  "fhir_metadata": {
    "profile": "http://hl7.org/fhir/StructureDefinition/Bundle",
    "version": "R4",
    "last_updated": "2025-07-31T13:17:10.821454Z"
  }
}
```

#### GET /api/v1/summaries

List stored clinical summaries with pagination.

**Query Parameters:**
- `limit` (integer, 1-100): Maximum number of summaries to return (default: 10)
- `offset` (integer, ≥0): Number of summaries to skip (default: 0)

**Response:**
```json
{
  "summaries": [
    {
      "summary_id": "123e4567-e89b-12d3-a456-426614174000",
      "patient_id": "patient-001",
      "generated_at": "2025-07-31T13:17:10.821454Z",
      "stored_at": "2025-07-31T13:17:10.821454Z",
      "expires_at": "2025-08-01T13:17:10.821454Z",
      "medication_count": 1,
      "lab_result_count": 0,
      "appointment_count": 0
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "returned": 1
  }
}
```

#### GET /api/v1/summary/{summary_id}/metadata

Get metadata for a clinical summary without full content.

#### POST /api/v1/summary/{summary_id}/store

Store a clinical summary (demonstration purposes only).

#### DELETE /api/v1/summary/{summary_id}

Delete a stored clinical summary.

## Error Handling

All errors return FHIR-compliant OperationOutcome responses:

```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "invalid",
      "details": {
        "text": "Bundle must contain at least one entry for processing"
      },
      "diagnostics": "HTTP 400"
    }
  ]
}
```

### Common Error Codes

- **400 Bad Request**: Invalid request format or missing required fields
- **413 Request Entity Too Large**: Request exceeds size limits
- **415 Unsupported Media Type**: Content-Type must be application/json
- **422 Unprocessable Entity**: Valid JSON but failed validation
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected server error
- **503 Service Unavailable**: Service temporarily unavailable

## Rate Limiting

The API implements rate limiting with the following headers:

- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Window`: Time window in seconds
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Timestamp when the window resets

Default limits:
- **60 requests per minute** per IP address
- Health check endpoints are excluded from rate limiting

## Security Headers

All responses include healthcare-compliant security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `X-Healthcare-API: Clinical-Notes-Summarizer`
- `X-FHIR-Version: R4`
- `X-PHI-Protected: true`
- `X-HIPAA-Compliant: true`

## Clinical Data Processing

### Hybrid Structured + AI Approach

The API uses a strict separation between critical and narrative data:

#### PRESERVED EXACTLY (No AI Processing):
- Medication names, dosages, frequencies, instructions
- Lab values, units, reference ranges, results
- Vital signs and measurements
- Appointment dates, times, locations
- Provider contact information
- Pharmacy addresses and phone numbers
- Insurance information
- Emergency contacts and medical alerts

#### AI-ENHANCED for Clarity:
- Chief complaint descriptions
- Diagnosis explanations
- Procedure descriptions
- General care instructions
- Lifestyle recommendations
- Warning signs explanations

### Safety Guarantees

1. **Zero PHI Storage**: No patient data is persisted or logged
2. **Data Integrity**: Critical medical data is preserved exactly
3. **Validation**: All inputs are validated for healthcare compliance
4. **Disclaimers**: All summaries include required healthcare disclaimers
5. **Audit Trail**: Complete processing metadata for accountability

## Integration Examples

### Diabetes Management Summary

```bash
curl -X POST "http://localhost:8000/api/v1/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "bundle": {
      "resourceType": "Bundle",
      "type": "document",
      "entry": [
        {
          "resource": {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
              "text": "Metformin 500mg tablets"
            },
            "subject": {"reference": "Patient/diabetes-patient"},
            "dosageInstruction": [{
              "text": "Take 1 tablet twice daily with meals",
              "timing": {
                "repeat": {
                  "frequency": 2,
                  "period": 1,
                  "periodUnit": "d"
                }
              }
            }]
          }
        }
      ]
    }
  }'
```

### Medication Reconciliation

```bash
curl -X POST "http://localhost:8000/api/v1/validate/medication-request" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "MedicationRequest",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {
      "text": "Lisinopril 10mg"
    },
    "subject": {"reference": "Patient/hypertension-patient"}
  }'
```

## Environment Configuration

Key environment variables (prefix with `CLINICAL_`):

```bash
CLINICAL_ENVIRONMENT=development
CLINICAL_DEBUG=true
CLINICAL_RATE_LIMIT_PER_MINUTE=60
CLINICAL_MAX_PROCESSING_TIME_SECONDS=5.0
CLINICAL_ENABLE_PHI_PROTECTION=true
CLINICAL_FHIR_VERSION=R4
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t clinical-notes-summarizer .

# Run container
docker run -p 8000:8000 \
  -e CLINICAL_ENVIRONMENT=production \
  -e CLINICAL_DEBUG=false \
  clinical-notes-summarizer
```

### Health Checks

Configure container health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health/live || exit 1
```

## Support

For issues, questions, or contributions:

- **GitHub**: [Clinical Notes Summarizer Repository]
- **License**: MIT License
- **FHIR Version**: R4
- **API Version**: 1.0.0

## Important Disclaimers

- This API is for educational purposes only
- Not a substitute for professional medical advice
- Always consult healthcare providers for medical decisions
- Ensure proper PHI protection in production environments
- Comply with all applicable healthcare regulations (HIPAA, etc.)