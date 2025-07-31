"""
Comprehensive safety validation tests for zero medication error tolerance.

This module implements rigorous safety testing that ensures the processor
meets healthcare-grade safety standards with zero tolerance for medication
errors that could compromise patient safety.

Safety Test Categories:
1. Zero Medication Error Tolerance
2. Critical Field Preservation Validation
3. AI Processing Prohibition Enforcement
4. Data Integrity Verification
5. Concurrent Processing Safety
6. Error Boundary Testing
7. Fail-Safe Mechanisms
8. Healthcare Compliance Validation
"""

import pytest
import hashlib
import json
import threading
import time
from typing import Dict, Any, List
from decimal import Decimal
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import SafetyLevel, ProcessingType, SafetyValidation
from src.models.medication import MedicationRequest
from pydantic import ValidationError


class TestZeroMedicationErrorTolerance:
    """
    Test zero-tolerance policy for medication errors.
    Any processing that could result in medication errors must be rejected.
    """
    
    def test_medication_name_error_prevention(self):
        """
        Test prevention of medication name errors that could be life-threatening.
        """
        processor = HybridClinicalProcessor()
        
        # Test cases that should be rejected to prevent medication errors
        dangerous_name_cases = [
            {
                "name": "Empty medication name",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": ""}  # Empty - could cause wrong medication
                },
                "expected_error": "medication text cannot be empty"
            },
            {
                "name": "Whitespace-only medication name", 
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "   "}  # Whitespace only
                },
                "expected_error": "medication text cannot be empty"
            },
            {
                "name": "Invalid characters in medication name",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active", 
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Lisinopril<script>alert('hack')</script>"}  # XSS attempt
                },
                "expected_error": "invalid characters"
            }
        ]
        
        for test_case in dangerous_name_cases:
            with pytest.raises((ValueError, ValidationError)) as exc_info:
                processor.process_medication_data(test_case["data"])
            
            # Verify appropriate error message
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in ["validation", "invalid", "empty", "required"])
    
    def test_dosage_error_prevention(self):
        """
        Test prevention of dosage errors that could cause overdose or underdose.
        """
        processor = HybridClinicalProcessor()
        
        dangerous_dosage_cases = [
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
                "name": "Zero dosage",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"},
                    "dosageInstruction": [{
                        "doseAndRate": [{
                            "doseQuantity": {"value": 0, "unit": "mg"}  # Zero dose
                        }]
                    }]
                }
            },
            {
                "name": "Extremely high dosage",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Digoxin"},  # Narrow therapeutic window
                    "dosageInstruction": [{
                        "doseAndRate": [{
                            "doseQuantity": {"value": 10000, "unit": "mg"}  # Dangerously high
                        }]
                    }]
                }
            }
        ]
        
        for test_case in dangerous_dosage_cases:
            with pytest.raises((ValueError, ValidationError)) as exc_info:
                processor.process_medication_data(test_case["data"])
            
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in ["positive", "value", "validation", "dosage"])
    
    def test_frequency_error_prevention(self):
        """
        Test prevention of frequency errors that could cause medication timing errors.
        """
        processor = HybridClinicalProcessor()
        
        dangerous_frequency_cases = [
            {
                "name": "Negative frequency",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"},
                    "dosageInstruction": [{
                        "timing": {
                            "repeat": {
                                "frequency": -1,  # Negative frequency
                                "period": 1,
                                "periodUnit": "d"
                            }
                        },
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }
            },
            {
                "name": "Zero frequency",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"},
                    "dosageInstruction": [{
                        "timing": {
                            "repeat": {
                                "frequency": 0,  # Zero frequency
                                "period": 1,
                                "periodUnit": "d"
                            }
                        },
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }
            },
            {
                "name": "Negative period",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"},
                    "dosageInstruction": [{
                        "timing": {
                            "repeat": {
                                "frequency": 1,
                                "period": -1,  # Negative period
                                "periodUnit": "d"
                            }
                        },
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }
            }
        ]
        
        for test_case in dangerous_frequency_cases:
            with pytest.raises((ValueError, ValidationError)) as exc_info:
                processor.process_medication_data(test_case["data"])
            
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in ["positive", "frequency", "period", "validation"])
    
    def test_critical_field_missing_prevention(self):
        """
        Test prevention of processing when critical required fields are missing.
        """
        processor = HybridClinicalProcessor()
        
        missing_field_cases = [
            {
                "name": "Missing subject reference",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Test Medication"}
                    # Missing subject - critical for patient safety
                }
            },
            {
                "name": "Missing medication specification",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"}
                    # Missing medicationCodeableConcept or medicationReference
                }
            },
            {
                "name": "Missing status",
                "data": {
                    "resourceType": "MedicationRequest",
                    "intent": "order",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"}
                    # Missing status - critical for determining if medication is active
                }
            },
            {
                "name": "Missing intent",
                "data": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "subject": {"reference": "Patient/test"},
                    "medicationCodeableConcept": {"text": "Test Medication"}
                    # Missing intent - critical for understanding medication purpose
                }
            }
        ]
        
        for test_case in missing_field_cases:
            with pytest.raises((ValueError, ValidationError)) as exc_info:
                processor.process_medication_data(test_case["data"])
            
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in ["required", "missing", "field required", "validation"])


