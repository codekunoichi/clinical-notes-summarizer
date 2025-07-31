"""
Pytest configuration and healthcare-specific fixtures for the clinical notes summarizer.

This module provides test fixtures and utilities that ensure healthcare safety
requirements are met throughout the testing process.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal


@pytest.fixture
def sample_medication_data() -> Dict[str, Any]:
    """
    Sample FHIR-compliant medication data for testing.
    
    This fixture provides realistic medication data that must be preserved
    exactly during processing - no AI summarization allowed.
    """
    return {
        "resourceType": "MedicationRequest",
        "id": "med-request-001",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197361",
                    "display": "Lisinopril 10 MG Oral Tablet"
                }
            ],
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
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route"
                        }
                    ]
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": 1,
                            "unit": "tablet",
                            "system": "http://unitsofmeasure.org",
                            "code": "{tbl}"
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_complex_medication_data() -> Dict[str, Any]:
    """
    Complex medication data with multiple instructions that must be preserved exactly.
    """
    return {
        "resourceType": "MedicationRequest",
        "id": "med-request-002",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197804",
                    "display": "Metformin 500 MG Oral Tablet"
                }
            ],
            "text": "Metformin 500mg tablets"
        },
        "subject": {
            "reference": "Patient/patient-001"
        },
        "dosageInstruction": [
            {
                "text": "Take 1 tablet by mouth twice daily with meals. Start with once daily for first week, then increase to twice daily as tolerated.",
                "patientInstruction": "Take with food to reduce stomach upset. Monitor blood sugar levels as directed.",
                "timing": {
                    "repeat": {
                        "frequency": 2,
                        "period": 1,
                        "periodUnit": "d",
                        "when": ["CM"]  # with meals
                    }
                },
                "route": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route"
                        }
                    ]
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": 1,
                            "unit": "tablet",
                            "system": "http://unitsofmeasure.org",
                            "code": "{tbl}"
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_lab_values() -> Dict[str, Any]:
    """
    Sample lab values that must be preserved exactly.
    """
    return {
        "resourceType": "Observation",
        "id": "lab-001",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "33747-0",
                    "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
                }
            ],
            "text": "Hemoglobin A1c"
        },
        "subject": {
            "reference": "Patient/patient-001"
        },
        "valueQuantity": {
            "value": 7.2,
            "unit": "%",
            "system": "http://unitsofmeasure.org",
            "code": "%"
        },
        "referenceRange": [
            {
                "low": {
                    "value": 4.0,
                    "unit": "%"
                },
                "high": {
                    "value": 6.0,
                    "unit": "%"
                },
                "text": "Normal: 4.0-6.0%"
            }
        ]
    }


class MedicationSafetyValidator:
    """
    Healthcare-specific validator to ensure medication data integrity.
    
    This validator implements zero-tolerance policies for medication errors
    and ensures that critical medical data is never altered by AI processing.
    """
    
    @staticmethod
    def validate_medication_preservation(original: Dict[str, Any], processed: Dict[str, Any]) -> List[str]:
        """
        Validate that medication data has been preserved exactly.
        
        Args:
            original: Original medication data (FHIR format)
            processed: Processed medication data (could be MedicationSummary format)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # If processed data is in MedicationSummary format, validate differently
        if "medication_name" in processed:
            # Validate medication name preservation
            orig_name = None
            if "medicationCodeableConcept" in original:
                orig_name = original["medicationCodeableConcept"].get("text")
            
            if orig_name and orig_name != processed.get("medication_name"):
                errors.append(f"Medication name was altered: '{orig_name}' -> '{processed.get('medication_name')}'")
            
            return errors
        
        # Otherwise, validate FHIR format preservation
        critical_fields = [
            "medicationCodeableConcept",
            "dosageInstruction",
            "status", 
            "intent"
        ]
        
        for field in critical_fields:
            if field in original:
                if field not in processed:
                    errors.append(f"Critical field '{field}' missing from processed data")
                elif original[field] != processed[field]:
                    errors.append(f"Critical field '{field}' was altered during processing")
        
        # Validate dosage instructions specifically
        if "dosageInstruction" in original and "dosageInstruction" in processed:
            orig_dosage = original["dosageInstruction"]
            proc_dosage = processed["dosageInstruction"]
            
            if len(orig_dosage) != len(proc_dosage):
                errors.append("Number of dosage instructions changed")
            
            for i, (orig_instr, proc_instr) in enumerate(zip(orig_dosage, proc_dosage)):
                # Critical dosage fields that must be preserved
                dosage_critical_fields = ["doseAndRate", "timing", "route"]
                
                for field in dosage_critical_fields:
                    if field in orig_instr:
                        if field not in proc_instr:
                            errors.append(f"Dosage instruction {i}: '{field}' missing")
                        elif orig_instr[field] != proc_instr[field]:
                            errors.append(f"Dosage instruction {i}: '{field}' was altered")
        
        return errors
    
    @staticmethod
    def validate_no_ai_processing_flags(processed_data: Dict[str, Any]) -> List[str]:
        """
        Validate that critical data was not processed by AI.
        
        Args:
            processed_data: Data that went through processing pipeline
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for AI processing flags in metadata
        if "_metadata" in processed_data:
            metadata = processed_data["_metadata"]
            
            # These fields should NEVER have AI processing flags
            prohibited_ai_fields = [
                "medication_name", "dosage", "frequency", "route",
                "lab_values", "vital_signs", "appointments", "contacts"
            ]
            
            for field in prohibited_ai_fields:
                if f"{field}_ai_processed" in metadata and metadata[f"{field}_ai_processed"]:
                    errors.append(f"CRITICAL: {field} was processed by AI - this is prohibited")
        
        return errors


@pytest.fixture
def medication_safety_validator() -> MedicationSafetyValidator:
    """Provide medication safety validator instance."""
    return MedicationSafetyValidator()


@pytest.fixture
def fhir_medication_bundle() -> Dict[str, Any]:
    """
    Complete FHIR bundle with medication data for integration testing.
    """
    return {
        "resourceType": "Bundle",
        "id": "medication-bundle-001",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-001",
                    "name": [
                        {
                            "family": "TestPatient",
                            "given": ["John"]
                        }
                    ]
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-request-001",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197361",
                                "display": "Lisinopril 10 MG Oral Tablet"
                            }
                        ],
                        "text": "Lisinopril 10mg tablets"
                    },
                    "subject": {
                        "reference": "Patient/patient-001"
                    },
                    "dosageInstruction": [
                        {
                            "text": "Take 1 tablet by mouth once daily for blood pressure",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d"
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }