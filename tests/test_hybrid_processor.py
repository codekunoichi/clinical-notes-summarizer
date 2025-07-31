"""
Tests for HybridClinicalProcessor - the core processing engine.

These are FAILING tests that define the expected behavior of the processor.
They will fail until we implement the HybridClinicalProcessor class.

Following TDD red-green-refactor cycle:
1. RED: These tests will fail (processor doesn't exist yet)
2. GREEN: Implement minimal processor to make tests pass  
3. REFACTOR: Improve implementation while maintaining test passes
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime
from pydantic import ValidationError

from src.models.medication import MedicationRequest
from src.models.clinical import (
    ClinicalSummary, 
    MedicationSummary, 
    ProcessingMetadata,
    SafetyValidation,
    ProcessingType,
    SafetyLevel
)

# Import will fail until we create the processor - this is expected in TDD
try:
    from src.summarizer.hybrid_processor import HybridClinicalProcessor
except ImportError:
    # This is expected in TDD - we haven't implemented it yet
    HybridClinicalProcessor = None


@pytest.mark.skipif(HybridClinicalProcessor is None, reason="HybridClinicalProcessor not implemented yet")
class TestHybridClinicalProcessor:
    """
    Test the core hybrid processing engine.
    
    These tests define the expected behavior for processing clinical data
    while maintaining strict safety standards for critical medical information.
    """
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return HybridClinicalProcessor()
    
    def test_processor_initialization(self, processor):
        """Test that processor initializes with correct default settings."""
        assert processor is not None
        assert hasattr(processor, 'process_clinical_data')
        assert hasattr(processor, 'process_medication_data')
        assert hasattr(processor, 'validate_safety_requirements')
    
    def test_medication_data_preservation(self, processor, sample_medication_data):
        """
        CRITICAL TEST: Medication data must be preserved exactly.
        
        This test ensures that medication names, dosages, frequencies,
        and instructions are NEVER altered by AI processing.
        """
        # Process the medication data
        result = processor.process_medication_data(sample_medication_data)
        
        # Verify result structure
        assert isinstance(result, MedicationSummary)
        
        # CRITICAL: Exact preservation of medication details
        original_med = sample_medication_data["medicationCodeableConcept"]["text"]
        assert result.medication_name == original_med
        
        # CRITICAL: Exact preservation of dosage instructions
        original_dosage = sample_medication_data["dosageInstruction"][0]
        expected_dosage = f"{original_dosage['doseAndRate'][0]['doseQuantity']['value']} {original_dosage['doseAndRate'][0]['doseQuantity']['unit']}"
        assert result.dosage == expected_dosage
        
        # CRITICAL: Exact preservation of frequency
        timing = original_dosage["timing"]["repeat"]
        expected_frequency = f"{timing['frequency']} time(s) per {timing['period']} {timing['periodUnit']}"
        assert result.frequency == expected_frequency
        
        # CRITICAL: Verify no AI processing of critical fields
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert result.metadata.processing_type == ProcessingType.PRESERVED
        assert not result.metadata.ai_processed  # Must be False for critical data
    
    def test_medication_ai_enhancement_allowed_fields(self, processor, sample_medication_data):
        """
        Test that AI enhancement is allowed ONLY for safe narrative fields.
        
        Purpose and important_notes can be AI-enhanced for patient understanding,
        but never the critical medication details.
        """
        result = processor.process_medication_data(sample_medication_data)
        
        # AI enhancement allowed for these fields (if present)
        if result.purpose:
            # Purpose should be patient-friendly explanation
            assert len(result.purpose) > 0
            assert "blood pressure" in result.purpose.lower() or "hypertension" in result.purpose.lower()
        
        if result.important_notes:
            # Important notes should be patient-friendly safety info
            assert len(result.important_notes) > 0
        
        # Verify metadata correctly reflects AI usage for safe fields only
        assert result.metadata.validation_passed
        assert len(result.metadata.validation_errors) == 0
    
    def test_complex_medication_processing(self, processor, sample_complex_medication_data):
        """
        Test processing of complex medication with multiple instructions.
        
        Complex medications with titration schedules and special instructions
        must have all critical details preserved exactly.
        """
        result = processor.process_medication_data(sample_complex_medication_data)
        
        # Verify complex instruction preservation  
        original_instruction = sample_complex_medication_data["dosageInstruction"][0]["text"]
        # Check that frequency correctly reflects "twice daily" (2 times per day)
        assert "2 time(s) per 1 d" in result.frequency or "twice daily" in result.frequency.lower()
        assert "with meals" in result.instructions.lower()
        
        # Verify patient instruction preservation
        original_patient_instruction = sample_complex_medication_data["dosageInstruction"][0]["patientInstruction"]
        assert "food" in result.instructions.lower()
        assert "blood sugar" in result.instructions.lower()
        
        # Critical safety check - no AI processing of dosage details
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed
    
    def test_safety_validation_enforcement(self, processor, sample_medication_data):
        """
        Test that safety validation is enforced throughout processing.
        
        The processor must validate that critical data is never altered
        and that AI processing flags are correctly set.
        """
        result = processor.process_medication_data(sample_medication_data)
        
        # Safety validation must pass
        assert result.metadata.validation_passed
        assert len(result.metadata.validation_errors) == 0
        
        # Verify safety validation covers critical fields
        validation = processor.validate_safety_requirements(sample_medication_data, result.model_dump())
        assert isinstance(validation, SafetyValidation)
        assert validation.passed
        assert validation.data_type == "medication"
        
        # Critical fields must be marked as preserved
        critical_fields = ["medication_name", "dosage", "frequency", "instructions"]
        for field in critical_fields:
            assert validation.critical_fields_preserved.get(field, False)
            assert not validation.ai_processing_flags.get(field, False)
    
    def test_complete_clinical_summary_generation(self, processor, fhir_medication_bundle):
        """
        Test generation of complete clinical summary from FHIR bundle.
        
        This tests the end-to-end processing pipeline while ensuring
        all safety requirements are met.
        """
        result = processor.process_clinical_data(fhir_medication_bundle)
        
        # Verify result structure
        assert isinstance(result, ClinicalSummary)
        assert result.summary_id is not None
        assert result.patient_id is not None
        assert isinstance(result.generated_at, datetime)
        
        # Verify medication processing
        assert len(result.medications) > 0
        medication = result.medications[0]
        assert isinstance(medication, MedicationSummary)
        
        # Verify safety validation for complete summary
        assert isinstance(result.safety_validation, SafetyValidation)
        assert result.safety_validation.passed
        
        # Verify required disclaimers are present
        assert len(result.disclaimers) >= 3
        required_disclaimer_keywords = ["educational purposes", "consult", "emergency"]
        for keyword in required_disclaimer_keywords:
            assert any(keyword.lower() in disclaimer.lower() for disclaimer in result.disclaimers)
    
    def test_error_handling_invalid_medication_data(self, processor):
        """
        Test that processor handles invalid medication data gracefully.
        
        Invalid data should be rejected with clear error messages,
        never processed in a way that could compromise safety.
        """
        invalid_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order"
            # Missing required fields like subject, medication
        }
        
        with pytest.raises(ValueError) as exc_info:
            processor.process_medication_data(invalid_data)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_processor_preserves_fhir_compliance(self, processor, sample_medication_data):
        """
        Test that processed data maintains FHIR compliance.
        
        Even after processing for patient-friendliness, the underlying
        data structure should remain FHIR-compliant for interoperability.
        """
        result = processor.process_medication_data(sample_medication_data)
        
        # The original FHIR data should be accessible for system integration
        assert hasattr(result, 'metadata')
        
        # Metadata should include preservation hash for integrity verification
        assert result.metadata.preservation_hash is not None
        
        # Processing should maintain traceability to original FHIR data
        assert result.metadata.processing_version is not None
        assert result.metadata.processed_at is not None


@pytest.mark.safety
@pytest.mark.skipif(HybridClinicalProcessor is None, reason="HybridClinicalProcessor not implemented yet")
class TestMedicationSafetyEnforcement:
    """
    Critical safety tests for medication processing.
    
    These tests ensure absolute zero tolerance for medication errors
    and validate that the processor meets healthcare safety standards.
    """
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for safety testing."""
        return HybridClinicalProcessor()
    
    def test_zero_tolerance_medication_name_changes(self, processor, medication_safety_validator):
        """
        CRITICAL SAFETY TEST: Medication names must NEVER be changed.
        
        Any alteration to medication names could result in dangerous
        medication errors. This is a zero-tolerance requirement.
        """
        test_medications = [
            "Lisinopril 10 MG Oral Tablet",
            "Metformin 500mg tablets", 
            "Warfarin Sodium 5 MG Oral Tablet",
            "Insulin Glargine 100 unit/mL Pen Injector"
        ]
        
        for med_name in test_medications:
            data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/test"},
                "medicationCodeableConcept": {"text": med_name}
            }
            
            result = processor.process_medication_data(data)
            
            # CRITICAL: Name must be preserved exactly
            assert result.medication_name == med_name
            
            # Validate using safety validator (pass in MedicationSummary format)
            errors = medication_safety_validator.validate_medication_preservation(
                data, {"medication_name": result.medication_name}
            )
            assert len(errors) == 0, f"Medication name validation failed: {errors}"
    
    def test_zero_tolerance_dosage_changes(self, processor, medication_safety_validator):
        """
        CRITICAL SAFETY TEST: Dosages must NEVER be changed.
        
        Any alteration to dosages could result in dangerous overdoses
        or underdoses. This is a zero-tolerance requirement.
        """
        critical_dosages = [
            {"value": 0.25, "unit": "mg"},  # Low dose (e.g., Digoxin)
            {"value": 5, "unit": "mg"},     # Medium dose
            {"value": 1000, "unit": "mg"},  # High dose
            {"value": 2.5, "unit": "mcg"}   # Precision critical (e.g., Levothyroxine)
        ]
        
        for dosage in critical_dosages:
            data = {
                "resourceType": "MedicationRequest",
                "status": "active",
                "intent": "order",
                "subject": {"reference": "Patient/test"},
                "medicationCodeableConcept": {"text": "Test Medication"},
                "dosageInstruction": [{
                    "doseAndRate": [{
                        "doseQuantity": dosage
                    }]
                }]
            }
            
            result = processor.process_medication_data(data)
            
            # CRITICAL: Dosage must be preserved exactly
            expected_dosage = f"{dosage['value']} {dosage['unit']}"
            assert result.dosage == expected_dosage
    
    def test_ai_processing_prohibition_enforcement(self, processor, medication_safety_validator):
        """
        CRITICAL SAFETY TEST: AI must NEVER process critical medication fields.
        
        This test ensures that the processor enforces the prohibition
        against AI processing of life-critical medication data.
        """
        data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": "Critical Test Medication 100mg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth twice daily with food",
                "doseAndRate": [{
                    "doseQuantity": {"value": 1, "unit": "tablet"}
                }],
                "timing": {
                    "repeat": {"frequency": 2, "period": 1, "periodUnit": "d"}
                }
            }]
        }
        
        result = processor.process_medication_data(data)
        
        # Validate no AI processing flags for critical fields
        errors = medication_safety_validator.validate_no_ai_processing_flags(result.model_dump())
        assert len(errors) == 0, f"AI processing prohibition violated: {errors}"
        
        # Verify metadata correctly indicates no AI processing for critical data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed  # Overall AI processing flag must be False
    
    def test_validation_failure_prevents_processing(self, processor):
        """
        CRITICAL SAFETY TEST: Invalid data must prevent processing completion.
        
        If safety validation fails, the processor must not return results
        that could be used clinically.
        """
        # Create data that will fail validation
        invalid_data = {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/test"},
            "medicationCodeableConcept": {"text": ""},  # Empty medication name
            "dosageInstruction": [{
                "doseAndRate": [{
                    "doseQuantity": {"value": -1, "unit": "tablet"}  # Negative dosage
                }]
            }]
        }
        
        # Processing should fail with validation error
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            processor.process_medication_data(invalid_data)
        
        # Error message should indicate safety validation failure
        assert "validation" in str(exc_info.value).lower()


# Test that will guide us in implementing the processor
def test_hybrid_processor_interface_definition():
    """
    Test that defines the expected interface for HybridClinicalProcessor.
    
    This test documents the expected public interface that we need to implement.
    """
    # Import should now work since we implemented the processor
    from src.summarizer.hybrid_processor import HybridClinicalProcessor
    
    # Verify the processor has the expected interface
    processor = HybridClinicalProcessor()
    
    # Core processing methods
    assert hasattr(processor, 'process_clinical_data')
    assert hasattr(processor, 'process_medication_data')
    assert hasattr(processor, 'process_lab_data') 
    assert hasattr(processor, 'process_appointment_data')
    
    # Safety and validation methods
    assert hasattr(processor, 'validate_safety_requirements')
    assert hasattr(processor, 'enforce_ai_processing_rules')
    
    # Configuration and metadata methods
    assert hasattr(processor, 'get_processing_metadata')
    assert hasattr(processor, 'set_safety_level')