class TestCriticalFieldPreservation:
    """
    Test that critical medication fields are preserved exactly without alteration.
    """
    
    def test_medication_name_exact_preservation(self):
        """
        Test that medication names are preserved character-for-character.
        """
        processor = HybridClinicalProcessor()
        
        # Test various medication name formats that must be preserved exactly
        critical_medication_names = [
            "Lisinopril 10 MG Oral Tablet",
            "Insulin Glargine 100 unit/mL Pen Injector", 
            "Warfarin Sodium 2.5 MG Oral Tablet",
            "Metformin Hydrochloride 500 MG Oral Tablet",
            "Digoxin 0.125 MG Oral Tablet",
            "Epinephrine 0.3 MG/0.3 ML Auto-Injector",
            "Nitroglycerin 0.4 MG Sublingual Tablet",
            "Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler"
        ]
        
        for med_name in critical_medication_names:
            test_data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/test"},
                "medicationCodeableConcept": {"text": med_name},
                "dosageInstruction": [{
                    "text": "Take as directed",
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                }]
            }
            
            result = processor.process_medication_data(test_data)
            
            # CRITICAL: Medication name must be preserved character-for-character
            assert result.medication_name == med_name, f"Medication name altered: '{med_name}' -> '{result.medication_name}'"
            
            # CRITICAL: No AI processing flag set for medication name
            assert not result.metadata.ai_processed
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
    
    def test_dosage_precision_preservation(self):
        """
        Test that dosage values maintain exact precision for critical medications.
        """
        processor = HybridClinicalProcessor()
        
        # Critical dosages where precision is life-or-death
        precision_critical_cases = [
            {"value": 0.125, "unit": "mg", "medication": "Digoxin"},  # Narrow therapeutic window
            {"value": 0.25, "unit": "mg", "medication": "Levothyroxine"},  # Thyroid precision critical
            {"value": 2.5, "unit": "mg", "medication": "Warfarin"},  # Anticoagulation precision
            {"value": 7.5, "unit": "units", "medication": "Insulin"},  # Pediatric insulin precision
            {"value": 0.3, "unit": "mg", "medication": "Epinephrine"},  # Emergency dose precision
            {"value": 12.5, "unit": "mcg", "medication": "Fentanyl"},  # Opioid precision critical
        ]
        
        for case in precision_critical_cases:
            test_data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/test"},
                "medicationCodeableConcept": {"text": f"{case['medication']} {case['value']}{case['unit']} tablets"},
                "dosageInstruction": [{
                    "text": f"Take {case['value']} {case['unit']} as directed",
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                    "doseAndRate": [{
                        "doseQuantity": {
                            "value": case['value'],
                            "unit": case['unit']
                        }
                    }]
                }]
            }
            
            result = processor.process_medication_data(test_data)
            
            # CRITICAL: Exact dosage precision preserved
            expected_dosage = f"{case['value']} {case['unit']}"
            assert expected_dosage in result.dosage, f"Dosage precision lost: expected '{expected_dosage}' in '{result.dosage}'"
            
            # CRITICAL: No AI processing of dosage data
            assert not result.metadata.ai_processed
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
    
    def test_frequency_timing_exact_preservation(self):
        """
        Test that medication timing and frequency are preserved exactly.
        """
        processor = HybridClinicalProcessor()
        
        # Critical timing scenarios where exact preservation is essential
        timing_critical_cases = [
            {
                "frequency": 1, "period": 1, "periodUnit": "d",
                "expected": "1 time(s) per 1 d",
                "description": "Once daily"
            },
            {
                "frequency": 2, "period": 1, "periodUnit": "d", 
                "expected": "2 time(s) per 1 d",
                "description": "Twice daily"
            },
            {
                "frequency": 3, "period": 1, "periodUnit": "d",
                "expected": "3 time(s) per 1 d", 
                "description": "Three times daily"
            },
            {
                "frequency": 1, "period": 6, "periodUnit": "h",
                "expected": "1 time(s) per 6 h",
                "description": "Every 6 hours"
            },
            {
                "frequency": 1, "period": 12, "periodUnit": "h",
                "expected": "1 time(s) per 12 h",
                "description": "Every 12 hours"
            }
        ]
        
        for case in timing_critical_cases:
            test_data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/test"},
                "medicationCodeableConcept": {"text": "Test Medication 10mg"},
                "dosageInstruction": [{
                    "text": f"Take as directed - {case['description']}",
                    "timing": {
                        "repeat": {
                            "frequency": case['frequency'],
                            "period": case['period'],
                            "periodUnit": case['periodUnit']
                        }
                    },
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                }]
            }
            
            result = processor.process_medication_data(test_data)
            
            # CRITICAL: Exact frequency preserved
            assert case['expected'] in result.frequency, f"Frequency not preserved: expected '{case['expected']}' in '{result.frequency}'"
            
            # CRITICAL: No AI processing of timing data
            assert not result.metadata.ai_processed
            assert result.metadata.safety_level == SafetyLevel.CRITICAL


