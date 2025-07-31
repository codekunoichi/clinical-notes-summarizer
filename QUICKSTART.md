# Quick Start Guide

## Prerequisites

- Python 3.9+
- Virtual environment activated
- All dependencies installed

## 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

## 2. Start the API Server

```bash
python3 run_api.py
```

The API will be available at: http://localhost:8000

## 3. Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

## 4. View API Documentation

Open your browser to: http://localhost:8000/docs

## 5. Test with Sample Data

### Process a Medication Summary

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
            "id": "med-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
              "text": "Lisinopril 10mg tablets"
            },
            "subject": {
              "reference": "Patient/patient-001"
            },
            "dosageInstruction": [
              {
                "text": "Take 1 tablet by mouth once daily",
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
    }
  }'
```

## 6. Run Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test categories
python3 -m pytest tests/test_api_endpoints.py::TestHealthEndpoints -v
python3 -m pytest tests/test_api_endpoints.py::TestSummarizeEndpoints -v
python3 -m pytest tests/test_fhir_models.py -v
```

## Key Features Demonstrated

✅ **FHIR R4 Compliance**: Full FHIR Bundle processing
✅ **Healthcare Safety**: Critical data preservation
✅ **PHI Protection**: No sensitive data logging
✅ **Rate Limiting**: API protection measures
✅ **Comprehensive Testing**: TDD approach with clinical scenarios
✅ **Error Handling**: FHIR-compliant OperationOutcome responses
✅ **Performance Monitoring**: <5 second processing requirement
✅ **Security Headers**: Healthcare-compliant security measures

## File Structure

```
/Users/rumpagiri/Projects/clinical-notes-summarizer/
├── src/api/
│   ├── main.py                 # FastAPI application
│   ├── core/config.py         # Configuration management
│   ├── endpoints/             # API endpoints
│   │   ├── health.py          # Health monitoring
│   │   ├── summarize.py       # Clinical summarization
│   │   ├── validate.py        # FHIR validation
│   │   └── summary.py         # Summary management
│   ├── middleware/            # Healthcare security
│   │   ├── security.py        # Security headers
│   │   ├── rate_limiting.py   # Rate limiting
│   │   └── phi_protection.py  # PHI protection
│   └── models/
│       └── fhir_models.py     # FHIR R4 models
├── tests/                     # Comprehensive test suite
├── docs/                      # API documentation
└── run_api.py                 # Server launcher
```

## Production Deployment

For production deployment, ensure:

1. Set environment variables:
   ```bash
   export CLINICAL_ENVIRONMENT=production
   export CLINICAL_DEBUG=false
   export CLINICAL_ENABLE_PHI_PROTECTION=true
   ```

2. Use proper security measures:
   - HTTPS/TLS encryption
   - Authentication and authorization
   - Database encryption for any persistent data
   - Regular security audits

3. Monitor health endpoints:
   - `/api/v1/health` for comprehensive monitoring
   - `/api/v1/health/ready` for readiness probes
   - `/api/v1/health/live` for liveness probes

## Healthcare Compliance

This implementation includes:

- **Zero PHI Storage**: No patient data persistence
- **Critical Data Preservation**: Exact medication information
- **FHIR R4 Compliance**: Standard healthcare data format
- **Safety Disclaimers**: Required healthcare warnings
- **Audit Trail**: Complete processing metadata
- **Rate Limiting**: API protection
- **Input Validation**: Comprehensive data sanitization