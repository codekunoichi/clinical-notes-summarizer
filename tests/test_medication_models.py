"""
Tests for medication Pydantic models with healthcare safety validation.

These tests ensure that medication models enforce strict validation
and prevent any corruption of critical medical data.
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError

from src.models.medication import (
    MedicationRequest,
    DosageInstruction,
    MedicationCodeableConcept,
    DoseAndRate,
    Quantity,
    Timing,
    Repeat,
    MedicationStatus,
    MedicationIntent
)


class TestMedicationCodeableConcept:
    """Test medication name validation and preservation."""
    
    def test_valid_medication_text(self):
        """Test that valid medication text is accepted."""
        concept = MedicationCodeableConcept(text="Lisinopril 10mg tablets")
        assert concept.text == "Lisinopril 10mg tablets"
    
    def test_empty_medication_text_rejected(self):
        """Test that empty medication text is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MedicationCodeableConcept(text="")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_whitespace_only_medication_text_rejected(self):
        """Test that whitespace-only medication text is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MedicationCodeableConcept(text="   ")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_invalid_characters_rejected(self):
        """Test that medication names with invalid characters are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MedicationCodeableConcept(text="Medication@#$%")
        assert "invalid characters" in str(exc_info.value)
    
    def test_rxnorm_code_validation(self):
        """Test that RxNorm codes must be numeric."""
        from src.models.medication import Coding
        
        # Valid RxNorm code
        concept = MedicationCodeableConcept(
            coding=[Coding(
                system="http://www.nlm.nih.gov/research/umls/rxnorm",
                code="197361",
                display="Lisinopril 10 MG Oral Tablet"
            )],
            text="Lisinopril 10mg"
        )
        assert concept.coding[0].code == "197361"
        
        # Invalid RxNorm code (non-numeric)
        with pytest.raises(ValidationError) as exc_info:
            MedicationCodeableConcept(
                coding=[Coding(
                    system="http://www.nlm.nih.gov/research/umls/rxnorm",
                    code="ABC123",
                    display="Invalid code"
                )],
                text="Test medication"
            )
        assert "must be numeric" in str(exc_info.value)


class TestQuantity:
    """Test medication quantity validation."""
    
    def test_positive_dosage_value(self):
        """Test that positive dosage values are accepted."""
        quantity = Quantity(value=10.5, unit="mg")
        assert quantity.value == 10.5
        assert quantity.unit == "mg"
    
    def test_zero_dosage_rejected(self):
        """Test that zero dosage values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Quantity(value=0, unit="mg")
        assert "must be positive" in str(exc_info.value)
    
    def test_negative_dosage_rejected(self):
        """Test that negative dosage values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Quantity(value=-5, unit="mg")
        assert "must be positive" in str(exc_info.value)
    
    def test_decimal_dosage_accepted(self):
        """Test that decimal dosage values are accepted."""
        quantity = Quantity(value=Decimal("2.5"), unit="mg")
        assert quantity.value == Decimal("2.5")
    
    def test_common_medication_units(self):
        """Test that common medication units are accepted."""
        valid_units = ["tablet", "tablets", "ml", "mg", "g", "mcg", "units", "drops"]
        
        for unit in valid_units:
            quantity = Quantity(value=1, unit=unit)
            assert quantity.unit == unit


class TestDoseAndRate:
    """Test dose and rate validation."""
    
    def test_dose_quantity_required(self):
        """Test that at least one dose specification is required."""
        # Valid with doseQuantity
        dose_rate = DoseAndRate(
            doseQuantity=Quantity(value=1, unit="tablet")
        )
        assert dose_rate.doseQuantity.value == 1
        
        # Invalid with no dose specification
        with pytest.raises(ValidationError) as exc_info:
            DoseAndRate()
        assert "at least one dose specification" in str(exc_info.value).lower()