class TestAIProcessingProhibitionEnforcement:
    """
    Test that AI processing is absolutely prohibited for critical medication fields.
    """
    
    def test_medication_name_ai_prohibition(self):
        """
        Test that medication names are never processed by AI.
        """
        processor = HybridClinicalProcessor()
        
        # Test that AI processing rules correctly prohibit AI for medication names
        assert not processor.enforce_ai_processing_rules("medication", "medication_name")
        assert not processor.enforce_ai_processing_rules("medication", "dosage")
        assert not processor.enforce_ai_processing_rules("medication", "frequency")
        assert not processor.enforce_ai_processing_rules("medication", "route")
        assert not processor.enforce_ai_processing_rules("medication", "instructions")
        
        # Test that only specific narrative fields allow AI
        assert processor.enforce_ai_processing_rules("medication", "purpose")
        assert processor.enforce_ai_processing_rules("medication", "important_notes")
        
        # Test that lab values never allow AI
        assert not processor.enforce_ai_processing_rules("lab", "test_name")
        assert not processor.enforce_ai_processing_rules("lab", "value")
        assert not processor.enforce_ai_processing_rules("lab", "reference_range")
        assert not processor.enforce_ai_processing_rules("lab", "units")
        
        # Test that vital signs never allow AI
        assert not processor.enforce_ai_processing_rules("vital", "measurement_type")
        assert not processor.enforce_ai_processing_rules("vital", "value")
        assert not processor.enforce_ai_processing_rules("vital", "units")
        assert not processor.enforce_ai_processing_rules("vital", "timestamp")
    
    def test_metadata_ai_processing_flags(self):
        """
        Test that metadata correctly tracks AI processing prohibition.
        """
        processor = HybridClinicalProcessor()
        
        test_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": "Critical Test Medication 5mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(test_data)
        
        # CRITICAL: AI processing flags must be False for all critical fields
        assert not result.metadata.ai_processed  # Overall flag
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert result.metadata.processing_type == ProcessingType.PRESERVED
        
        # Validate that safety validation correctly tracks AI processing
        safety_validation = processor.validate_safety_requirements(test_data, result.model_dump())
        
        # CRITICAL: All critical fields must show no AI processing
        critical_fields = ["medication_name", "dosage", "frequency", "instructions"]
        for field in critical_fields:
            assert not safety_validation.ai_processing_flags.get(field, False), f"AI processing flag incorrectly set for {field}"


