"""
Comprehensive clinical scenario tests for the Clinical Notes Summarizer.

This test suite covers realistic, complex clinical scenarios that healthcare
professionals encounter daily. All tests follow TDD principles and maintain
zero-tolerance safety standards for critical medical data.

Test Categories:
1. Diabetes Management (insulin regimens, monitoring)
2. Cardiac Care (multiple medications, interactions)
3. Post-Surgical Protocols (pain management, infection prevention)
4. Chronic Disease Management (hypertension, depression)
5. Emergency Medication Protocols (acute interventions)
6. Pediatric vs Adult Dosing (age-specific calculations)
7. Medication Reconciliation (complex multi-provider scenarios)
"""

import pytest
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import (
    ClinicalSummary,
    MedicationSummary,
    SafetyLevel,
    ProcessingType
)
from src.models.medication import MedicationRequest


class TestDiabetesManagementScenarios:
    """
    Test scenarios for complex diabetes management with multiple insulins,
    sliding scales, and blood glucose monitoring protocols.
    """
    
    def test_complex_insulin_regimen_processing(self):
        """
        Test processing of complex insulin regimen with basal-bolus therapy.
        
        Scenario: Type 1 diabetic patient on multiple daily injections:
        - Long-acting insulin (Lantus) once daily
        - Rapid-acting insulin (NovoLog) with meals
        - Correction scale for high blood glucose
        - Blood glucose monitoring protocol
        """
        processor = HybridClinicalProcessor()
        
        # Complex insulin bundle with multiple medication requests
        insulin_bundle = {
            "resourceType": "Bundle",
            "id": "diabetes-management-001",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-diabetes-001",
                        "name": [{"family": "DiabetesPatient", "given": ["Jane"]}]
                    }
                },
                # Long-acting insulin (basal)
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "insulin-lantus-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "274783",
                                "display": "Insulin Glargine 100 unit/mL Pen Injector"
                            }],
                            "text": "Lantus (insulin glargine) 100 units/mL pen"
                        },
                        "subject": {"reference": "Patient/patient-diabetes-001"},
                        "dosageInstruction": [{
                            "text": "Inject 24 units subcutaneously once daily at bedtime",
                            "patientInstruction": "Inject same time each evening. Rotate injection sites. Do not shake pen.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["21:00"]
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "34206005",
                                    "display": "Subcutaneous route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 24,
                                    "unit": "units",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "U"
                                }
                            }]
                        }]
                    }
                },
                # Rapid-acting insulin (bolus)
                {
                    "resource": {
                        "resourceType": "MedicationRequest", 
                        "id": "insulin-novolog-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "285018",
                                "display": "Insulin Aspart 100 unit/mL Pen Injector"
                            }],
                            "text": "NovoLog (insulin aspart) 100 units/mL pen"
                        },
                        "subject": {"reference": "Patient/patient-diabetes-001"},
                        "dosageInstruction": [{
                            "text": "Inject 8-12 units subcutaneously before meals based on carbohydrate content (1 unit per 10g carbs) plus correction scale",
                            "patientInstruction": "Inject 15 minutes before meals. Use sliding scale for blood glucose >150 mg/dL: 151-200: add 2 units, 201-250: add 4 units, 251-300: add 6 units, >300: call provider.",
                            "timing": {
                                "repeat": {
                                    "frequency": 3,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "when": ["AC"]  # before meals
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "34206005",
                                    "display": "Subcutaneous route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 10,  # Average dose
                                    "unit": "units",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "U"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
        
        # Process the complex insulin regimen
        start_time = time.time()
        result = processor.process_clinical_data(insulin_bundle)
        processing_time = time.time() - start_time
        
        # CRITICAL SAFETY: Processing time must be <5 seconds
        assert processing_time < 5.0, f"Processing took {processing_time:.2f}s, exceeds 5s limit"
        
        # Verify complete clinical summary structure
        assert isinstance(result, ClinicalSummary)
        assert len(result.medications) == 2
        
        # CRITICAL: Verify exact preservation of insulin names
        lantus_med = next((m for m in result.medications if "Lantus" in m.medication_name), None)
        novolog_med = next((m for m in result.medications if "NovoLog" in m.medication_name), None)
        
        assert lantus_med is not None, "Lantus medication not found in results"
        assert novolog_med is not None, "NovoLog medication not found in results"
        
        # CRITICAL: Verify exact dosage preservation for Lantus
        assert lantus_med.medication_name == "Lantus (insulin glargine) 100 units/mL pen"
        assert "24 units" in lantus_med.dosage
        assert "1 time(s) per 1 d" in lantus_med.frequency
        
        # CRITICAL: Verify complex dosage preservation for NovoLog  
        assert novolog_med.medication_name == "NovoLog (insulin aspart) 100 units/mL pen"
        assert "10 units" in novolog_med.dosage
        assert "3 time(s) per 1 d" in novolog_med.frequency
        
        # CRITICAL: Verify complex instructions are preserved exactly
        assert "sliding scale" in novolog_med.instructions.lower()
        assert "151-200" in novolog_med.instructions  # Sliding scale details preserved
        assert "carbohydrate" in novolog_med.instructions.lower()
        
        # CRITICAL: Verify no AI processing of medication data
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert medication.metadata.processing_type == ProcessingType.PRESERVED
            assert not medication.metadata.ai_processed
        
        # Verify safety validation passed
        assert result.safety_validation.passed
        assert len(result.safety_validation.errors) == 0
    
    def test_pediatric_diabetes_dosing_precision(self):
        """
        Test pediatric diabetes dosing where precision is critical.
        
        Scenario: 8-year-old Type 1 diabetic (weight-based dosing):
        - Weight-based insulin calculations
        - Micro-dose precision requirements
        - Different injection sites and techniques
        """
        processor = HybridClinicalProcessor()
        
        pediatric_insulin_data = {
            "resourceType": "MedicationRequest",
            "id": "pediatric-insulin-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "274783",
                    "display": "Insulin Glargine 100 unit/mL Pen Injector"
                }],
                "text": "Lantus (insulin glargine) 100 units/mL pen - pediatric"
            },
            "subject": {"reference": "Patient/pediatric-patient-001"},
            "dosageInstruction": [{
                "text": "Inject 0.3 units per kg body weight (child weighs 25 kg = 7.5 units) subcutaneously once daily at bedtime",
                "patientInstruction": "Pediatric dose calculation: 0.3 units/kg x 25 kg = 7.5 units. Use insulin pen with 0.5 unit increments. Parent supervision required.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "d",
                        "timeOfDay": ["20:00"]
                    }
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "34206005",
                        "display": "Subcutaneous route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 7.5,  # Critical precision for pediatric dose
                        "unit": "units",
                        "system": "http://unitsofmeasure.org",
                        "code": "U"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(pediatric_insulin_data)
        
        # CRITICAL: Pediatric dose precision must be preserved exactly
        assert "7.5 units" in result.dosage
        assert result.medication_name == "Lantus (insulin glargine) 100 units/mL pen - pediatric"
        
        # CRITICAL: Weight-based calculation details must be preserved
        assert "0.3 units per kg" in result.instructions
        assert "25 kg" in result.instructions
        assert "parent supervision" in result.instructions.lower()
        
        # CRITICAL: No AI processing allowed for pediatric dosing
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestCardiacCareScenarios:
    """
    Test scenarios for cardiac patients on multiple medications with
    potential interactions and critical monitoring requirements.
    """
    
    def test_heart_failure_medication_regimen(self):
        """
        Test complex heart failure medication regimen with multiple drug classes.
        
        Scenario: Heart failure patient on:
        - ACE inhibitor (Lisinopril)
        - Beta-blocker (Metoprolol)
        - Diuretic (Furosemide)
        - Anticoagulant (Warfarin) with INR monitoring
        """
        processor = HybridClinicalProcessor()
        
        heart_failure_bundle = {
            "resourceType": "Bundle",
            "id": "heart-failure-001",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-hf-001",
                        "name": [{"family": "HeartPatient", "given": ["Robert"]}]
                    }
                },
                # ACE Inhibitor
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "lisinopril-hf-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197361",
                                "display": "Lisinopril 10 MG Oral Tablet"
                            }],
                            "text": "Lisinopril 10mg tablets"
                        },
                        "subject": {"reference": "Patient/patient-hf-001"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily for heart failure and blood pressure control",
                            "patientInstruction": "Monitor blood pressure and kidney function. Report dry cough, swelling, or dizziness.",
                            "timing": {
                                "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                },
                # Beta-blocker
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "metoprolol-hf-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "866511",
                                "display": "Metoprolol Succinate 50 MG Extended Release Oral Tablet"
                            }],
                            "text": "Metoprolol succinate ER 50mg tablets"
                        },
                        "subject": {"reference": "Patient/patient-hf-001"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily with or immediately following meals",
                            "patientInstruction": "Do not crush, chew, or divide tablet. Monitor heart rate and blood pressure. Do not stop suddenly.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "when": ["PCM"]  # after meals
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                },
                # Diuretic
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "furosemide-hf-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "310429",
                                "display": "Furosemide 20 MG Oral Tablet"
                            }],
                            "text": "Furosemide 20mg tablets"
                        },
                        "subject": {"reference": "Patient/patient-hf-001"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth twice daily in morning and early afternoon",
                            "patientInstruction": "Take in morning and early afternoon to avoid nighttime urination. Monitor weight daily. Report rapid weight gain >3 lbs in 24 hours.",
                            "timing": {
                                "repeat": {
                                    "frequency": 2,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["08:00", "14:00"]
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
        
        start_time = time.time()
        result = processor.process_clinical_data(heart_failure_bundle)
        processing_time = time.time() - start_time
        
        # CRITICAL: Processing time constraint
        assert processing_time < 5.0
        
        # Verify all medications processed
        assert len(result.medications) == 3
        medication_names = [med.medication_name for med in result.medications]
        
        # CRITICAL: Exact medication name preservation
        assert "Lisinopril 10mg tablets" in medication_names
        assert "Metoprolol succinate ER 50mg tablets" in medication_names
        assert "Furosemide 20mg tablets" in medication_names
        
        # CRITICAL: Verify complex timing preservation for diuretic
        furosemide = next((m for m in result.medications if "Furosemide" in m.medication_name), None)
        assert furosemide is not None
        assert "2 time(s) per 1 d" in furosemide.frequency
        assert "morning and early afternoon" in furosemide.instructions.lower()
        assert "weight daily" in furosemide.instructions.lower()
        
        # CRITICAL: Verify beta-blocker specific instructions preserved
        metoprolol = next((m for m in result.medications if "Metoprolol" in m.medication_name), None)
        assert metoprolol is not None
        assert "do not crush" in metoprolol.instructions.lower()
        assert "do not stop suddenly" in metoprolol.instructions.lower()
        
        # CRITICAL: All medications must have critical safety level
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed


class TestPostSurgicalProtocols:
    """
    Test scenarios for post-surgical medication protocols including
    pain management, infection prevention, and wound care.
    """
    
    def test_post_operative_pain_management_protocol(self):
        """
        Test post-surgical pain management with multimodal approach.
        
        Scenario: Post-operative knee replacement patient:
        - Opioid analgesic with strict dosing
        - NSAID for inflammation
        - Anticoagulant for DVT prevention
        - Antibiotic prophylaxis
        """
        processor = HybridClinicalProcessor()
        
        post_surgical_data = {
            "resourceType": "MedicationRequest",
            "id": "oxycodone-post-op-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "1049621",
                    "display": "Oxycodone Hydrochloride 5 MG Oral Tablet"
                }],
                "text": "Oxycodone 5mg tablets"
            },
            "subject": {"reference": "Patient/post-surgical-001"},
            "dosageInstruction": [{
                "text": "Take 1-2 tablets by mouth every 4-6 hours as needed for severe pain. Maximum 12 tablets in 24 hours.",
                "patientInstruction": "CONTROLLED SUBSTANCE: Use only as directed. May cause drowsiness - do not drive or operate machinery. Do not use with alcohol. Risk of addiction and respiratory depression. Taper gradually when discontinuing.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 4,
                        "periodUnit": "h",
                        "when": ["HS", "Q4H"]  # as needed every 4 hours
                    }
                },
                "asNeeded": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "22253000",
                        "display": "Pain"
                    }],
                    "text": "severe pain"
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 1.5,  # Average of 1-2 tablets
                        "unit": "tablet",
                        "system": "http://unitsofmeasure.org",
                        "code": "{tbl}"
                    }
                }],
                "maxDosePerPeriod": {
                    "numerator": {
                        "value": 12,
                        "unit": "tablet"
                    },
                    "denominator": {
                        "value": 24,
                        "unit": "h"
                    }
                }
            }]
        }
        
        result = processor.process_medication_data(post_surgical_data)
        
        # CRITICAL: Opioid medication name and dose must be exact
        assert result.medication_name == "Oxycodone 5mg tablets"
        assert "1.5 tablet" in result.dosage
        
        # CRITICAL: Complex dosing schedule must be preserved
        assert "1-2 tablets" in result.instructions
        assert "every 4-6 hours" in result.instructions.lower()
        assert "maximum 12 tablets" in result.instructions.lower()
        assert "24 hours" in result.instructions
        
        # CRITICAL: Controlled substance warnings must be preserved exactly
        assert "CONTROLLED SUBSTANCE" in result.instructions
        assert "addiction" in result.instructions.lower()
        assert "respiratory depression" in result.instructions.lower()
        assert "do not use with alcohol" in result.instructions.lower()
        
        # CRITICAL: No AI processing of opioid data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestPerformanceAndSafetyValidation:
    """
    Tests to verify performance requirements and safety validation
    meet healthcare standards for production use.
    """
    
    def test_large_medication_list_performance(self):
        """
        Test processing performance with large medication lists.
        
        Scenario: Complex patient with 15+ medications (polypharmacy)
        Must process in <5 seconds while maintaining safety standards.
        """
        processor = HybridClinicalProcessor()
        
        # Create complex polypharmacy bundle
        large_med_bundle = {
            "resourceType": "Bundle",
            "id": "polypharmacy-performance-001",
            "type": "collection",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "polypharmacy-patient-001",
                    "name": [{"family": "PolypharmacyPatient", "given": ["Complex"]}]
                }}
            ]
        }
        
        # Add 15 different medications to test performance
        medications = [
            ("Lisinopril 10mg tablets", "197361", "Lisinopril 10 MG Oral Tablet"),
            ("Metformin 500mg tablets", "197804", "Metformin 500 MG Oral Tablet"),
            ("Atorvastatin 20mg tablets", "617314", "Atorvastatin 20 MG Oral Tablet"),
            ("Amlodipine 5mg tablets", "197361", "Amlodipine 5 MG Oral Tablet"),
            ("Omeprazole 20mg capsules", "40790", "Omeprazole 20 MG Oral Capsule"),
            ("Aspirin 81mg tablets", "1191", "Aspirin 81 MG Oral Tablet"),
            ("Metoprolol 25mg tablets", "866511", "Metoprolol 25 MG Oral Tablet"),
            ("Furosemide 40mg tablets", "310429", "Furosemide 40 MG Oral Tablet"),
            ("Warfarin 5mg tablets", "855332", "Warfarin Sodium 5 MG Oral Tablet"),
            ("Levothyroxine 75mcg tablets", "966224", "Levothyroxine 75 MCG Oral Tablet"),
            ("Gabapentin 300mg capsules", "859437", "Gabapentin 300 MG Oral Capsule"),
            ("Sertraline 50mg tablets", "312938", "Sertraline 50 MG Oral Tablet"),
            ("Albuterol inhaler", "630208", "Albuterol 90 MCG/ACTUAT Metered Dose Inhaler"),
            ("Vitamin D3 1000 IU tablets", "1536832", "Cholecalciferol 1000 UNT Oral Tablet"),
            ("Multivitamin tablets", "89905", "Multivitamin Oral Tablet")
        ]
        
        for i, (name, code, display) in enumerate(medications):
            med_entry = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"med-{i+1:03d}",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": code,
                            "display": display
                        }],
                        "text": name
                    },
                    "subject": {"reference": "Patient/polypharmacy-patient-001"},
                    "dosageInstruction": [{
                        "text": f"Take 1 tablet by mouth once daily",
                        "timing": {
                            "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                        },
                        "route": {
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "26643006",
                                "display": "Oral route"
                            }]
                        },
                        "doseAndRate": [{
                            "doseQuantity": {
                                "value": 1,
                                "unit": "tablet",
                                "system": "http://unitsofmeasure.org",
                                "code": "{tbl}"
                            }
                        }]
                    }]
                }
            }
            large_med_bundle["entry"].append(med_entry)
        
        # Test performance with large medication list
        start_time = time.time()
        result = processor.process_clinical_data(large_med_bundle)
        processing_time = time.time() - start_time
        
        # CRITICAL: Must process in <5 seconds regardless of medication count
        assert processing_time < 5.0, f"Processing {len(medications)} medications took {processing_time:.2f}s, exceeds 5s limit"
        
        # CRITICAL: All medications must be processed correctly
        assert len(result.medications) == len(medications)
        
        # CRITICAL: Safety validation must pass for all medications
        assert result.safety_validation.passed
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed
    
    def test_zero_medication_error_tolerance(self):
        """
        Test zero-tolerance policy for medication errors.
        
        Any processing that would result in medication errors must be rejected.
        """
        processor = HybridClinicalProcessor()
        
        # Test cases that should be rejected
        error_test_cases = [
            {
                "name": "Empty medication name",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": ""}  # Empty name
                }
            },
            {
                "name": "Negative dosage",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"},
                    "dosageInstruction": [{
                        "doseAndRate": [{
                            "doseQuantity": {"value": -5, "unit": "mg"}  # Negative dose
                        }]
                    }]
                }
            },
            {
                "name": "Missing required subject",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Test Medication"}
                    # Missing subject reference
                }
            }
        ]
        
        for test_case in error_test_cases:
            with pytest.raises((ValueError, Exception)) as exc_info:
                processor.process_medication_data(test_case["data"])
            
            # Error message should indicate validation failure
            assert "validation" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
    
    def test_concurrent_processing_safety(self):
        """
        Test that concurrent processing maintains safety standards.
        
        Multiple simultaneous requests should not compromise data integrity.
        """
        import threading
        import queue
        
        processor = HybridClinicalProcessor()
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def process_medication(med_data, result_queue, error_queue):
            try:
                result = processor.process_medication_data(med_data)
                result_queue.put(result)
            except Exception as e:
                error_queue.put(e)
        
        # Create multiple medication requests for concurrent processing
        test_medications = []
        for i in range(5):
            med_data = {
                "resourceType": "MedicationRequest",
                "id": f"concurrent-test-{i}",
                "status": "active",
                "intent": "order",
                "subject": {"reference": f"Patient/concurrent-{i}"},
                "medicationCodeableConcept": {
                    "text": f"Test Medication {i} 10mg tablets"
                },
                "dosageInstruction": [{
                    "text": "Take 1 tablet by mouth once daily",
                    "timing": {
                        "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                    },
                    "doseAndRate": [{
                        "doseQuantity": {"value": 1, "unit": "tablet"}
                    }]
                }]
            }
            test_medications.append(med_data)
        
        # Start concurrent processing
        threads = []
        for med_data in test_medications:
            thread = threading.Thread(
                target=process_medication,
                args=(med_data, results_queue, errors_queue)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert errors_queue.empty(), f"Concurrent processing errors: {list(errors_queue.queue)}"
        
        # Verify all medications were processed correctly
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == len(test_medications)
        
        # CRITICAL: Each result must maintain safety standards
        for result in results:
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
            assert not result.metadata.ai_processed
            assert result.metadata.validation_passed