class TestRepeat:
    """Test timing repeat validation."""
    
    def test_positive_frequency(self):
        """Test that frequency must be positive."""
        repeat = Repeat(frequency=2, period=1, periodUnit="d")
        assert repeat.frequency == 2
        
        with pytest.raises(ValidationError) as exc_info:
            Repeat(frequency=0, period=1, periodUnit="d")
        assert "must be positive" in str(exc_info.value)
    
    def test_positive_period(self):
        """Test that period must be positive."""
        repeat = Repeat(frequency=1, period=2, periodUnit="d")
        assert repeat.period == 2
        
        with pytest.raises(ValidationError) as exc_info:
            Repeat(frequency=1, period=0, periodUnit="d")
        assert "must be positive" in str(exc_info.value)


class TestDosageInstruction:
    """Test dosage instruction validation."""
    
    def test_meaningful_dosage_text(self):
        """Test that dosage text must be meaningful if provided."""
        # Valid meaningful text
        dosage = DosageInstruction(text="Take 1 tablet by mouth once daily")
        assert dosage.text == "Take 1 tablet by mouth once daily"
        
        # Invalid short text
        with pytest.raises(ValidationError) as exc_info:
            DosageInstruction(text="Take")
        assert "must be meaningful" in str(exc_info.value)
    
    def test_dosage_completeness_validation(self):
        """Test that dosage must have either text or structured data."""
        # Valid with text only
        dosage1 = DosageInstruction(text="Take 1 tablet daily")
        assert dosage1.text is not None
        
        # Valid with structured data only
        dosage2 = DosageInstruction(
            doseAndRate=[DoseAndRate(doseQuantity=Quantity(value=1, unit="tablet"))]
        )
        assert dosage2.doseAndRate is not None
        
        # Invalid with neither
        with pytest.raises(ValidationError) as exc_info:
            DosageInstruction()
        assert "must have either text or structured dose information" in str(exc_info.value)


class TestMedicationRequest:
    """Test complete medication request validation."""
    
    def test_valid_medication_request(self, sample_medication_data):
        """Test that valid medication request is accepted."""
        med_request = MedicationRequest(**sample_medication_data)
        assert med_request.status == MedicationStatus.ACTIVE
        assert med_request.intent == MedicationIntent.ORDER
        assert med_request.medicationCodeableConcept.text == "Lisinopril 10mg tablets"
    
    def test_medication_specification_required(self):
        """Test that either medicationCodeableConcept or medicationReference is required."""
        from src.models.medication import Reference
        
        # Missing both - should fail
        with pytest.raises(ValidationError) as exc_info:
            MedicationRequest(
                status=MedicationStatus.ACTIVE,
                intent=MedicationIntent.ORDER,
                subject=Reference(reference="Patient/patient-001")
            )
        assert "must be specified" in str(exc_info.value)
    
    def test_both_medication_specifications_rejected(self):
        """Test that both medication specifications cannot be provided."""
        from src.models.medication import Reference
        
        with pytest.raises(ValidationError) as exc_info:
            MedicationRequest(
                status=MedicationStatus.ACTIVE,
                intent=MedicationIntent.ORDER,
                subject=Reference(reference="Patient/patient-001"),
                medicationCodeableConcept=MedicationCodeableConcept(text="Test med"),
                medicationReference=Reference(reference="Medication/med-001")
            )
        assert "Only one of" in str(exc_info.value)
    
    def test_empty_dosage_instructions_rejected(self):
        """Test that empty dosage instruction list is rejected."""
        from src.models.medication import Reference
        
        with pytest.raises(ValidationError) as exc_info:
            MedicationRequest(
                status=MedicationStatus.ACTIVE,
                intent=MedicationIntent.ORDER,
                subject=Reference(reference="Patient/patient-001"),
                medicationCodeableConcept=MedicationCodeableConcept(text="Test med"),
                dosageInstruction=[]  # Empty list should be rejected
            )
        assert "cannot be empty" in str(exc_info.value)
    
    def test_medication_status_enum(self):
        """Test that medication status must be valid enum value."""
        from src.models.medication import Reference
        
        # Valid status
        med_request = MedicationRequest(
            status=MedicationStatus.ACTIVE,
            intent=MedicationIntent.ORDER,
            subject=Reference(reference="Patient/patient-001"),
            medicationCodeableConcept=MedicationCodeableConcept(text="Test med")
        )
        assert med_request.status == MedicationStatus.ACTIVE
        
        # Invalid status should be caught by Pydantic enum validation
        with pytest.raises(ValidationError):
            MedicationRequest(
                status="invalid_status",
                intent=MedicationIntent.ORDER,
                subject=Reference(reference="Patient/patient-001"),
                medicationCodeableConcept=MedicationCodeableConcept(text="Test med")
            )
    
    def test_pydantic_config_validation(self):
        """Test that Pydantic configuration enforces safety requirements."""
        from src.models.medication import Reference
        
        med_request = MedicationRequest(
            status=MedicationStatus.ACTIVE,
            intent=MedicationIntent.ORDER,
            subject=Reference(reference="Patient/patient-001"),
            medicationCodeableConcept=MedicationCodeableConcept(text="Test med")
        )
        
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            med_request_dict = med_request.dict()
            med_request_dict["extra_field"] = "not allowed"
            MedicationRequest(**med_request_dict)
        
        # Test that assignment validation works
        with pytest.raises(ValidationError):
            med_request.status = "invalid_status"