class TestDataIntegrityVerification:
    """
    Test data integrity verification mechanisms to ensure no corruption.
    """
    
    def test_preservation_hash_integrity(self):
        """
        Test that preservation hashes correctly verify data integrity.
        """
        processor = HybridClinicalProcessor()
        
        test_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": "Integrity Test Medication 10mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(test_data)
        
        # CRITICAL: Preservation hash must be generated
        assert result.metadata.preservation_hash is not None
        assert len(result.metadata.preservation_hash) == 64  # SHA-256 hash length
        
        # Verify hash consistency - same input should produce same hash
        result2 = processor.process_medication_data(test_data)
        assert result.metadata.preservation_hash == result2.metadata.preservation_hash
        
        # Verify hash changes with data modification
        modified_data = test_data.copy()
        modified_data["medicationCodeableConcept"]["text"] = "Modified Medication 10mg"
        result3 = processor.process_medication_data(modified_data)
        assert result.metadata.preservation_hash != result3.metadata.preservation_hash
    
    def test_safety_validation_comprehensive_checks(self):
        """
        Test that safety validation performs comprehensive integrity checks.
        """
        processor = HybridClinicalProcessor()
        
        original_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": "Safety Validation Test 5mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet twice daily",
                "timing": {"repeat": {"frequency": 2, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(original_data)
        processed_data = result.model_dump()
        
        # Perform comprehensive safety validation
        safety_validation = processor.validate_safety_requirements(original_data, processed_data)
        
        # CRITICAL: Safety validation must pass
        assert safety_validation.passed
        assert len(safety_validation.errors) == 0
        assert safety_validation.data_type == "medication"
        
        # CRITICAL: All critical fields marked as preserved
        critical_fields = ["medication_name", "dosage", "frequency", "instructions"]
        for field in critical_fields:
            assert safety_validation.critical_fields_preserved.get(field, False), f"Critical field {field} not marked as preserved"
        
        # CRITICAL: No AI processing flags set for critical fields
        for field in critical_fields:
            assert not safety_validation.ai_processing_flags.get(field, False), f"AI processing flag incorrectly set for {field}"
    
    def test_error_detection_data_corruption(self):
        """
        Test that safety validation detects data corruption or alteration.
        """
        processor = HybridClinicalProcessor()
        
        original_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": "Original Medication 10mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Simulate corrupted processed data
        corrupted_processed_data = {
            "medication_name": "Modified Medication 10mg",  # Name was altered
            "dosage": "2 tablet",  # Dosage was altered
            "frequency": "1 time(s) per 1 d",
            "instructions": "Take 1 tablet once daily"
        }
        
        # Safety validation should detect corruption
        safety_validation = processor.validate_safety_requirements(original_data, corrupted_processed_data)
        
        # CRITICAL: Validation must fail when data is corrupted
        assert not safety_validation.passed
        assert len(safety_validation.errors) > 0
        
        # Verify specific error detection
        error_messages = " ".join(safety_validation.errors).lower()
        assert "medication name was altered" in error_messages or "altered" in error_messages


class TestConcurrentProcessingSafety:
    """
    Test that concurrent processing maintains safety standards.
    """
    
    def test_thread_safety_medication_processing(self):
        """
        Test that concurrent medication processing maintains safety standards.
        """
        import threading
        import queue
        
        processor = HybridClinicalProcessor()
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def process_medication_safely(med_data, result_queue, error_queue, thread_id):
            try:
                result = processor.process_medication_data(med_data)
                # Add thread ID to track which thread processed what
                result_queue.put((thread_id, result))
            except Exception as e:
                error_queue.put((thread_id, e))
        
        # Create multiple different medications for concurrent processing
        test_medications = []
        for i in range(10):
            med_data = {
                "resourceType": "MedicationRequest",
                "id": f"concurrent-safety-{i}",
                "status": "active",
                "intent": "order",
                "subject": {"reference": f"Patient/concurrent-{i}"},
                "medicationCodeableConcept": {"text": f"Thread Safety Test Med {i} {(i+1)*5}mg tablets"},
                "dosageInstruction": [{
                    "text": f"Take 1 tablet {['once', 'twice', 'three times'][i % 3]} daily",
                    "timing": {"repeat": {"frequency": (i % 3) + 1, "period": 1, "periodUnit": "d"}},
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                }]
            }
            test_medications.append(med_data)
        
        # Start concurrent processing threads
        threads = []
        for i, med_data in enumerate(test_medications):
            thread = threading.Thread(
                target=process_medication_safely,
                args=(med_data, results_queue, errors_queue, i)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # CRITICAL: No errors should occur during concurrent processing
        assert errors_queue.empty(), f"Concurrent processing errors: {list(errors_queue.queue)}"
        
        # Verify all medications processed correctly
        results = {}
        while not results_queue.empty():
            thread_id, result = results_queue.get()
            results[thread_id] = result
        
        assert len(results) == len(test_medications)
        
        # CRITICAL: Each result maintains safety standards
        for thread_id, result in results.items():
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
            assert not result.metadata.ai_processed
            assert result.metadata.validation_passed
            
            # Verify correct medication processed by this thread
            expected_name = f"Thread Safety Test Med {thread_id} {(thread_id+1)*5}mg tablets"
            assert result.medication_name == expected_name
    
    def test_race_condition_prevention(self):
        """
        Test prevention of race conditions that could compromise safety.
        """
        import threading
        import time
        
        processor = HybridClinicalProcessor()
        
        # Shared state to test for race conditions
        shared_results = []
        shared_lock = threading.Lock()
        
        def process_with_shared_state(med_data, thread_id):
            # Simulate some processing time
            time.sleep(0.01)
            
            result = processor.process_medication_data(med_data)
            
            # Use lock to safely update shared state
            with shared_lock:
                shared_results.append((thread_id, result))
        
        # Create medication data for race condition testing
        race_condition_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/race-test"},
            "medicationCodeableConcept": {"text": "Race Condition Test Medication 10mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Start multiple threads processing same medication
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=process_with_shared_state,
                args=(race_condition_data, i)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # CRITICAL: All threads should complete successfully
        assert len(shared_results) == num_threads
        
        # CRITICAL: All results should be identical (no race condition corruption)
        first_result = shared_results[0][1]
        for thread_id, result in shared_results:
            assert result.medication_name == first_result.medication_name
            assert result.dosage == first_result.dosage
            assert result.frequency == first_result.frequency
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
            assert not result.metadata.ai_processed


class TestFailSafeMechanisms:
    """
    Test fail-safe mechanisms that prevent unsafe operation under error conditions.
    """
    
    def test_graceful_degradation_invalid_input(self):
        """
        Test that system fails safely when given invalid input.
        """
        processor = HybridClinicalProcessor()
        
        # Test various invalid input scenarios
        invalid_inputs = [
            None,  # Null input
            "",    # Empty string
            {},    # Empty dictionary
            {"invalid": "structure"},  # Wrong structure
            {"resourceType": "InvalidType"},  # Wrong resource type
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises((ValueError, ValidationError, TypeError, AttributeError)):
                processor.process_medication_data(invalid_input)
    
    def test_memory_protection_large_input(self):
        """
        Test protection against memory exhaustion attacks.
        """
        processor = HybridClinicalProcessor()
        
        # Create excessively large input to test memory protection
        large_instruction = "X" * 100000  # 100KB string
        
        large_input_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/memory-test"},
            "medicationCodeableConcept": {"text": "Memory Test Medication"},
            "dosageInstruction": [{
                "text": large_instruction,  # Excessively large instruction
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Should either process efficiently or reject gracefully
        try:
            start_time = time.time()
            result = processor.process_medication_data(large_input_data)
            processing_time = time.time() - start_time
            
            # If processed, should be within reasonable time limits
            assert processing_time < 10.0, f"Large input processing took {processing_time:.2f}s, too slow"
            
            # Safety standards must still be maintained
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
            assert not result.metadata.ai_processed
            
        except (ValueError, ValidationError) as e:
            # Graceful rejection is acceptable for oversized input
            assert "too large" in str(e).lower() or "size" in str(e).lower() or "length" in str(e).lower()
    
    def test_error_isolation_partial_failures(self):
        """
        Test that partial failures don't corrupt successful processing.
        """
        processor = HybridClinicalProcessor()
        
        # Bundle with mix of valid and invalid medications
        mixed_bundle = {
            "resourceType": "Bundle",
            "id": "error-isolation-test",
            "type": "collection",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "error-isolation-patient",
                    "name": [{"family": "ErrorTest", "given": ["Patient"]}]
                }},
                # Valid medication
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "valid-med",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/error-isolation-patient"},
                    "medicationCodeableConcept": {"text": "Valid Medication 10mg"},
                    "dosageInstruction": [{
                        "text": "Take 1 tablet once daily",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }},
                # Invalid medication (will be skipped)
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "invalid-med",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/error-isolation-patient"},
                    "medicationCodeableConcept": {"text": ""},  # Empty name - invalid
                    "dosageInstruction": [{
                        "text": "Invalid dosage",
                        "timing": {"repeat": {"frequency": -1, "period": 1, "periodUnit": "d"}},  # Invalid frequency
                        "doseAndRate": [{"doseQuantity": {"value": -5, "unit": "tablet"}}]  # Invalid dose
                    }]
                }}
            ]
        }
        
        # Process bundle - should handle invalid entries gracefully
        result = processor.process_clinical_data(mixed_bundle)
        
        # CRITICAL: Valid medications should be processed successfully
        assert len(result.medications) == 1  # Only valid medication processed
        
        valid_med = result.medications[0]
        assert valid_med.medication_name == "Valid Medication 10mg"
        assert valid_med.metadata.safety_level == SafetyLevel.CRITICAL
        assert not valid_med.metadata.ai_processed
        
        # Overall safety validation should reflect partial success
        assert result.safety_validation.passed  # Valid data processed successfully
        assert len(result.safety_validation.warnings) >= 0  # May have warnings about skipped entries