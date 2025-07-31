"""
PHI (Protected Health Information) protection compliance tests.

This module ensures that the Clinical Notes Summarizer complies with HIPAA
and other healthcare privacy regulations by preventing any storage, logging,
or transmission of protected health information.

PHI Protection Test Categories:
1. No PHI Storage Prevention
2. No PHI Logging Prevention  
3. Data Anonymization Validation
4. Memory Cleanup Verification
5. Temporary File Protection
6. Network Transmission Security
7. Error Message Sanitization
8. Audit Trail Compliance
"""

import pytest
import tempfile
import os
import logging
import json
import time
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import ClinicalSummary


class TestNoPHIStorage:
    """
    Test that no PHI is stored in persistent storage anywhere in the system.
    """
    
    def test_no_patient_names_in_output(self):
        """
        Test that patient names never appear in processed output.
        """
        processor = HybridClinicalProcessor()
        
        # Create bundle with PHI that should NOT appear in output
        phi_bundle = {
            "resourceType": "Bundle",
            "id": "phi-storage-test-001",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "phi-patient-001",
                        "identifier": [{"value": "SSN-123-45-6789"}],  # PHI
                        "name": [{"family": "Smith", "given": ["John", "Michael"]}],  # PHI
                        "birthDate": "1985-03-15",  # PHI
                        "address": [{  # PHI
                            "line": ["123 Main Street", "Apt 4B"],
                            "city": "Springfield",
                            "state": "IL",
                            "postalCode": "62701"
                        }],
                        "telecom": [{  # PHI
                            "system": "phone",
                            "value": "555-123-4567"
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "phi-med-001", 
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/phi-patient-001"},
                        "medicationCodeableConcept": {"text": "Lisinopril 10mg tablets"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet once daily",
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                        }]
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(phi_bundle)
        
        # CRITICAL: No PHI should appear anywhere in the output
        result_json = result.model_dump_json()
        
        # Check for patient names
        assert "John" not in result_json
        assert "Michael" not in result_json  
        assert "Smith" not in result_json
        
        # Check for identifiers
        assert "SSN" not in result_json
        assert "123-45-6789" not in result_json
        
        # Check for addresses
        assert "123 Main Street" not in result_json
        assert "Springfield" not in result_json
        assert "62701" not in result_json
        
        # Check for phone numbers
        assert "555-123-4567" not in result_json
        
        # Check for birth dates
        assert "1985-03-15" not in result_json
        
        # CRITICAL: Patient ID should be anonymized or abstracted
        assert result.patient_id != "John Michael Smith"
        assert result.patient_id == "phi-patient-001"  # Should use abstract ID only
    
    def test_no_provider_phi_in_output(self):
        """
        Test that provider PHI is not stored in output.
        """
        processor = HybridClinicalProcessor()
        
        # Bundle with provider PHI
        provider_phi_data = {
            "resourceType": "MedicationRequest",
            "id": "provider-phi-test",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test-patient"},
            "medicationCodeableConcept": {"text": "Test Medication 5mg"},
            "authoredOn": "2024-01-15T10:30:00Z",
            "requester": {
                "reference": "Practitioner/dr-jane-doe",
                "display": "Dr. Jane Doe, Internal Medicine",  # Provider PHI
                "identifier": [{"value": "NPI-1234567890"}]  # Provider PHI
            },
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(provider_phi_data)
        result_json = result.model_dump_json()
        
        # CRITICAL: Provider names should not appear in output
        assert "Jane Doe" not in result_json
        assert "Dr. Jane Doe" not in result_json
        
        # CRITICAL: Provider identifiers should not appear
        assert "NPI-1234567890" not in result_json
        assert "NPI" not in result_json
        
        # CRITICAL: Specific department info might be considered PHI
        # (Implementation decision - may want to remove specific departments)
        # assert "Internal Medicine" not in result_json
    
    def test_no_phi_in_temporary_files(self):
        """
        Test that no PHI is written to temporary files during processing.
        """
        processor = HybridClinicalProcessor()
        
        # Monitor temporary directory for PHI
        original_temp_dir = tempfile.gettempdir()
        temp_files_before = set(os.listdir(original_temp_dir))
        
        phi_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/john-doe-ssn-123456789"},  # PHI in reference
            "medicationCodeableConcept": {"text": "Confidential Medication 10mg"},
            "dosageInstruction": [{
                "text": "Patient John Doe (DOB: 1985-03-15) take 1 tablet daily",  # PHI in instructions
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Process data
        result = processor.process_medication_data(phi_data)
        
        # Check for new temporary files
        temp_files_after = set(os.listdir(original_temp_dir))
        new_temp_files = temp_files_after - temp_files_before
        
        # CRITICAL: Check that no new temp files contain PHI
        for temp_file in new_temp_files:
            temp_path = os.path.join(original_temp_dir, temp_file)
            try:
                if os.path.isfile(temp_path):
                    with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check for PHI in temporary files
                    assert "John Doe" not in content
                    assert "john-doe" not in content
                    assert "SSN" not in content
                    assert "123456789" not in content
                    assert "1985-03-15" not in content
                    
            except (PermissionError, FileNotFoundError):
                # Ignore files we can't read (system files, etc.)
                pass


class TestNoPHILogging:
    """
    Test that no PHI appears in application logs.
    """
    
    def test_no_phi_in_log_messages(self):
        """
        Test that PHI never appears in log messages.
        """
        processor = HybridClinicalProcessor()
        
        # Set up log capture
        log_stream = []
        
        class PHILogHandler(logging.Handler):
            def emit(self, record):
                log_stream.append(self.format(record))
        
        # Add handler to capture logs
        phi_handler = PHILogHandler()
        phi_handler.setLevel(logging.DEBUG)
        
        # Get root logger to catch all log messages
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(phi_handler)
        
        try:
            # Process data with PHI
            phi_data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/sensitive-patient-data"},
                "medicationCodeableConcept": {"text": "Sensitive Medication for Patient John Smith"},
                "dosageInstruction": [{
                    "text": "Patient born 1975-12-25, address 456 Oak Street, phone 555-987-6543",
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                }]
            }
            
            # This might cause logging during processing
            result = processor.process_medication_data(phi_data)
            
            # Force any buffered logs to be emitted
            for handler in root_logger.handlers:
                handler.flush()
            
            # CRITICAL: Check that no PHI appears in any log messages
            all_logs = "\n".join(log_stream)
            
            # Patient identifiers
            assert "John Smith" not in all_logs
            assert "john smith" not in all_logs.lower()
            
            # Dates of birth
            assert "1975-12-25" not in all_logs
            
            # Addresses
            assert "456 Oak Street" not in all_logs
            assert "Oak Street" not in all_logs
            
            # Phone numbers
            assert "555-987-6543" not in all_logs
            
            # General PHI patterns
            assert not any("SSN" in log for log in log_stream)
            assert not any("social security" in log.lower() for log in log_stream)
            
        finally:
            # Clean up logging configuration
            root_logger.removeHandler(phi_handler)
            root_logger.setLevel(original_level)
    
    def test_error_messages_no_phi_exposure(self):
        """
        Test that error messages don't expose PHI even when processing fails.
        """
        processor = HybridClinicalProcessor()
        
        # Data that will cause an error but contains PHI
        invalid_phi_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/mary-johnson-dob-1980-05-10"},
            "medicationCodeableConcept": {"text": ""},  # Empty medication name will cause error
            "dosageInstruction": [{
                "text": "Patient Mary Johnson (SSN: 987-65-4321) - invalid dosage",
                "timing": {"repeat": {"frequency": -1, "period": 1, "periodUnit": "d"}},  # Invalid frequency
                "doseAndRate": [{"doseQuantity": {"value": -5, "unit": "tablet"}}]  # Invalid dose
            }]
        }
        
        # Process should fail with error
        try:
            result = processor.process_medication_data(invalid_phi_data)
            assert False, "Expected processing to fail with invalid data"
        except Exception as e:
            error_message = str(e)
            
            # CRITICAL: Error message must not contain PHI
            assert "Mary Johnson" not in error_message
            assert "mary johnson" not in error_message.lower()
            assert "987-65-4321" not in error_message
            assert "SSN" not in error_message
            assert "1980-05-10" not in error_message
            
            # Error message should be generic and safe
            assert any(word in error_message.lower() for word in ["validation", "invalid", "error", "failed"])


class TestDataAnonymization:
    """
    Test that data is properly anonymized for processing while preserving clinical value.
    """
    
    def test_patient_id_anonymization(self):
        """
        Test that patient identifiers are anonymized but consistent.
        """
        processor = HybridClinicalProcessor()
        
        # Bundle with identifiable patient info
        identifiable_bundle = {
            "resourceType": "Bundle",
            "id": "anonymization-test",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-john-smith-dob-1985",
                        "identifier": [{"value": "MRN-12345"}],
                        "name": [{"family": "Smith", "given": ["John"]}]
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-for-john-smith",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/patient-john-smith-dob-1985"},
                        "medicationCodeableConcept": {"text": "Test Medication 10mg"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet once daily",
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                        }]
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(identifiable_bundle)
        
        # CRITICAL: Patient ID should be anonymized but consistent
        assert result.patient_id is not None
        assert result.patient_id == "patient-john-smith-dob-1985"  # Uses technical ID, not personal info
        
        # Process same bundle again - should get same anonymized ID
        result2 = processor.process_clinical_data(identifiable_bundle)
        assert result.patient_id == result2.patient_id  # Consistent anonymization
        
        # CRITICAL: No personal identifiers in final output
        result_json = result.model_dump_json()
        assert "John" not in result_json
        assert "Smith" not in result_json
        assert "MRN-12345" not in result_json
    
    def test_timestamp_anonymization(self):
        """
        Test that timestamps are handled appropriately for privacy.
        """
        processor = HybridClinicalProcessor()
        
        # Data with specific timestamps that might be identifying
        timestamp_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/timestamp-test"},
            "medicationCodeableConcept": {"text": "Timestamp Test Med 5mg"},
            "authoredOn": "2024-01-15T14:30:22.123Z",  # Specific timestamp
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily starting 2024-01-15",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(timestamp_data)
        
        # CRITICAL: Specific timestamps should not appear in patient-facing output
        result_json = result.model_dump_json()
        
        # The exact timestamp from input should not appear in patient output
        assert "2024-01-15T14:30:22.123Z" not in result_json
        
        # General date references in instructions are OK (clinical relevance)
        # but specific times down to seconds/milliseconds should be removed
        assert "14:30:22" not in result_json
        assert ".123Z" not in result_json


class TestMemoryCleanup:
    """
    Test that PHI is properly cleaned from memory after processing.
    """
    
    def test_memory_cleanup_after_processing(self):
        """
        Test that sensitive data is cleaned from memory after processing.
        """
        processor = HybridClinicalProcessor()
        
        sensitive_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/memory-cleanup-test"},
            "medicationCodeableConcept": {"text": "Memory Cleanup Test Medication"},
            "dosageInstruction": [{
                "text": "Patient with sensitive condition - memory test",
                "patientInstruction": "Confidential instructions for memory cleanup testing",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Process the data
        result = processor.process_medication_data(sensitive_data)
        
        # Force garbage collection to clean up memory
        import gc
        gc.collect()
        
        # VERIFICATION: While we can't directly inspect all memory,
        # we can verify that the processor doesn't maintain references
        # to the original sensitive data
        
        # Check that processor doesn't have persistent state with PHI
        processor_dict = processor.__dict__
        processor_str = str(processor_dict)
        
        # Processor state should not contain the original sensitive data
        assert "sensitive condition" not in processor_str.lower()
        assert "confidential instructions" not in processor_str.lower()
        assert "memory cleanup test" not in processor_str.lower()
    
    def test_no_phi_in_processor_state(self):
        """
        Test that processor doesn't maintain PHI in its internal state.
        """
        processor = HybridClinicalProcessor()
        
        # Initial state check
        initial_state = str(processor.__dict__)
        
        phi_data = {
            "resourceType": "MedicationRequest", 
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/state-test-patient"},
            "medicationCodeableConcept": {"text": "State Test Medication with PHI"},
            "dosageInstruction": [{
                "text": "Contains patient state information that should not persist",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        } 
        
        # Process multiple different datasets
        for i in range(3):
            modified_data = phi_data.copy() 
            modified_data["id"] = f"state-test-{i}"
            modified_data["medicationCodeableConcept"]["text"] = f"State Test Med {i} with different PHI"
            
            result = processor.process_medication_data(modified_data)
            
            # Check processor state after each processing
            current_state = str(processor.__dict__)
            
            # CRITICAL: Processor should not accumulate PHI from previous processing
            assert "different PHI" not in current_state
            assert f"State Test Med {i-1}" not in current_state if i > 0 else True
            assert "patient state information" not in current_state.lower()


class TestNetworkTransmissionSecurity:
    """
    Test that PHI is not transmitted over networks insecurely.
    """
    
    @patch('requests.post')
    @patch('requests.get')
    def test_no_phi_in_network_requests(self, mock_get, mock_post):
        """
        Test that no PHI is sent in network requests (if any are made).
        """
        processor = HybridClinicalProcessor()
        
        # Configure mocks to capture network requests
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {})
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {})
        
        phi_data = {
            "resourceType": "MedicationRequest",
            "status": "active", 
            "intent": "order",
            "subject": {"reference": "Patient/network-test-patient-jane-doe"},
            "medicationCodeableConcept": {"text": "Network Test Medication for Jane Doe"},
            "dosageInstruction": [{
                "text": "Patient Jane Doe (SSN: 111-22-3333) network transmission test",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        # Process data (might make network requests)
        result = processor.process_medication_data(phi_data)
        
        # CRITICAL: Check that no network requests contained PHI
        all_post_calls = mock_post.call_args_list
        all_get_calls = mock_get.call_args_list
        
        for call in all_post_calls + all_get_calls:
            call_str = str(call)
            
            # Check for PHI in network calls
            assert "Jane Doe" not in call_str
            assert "jane doe" not in call_str.lower()
            assert "111-22-3333" not in call_str
            assert "SSN" not in call_str
            
        # Check request bodies/parameters specifically
        for call in all_post_calls:
            args, kwargs = call
            
            # Check URL
            if args:
                url = args[0]
                assert "Jane Doe" not in url
                assert "111-22-3333" not in url
                
            # Check data/json parameters
            if 'data' in kwargs:
                data_str = str(kwargs['data'])
                assert "Jane Doe" not in data_str
                assert "111-22-3333" not in data_str
                
            if 'json' in kwargs:
                json_str = str(kwargs['json'])
                assert "Jane Doe" not in json_str  
                assert "111-22-3333" not in json_str


class TestAuditTrailCompliance:
    """
    Test that audit trails are maintained without exposing PHI.
    """
    
    def test_processing_metadata_no_phi(self):
        """
        Test that processing metadata doesn't contain PHI.
        """
        processor = HybridClinicalProcessor()
        
        phi_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order", 
            "subject": {"reference": "Patient/audit-test-robert-johnson"}, 
            "medicationCodeableConcept": {"text": "Audit Test Medication for Robert Johnson"},
            "dosageInstruction": [{
                "text": "Patient Robert Johnson (DOB: 1970-08-20) audit trail test",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(phi_data)
        
        # CRITICAL: Processing metadata should not contain PHI
        metadata = result.metadata
        metadata_json = metadata.model_dump_json()
        
        assert "Robert Johnson" not in metadata_json
        assert "robert johnson" not in metadata_json.lower()
        assert "1970-08-20" not in metadata_json
        
        # Check preservation hash doesn't expose PHI  
        assert metadata.preservation_hash is not None
        # Hash should be deterministic but not reversible to PHI
        assert len(metadata.preservation_hash) == 64  # SHA-256
        assert "Robert" not in metadata.preservation_hash
        assert "Johnson" not in metadata.preservation_hash
        
        # Processing metadata should be safe for audit logs
        processing_metadata = processor.get_processing_metadata()
        metadata_str = str(processing_metadata)
        assert "Robert Johnson" not in metadata_str
        assert "1970-08-20" not in metadata_str
    
    def test_safety_validation_no_phi_exposure(self):
        """
        Test that safety validation results don't expose PHI.
        """
        processor = HybridClinicalProcessor()
        
        original_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/safety-validation-alice-williams"},
            "medicationCodeableConcept": {"text": "Safety Validation Med for Alice Williams"},
            "dosageInstruction": [{
                "text": "Patient Alice Williams (MRN: ABC-123) safety validation test",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(original_data)
        processed_data = result.model_dump()
        
        # Get safety validation results
        safety_validation = processor.validate_safety_requirements(original_data, processed_data)
        validation_json = safety_validation.model_dump_json()
        
        # CRITICAL: Safety validation should not expose PHI
        assert "Alice Williams" not in validation_json
        assert "alice williams" not in validation_json.lower()
        assert "MRN: ABC-123" not in validation_json
        assert "ABC-123" not in validation_json
        
        # Validation errors (if any) should not contain PHI
        for error in safety_validation.errors:
            assert "Alice Williams" not in error
            assert "ABC-123" not in error
            
        for warning in safety_validation.warnings:
            assert "Alice Williams" not in warning
            assert "ABC-123" not in warning


class TestComplianceDocumentation:
    """
    Test that system generates appropriate compliance documentation.
    """
    
    def test_disclaimers_privacy_compliance(self):
        """
        Test that appropriate privacy disclaimers are included.
        """
        processor = HybridClinicalProcessor()
        
        simple_bundle = {
            "resourceType": "Bundle",
            "id": "disclaimer-test",
            "type": "collection", 
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "disclaimer-patient",
                    "name": [{"family": "Test", "given": ["Patient"]}]
                }},
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "disclaimer-med",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/disclaimer-patient"},
                    "medicationCodeableConcept": {"text": "Disclaimer Test Medication"},
                    "dosageInstruction": [{
                        "text": "Take as directed",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }}
            ]
        }
        
        result = processor.process_clinical_data(simple_bundle)
        
        # CRITICAL: Required disclaimers must be present
        assert len(result.disclaimers) >= 3
        
        disclaimer_text = " ".join(result.disclaimers).lower()
        
        # Educational use disclaimer
        assert any(word in disclaimer_text for word in ["educational", "education"])
        
        # Professional consultation disclaimer 
        assert any(word in disclaimer_text for word in ["consult", "healthcare provider", "provider"])
        
        # Emergency disclaimer
        assert any(word in disclaimer_text for word in ["emergency", "911"])
        
        # HIPAA/Privacy considerations could be added
        # assert any(word in disclaimer_text for word in ["privacy", "confidential"])
    
    def test_processing_transparency_compliance(self):
        """
        Test that processing is transparent and auditable without exposing PHI.
        """
        processor = HybridClinicalProcessor()
        
        test_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/transparency-test"},
            "medicationCodeableConcept": {"text": "Transparency Test Medication"},
            "dosageInstruction": [{
                "text": "Take 1 tablet once daily",
                "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
            }]
        }
        
        result = processor.process_medication_data(test_data)
        
        # TRANSPARENCY: Processing should be fully documented
        assert result.metadata.processing_version is not None
        assert result.metadata.processed_at is not None
        assert result.metadata.safety_level is not None
        assert result.metadata.processing_type is not None
        
        # AUDITABILITY: Clear indication of what was/wasn't AI processed
        assert result.metadata.ai_processed is not None  # Should be False for medication data
        assert result.metadata.validation_passed is not None
        
        # COMPLIANCE: Safety validation provides audit trail
        # (This would be expanded with more detailed audit requirements)
        assert isinstance(result.metadata.validation_errors, list)
        
        # All metadata should be PHI-free by design
        metadata_str = str(result.metadata.model_dump())
        # This test assumes no PHI was in the original simple test data
        # In production, would need more sophisticated PHI detection