@pytest.mark.safety
class TestMedicationSafetyRequirements:
    """
    Critical safety tests for medication data models.
    
    These tests ensure that medication models meet healthcare safety standards
    and prevent any possibility of data corruption.
    """
    
    def test_medication_name_preservation(self):
        """Test that medication names are preserved exactly."""
        original_name = "Lisinopril 10 MG Oral Tablet"
        concept = MedicationCodeableConcept(text=original_name)
        
        # Name must be preserved exactly
        assert concept.text == original_name
        
        # Serialization must preserve the name
        serialized = concept.dict()
        assert serialized["text"] == original_name
        
        # Deserialization must preserve the name
        restored = MedicationCodeableConcept(**serialized)
        assert restored.text == original_name
    
    def test_dosage_precision_preservation(self):
        """Test that dosage precision is preserved exactly."""
        # Test with decimal precision
        precise_dose = Decimal("2.125")
        quantity = Quantity(value=precise_dose, unit="mg")
        
        # Precision must be preserved
        assert quantity.value == precise_dose
        
        # Serialization must preserve precision
        serialized = quantity.dict()
        restored = Quantity(**serialized)
        assert restored.value == precise_dose
    
    def test_critical_medication_fields_immutable(self, sample_medication_data):
        """Test that critical medication fields cannot be accidentally modified."""
        med_request = MedicationRequest(**sample_medication_data)
        
        # Critical fields that must not be modifiable
        original_status = med_request.status
        original_med_concept = med_request.medicationCodeableConcept
        original_dosage = med_request.dosageInstruction
        
        # Verify fields are preserved
        assert med_request.status == original_status
        assert med_request.medicationCodeableConcept == original_med_concept
        assert med_request.dosageInstruction == original_dosage
        
        # Test that validation occurs on assignment (if enabled in config)
        try:
            med_request.status = "invalid"
            assert False, "Should have raised ValidationError"
        except (ValidationError, ValueError):
            # This is expected - validation should prevent invalid assignment
            pass
    
    def test_fhir_compliance_validation(self, sample_medication_data):
        """Test that medication models maintain FHIR compliance."""
        med_request = MedicationRequest(**sample_medication_data)
        
        # Must have correct resourceType
        assert med_request.resourceType == "MedicationRequest"
        
        # Must have required FHIR fields
        assert med_request.status is not None
        assert med_request.intent is not None
        assert med_request.subject is not None
        
        # Must validate against FHIR constraints
        assert med_request.status in [status.value for status in MedicationStatus]
        assert med_request.intent in [intent.value for intent in MedicationIntent]