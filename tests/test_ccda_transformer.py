"""
Comprehensive TDD Tests for CCDA to FHIR Transformer

This module contains Test-Driven Development tests for CCDA to FHIR transformation
with healthcare safety requirements. All tests focus on exact preservation
of critical medical data during the transformation process.
"""

import pytest
import json
from typing import Dict, Any, List

from src.summarizer.ccda_parser import CCDAParser
from src.summarizer.ccda_transformer import (
    CCDAToFHIRTransformer, 
    CCDATransformationError
)
from tests.fixtures.ccda_test_data import (
    diabetes_ccda_document,
    cardiac_ccda_document,
    expected_diabetes_medications,
    expected_diabetes_labs,
    expected_diabetes_vitals,
    expected_diabetes_allergies
)


class TestCCDAToFHIRTransformer:
    """Test CCDA to FHIR transformation with safety validation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.parser = CCDAParser()
        self.transformer = CCDAToFHIRTransformer()
    
    def test_transformer_initialization(self):
        """Test CCDA to FHIR transformer initializes correctly."""
        assert self.transformer.transformer_version == "1.0.0"
        assert "8480-6" in self.transformer.vital_sign_mappings  # Systolic BP
        assert "4548-4" in self.transformer.lab_test_mappings    # HbA1c
    
    def test_ccda_to_fhir_bundle_structure(self, diabetes_ccda_document):
        """
        TEST: Verify CCDA transforms to valid FHIR Bundle structure.
        """
        # Parse CCDA document
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Transform to FHIR Bundle
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Verify FHIR Bundle structure
        assert fhir_bundle["resourceType"] == "Bundle"
        assert fhir_bundle["type"] == "document"
        assert "id" in fhir_bundle
        assert "timestamp" in fhir_bundle
        assert "entry" in fhir_bundle
        assert len(fhir_bundle["entry"]) > 0
        
        # Verify transformation metadata
        assert "_ccda_transformation" in fhir_bundle
        assert fhir_bundle["_ccda_transformation"]["source_document_type"] == "ccda"
        assert fhir_bundle["_ccda_transformation"]["transformer_version"] == "1.0.0"

    def test_ccda_medication_to_fhir_preservation(self, diabetes_ccda_document, expected_diabetes_medications):
        """
        CRITICAL TEST: Verify medication data preservation during CCDA to FHIR transformation.
        
        This test ensures zero-tolerance medication data preservation through transformation.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract MedicationRequest resources
        medication_resources = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "MedicationRequest"
        ]
        
        # Verify correct number of medications
        assert len(medication_resources) == 3
        
        # Test each medication for exact preservation
        for i, expected_med in enumerate(expected_diabetes_medications):
            med_resource = medication_resources[i]
            
            # Verify FHIR resource structure
            assert med_resource["resourceType"] == "MedicationRequest"
            assert med_resource["status"] == "active"
            assert med_resource["intent"] == "order"
            
            # Verify medication name preservation
            medication_text = med_resource["medicationCodeableConcept"]["text"]
            assert expected_med["substance_name"] in medication_text
            
            # Verify dosage instruction preservation
            dosage_instructions = med_resource["dosageInstruction"]
            assert len(dosage_instructions) > 0
            
            dosage = dosage_instructions[0]
            if "doseAndRate" in dosage:
                dose_quantity = dosage["doseAndRate"][0]["doseQuantity"]
                # Verify dosage amount is preserved (may be converted to float)
                if expected_med["dosage_amount"].replace('.', '').isdigit():
                    assert dose_quantity["value"] == float(expected_med["dosage_amount"])
                assert dose_quantity["unit"] == expected_med["dosage_unit"]
            
            # Verify preservation data exists
            assert "_ccda_preservation" in med_resource
            preservation_data = med_resource["_ccda_preservation"]
            assert preservation_data["safety_level"] == "CRITICAL"
            assert "preservation_hash" in preservation_data
            assert "original_data" in preservation_data

    def test_ccda_lab_results_to_fhir_preservation(self, diabetes_ccda_document, expected_diabetes_labs):
        """
        CRITICAL TEST: Verify lab result data preservation during CCDA to FHIR transformation.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract Observation resources (lab results)
        lab_observations = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "Observation" and
            entry["resource"].get("category", [{}])[0].get("coding", [{}])[0].get("code") == "laboratory"
        ]
        
        # Verify correct number of lab results
        assert len(lab_observations) == 2
        
        # Test each lab result for exact preservation
        for i, expected_lab in enumerate(expected_diabetes_labs):
            lab_obs = lab_observations[i]
            
            # Verify FHIR resource structure
            assert lab_obs["resourceType"] == "Observation"
            assert lab_obs["status"] == "final"
            
            # Verify test name preservation
            assert lab_obs["code"]["text"] == expected_lab["test_name"]
            
            # Verify test code preservation
            if "coding" in lab_obs["code"]:
                assert lab_obs["code"]["coding"][0]["code"] == expected_lab["test_code"]
            
            # Verify value preservation (critical for clinical decisions)
            if "valueQuantity" in lab_obs:
                value_quantity = lab_obs["valueQuantity"]
                assert value_quantity["value"] == float(expected_lab["value"])
                assert value_quantity["unit"] == expected_lab["unit"]
            
            # Verify interpretation preservation
            if "interpretation" in lab_obs:
                interp_code = lab_obs["interpretation"][0]["coding"][0]["code"]
                assert interp_code == expected_lab["interpretation"]
            
            # Verify reference range preservation
            if "referenceRange" in lab_obs:
                ref_range_text = lab_obs["referenceRange"][0]["text"]
                assert ref_range_text == expected_lab["reference_range"]
            
            # Verify preservation data exists
            assert "_ccda_preservation" in lab_obs
            preservation_data = lab_obs["_ccda_preservation"]
            assert preservation_data["safety_level"] == "CRITICAL"
            assert "preservation_hash" in preservation_data

    def test_ccda_vital_signs_to_fhir_preservation(self, diabetes_ccda_document, expected_diabetes_vitals):
        """
        CRITICAL TEST: Verify vital signs data preservation during CCDA to FHIR transformation.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract vital signs Observation resources
        vital_observations = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "Observation" and
            entry["resource"].get("category", [{}])[0].get("coding", [{}])[0].get("code") == "vital-signs"
        ]
        
        # Verify correct number of vital signs
        assert len(vital_observations) == 3
        
        # Test each vital sign for exact preservation
        for i, expected_vital in enumerate(expected_diabetes_vitals):
            vital_obs = vital_observations[i]
            
            # Verify FHIR resource structure
            assert vital_obs["resourceType"] == "Observation"
            assert vital_obs["status"] == "final"
            
            # Verify vital sign name preservation
            assert vital_obs["code"]["text"] == expected_vital["vital_name"]
            
            # Verify vital sign code preservation
            if "coding" in vital_obs["code"]:
                assert vital_obs["code"]["coding"][0]["code"] == expected_vital["vital_code"]
            
            # Verify value preservation (critical for clinical assessment)
            if "valueQuantity" in vital_obs:
                value_quantity = vital_obs["valueQuantity"]
                # Handle different value formats (simple numbers vs complex like BP)
                if expected_vital["value"].replace('.', '').replace('/', '').isdigit():
                    assert value_quantity["value"] == float(expected_vital["value"])
                assert value_quantity["unit"] == expected_vital["unit"]
            
            # Verify preservation data exists
            assert "_ccda_preservation" in vital_obs
            preservation_data = vital_obs["_ccda_preservation"]
            assert preservation_data["safety_level"] == "CRITICAL"

    def test_ccda_allergies_to_fhir_preservation(self, diabetes_ccda_document, expected_diabetes_allergies):
        """
        CRITICAL TEST: Verify allergy data preservation during CCDA to FHIR transformation.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract AllergyIntolerance resources
        allergy_resources = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "AllergyIntolerance"
        ]
        
        # Verify correct number of allergies
        assert len(allergy_resources) == 1
        
        # Test allergy for exact preservation
        expected_allergy = expected_diabetes_allergies[0]
        allergy_resource = allergy_resources[0]
        
        # Verify FHIR resource structure
        assert allergy_resource["resourceType"] == "AllergyIntolerance"
        
        # Verify allergen preservation
        assert allergy_resource["code"]["text"] == expected_allergy["allergen"]
        
        # Verify severity preservation
        if "reaction" in allergy_resource:
            severity = allergy_resource["reaction"][0]["severity"]
            assert severity == expected_allergy["severity"].lower()
        
        # Verify preservation data exists
        assert "_ccda_preservation" in allergy_resource
        preservation_data = allergy_resource["_ccda_preservation"]
        assert preservation_data["safety_level"] == "CRITICAL"

    def test_ccda_transformation_integrity_validation(self, diabetes_ccda_document):
        """
        INTEGRITY TEST: Verify transformation integrity validation passes.
        
        This test ensures that all preservation hashes from original CCDA
        are present in the transformed FHIR bundle.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Perform integrity validation
        integrity_valid = self.transformer.validate_transformation_integrity(ccda_data, fhir_bundle)
        
        # Verification should pass
        assert integrity_valid is True

    def test_ccda_transformation_with_missing_data_integrity(self):
        """
        INTEGRITY TEST: Verify transformation fails integrity check when data is missing.
        
        This test simulates data loss during transformation to ensure
        integrity validation detects the issue.
        """
        # Create mock CCDA data with preservation hashes
        mock_ccda_data = {
            "sections": {
                "medications": [
                    {
                        "substance_name": "Test Med",
                        "preservation_hash": "abcd1234"
                    }
                ]
            }
        }
        
        # Create mock FHIR bundle missing the preservation hash
        mock_fhir_bundle = {
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "_ccda_preservation": {
                            "preservation_hash": "different_hash"  # Wrong hash
                        }
                    }
                }
            ]
        }
        
        # Integrity validation should fail
        integrity_valid = self.transformer.validate_transformation_integrity(mock_ccda_data, mock_fhir_bundle)
        assert integrity_valid is False

    def test_ccda_cardiac_medications_transformation(self, cardiac_ccda_document):
        """
        CRITICAL TEST: Verify cardiac medications with narrow therapeutic windows.
        
        Tests transformation of digoxin and warfarin - medications where exact
        dosing is critical for patient safety.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(cardiac_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract MedicationRequest resources
        medication_resources = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "MedicationRequest"
        ]
        
        assert len(medication_resources) == 2
        
        # Test digoxin transformation (narrow therapeutic window)
        digoxin_resource = medication_resources[0]
        assert "Digoxin" in digoxin_resource["medicationCodeableConcept"]["text"]
        
        # Verify exact dosage preservation for digoxin
        dosage = digoxin_resource["dosageInstruction"][0]
        if "doseAndRate" in dosage:
            dose_quantity = dosage["doseAndRate"][0]["doseQuantity"]
            assert dose_quantity["value"] == 0.125  # Critical precision
            assert dose_quantity["unit"] == "mg"
        
        # Test warfarin transformation (variable dosing)
        warfarin_resource = medication_resources[1]
        assert "Warfarin" in warfarin_resource["medicationCodeableConcept"]["text"]
        
        # Verify exact dosage preservation for warfarin
        dosage = warfarin_resource["dosageInstruction"][0]
        if "doseAndRate" in dosage:
            dose_quantity = dosage["doseAndRate"][0]["doseQuantity"]
            assert dose_quantity["value"] == 2.5  # Critical precision
            assert dose_quantity["unit"] == "mg"

    def test_ccda_cardiac_lab_monitoring_transformation(self, cardiac_ccda_document):
        """
        CRITICAL TEST: Verify lab results for medication monitoring transformation.
        
        Tests transformation of INR and digoxin levels - critical for
        medication safety monitoring.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(cardiac_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Extract lab Observation resources
        lab_observations = [
            entry["resource"] for entry in fhir_bundle["entry"]
            if entry["resource"]["resourceType"] == "Observation" and
            entry["resource"].get("category", [{}])[0].get("coding", [{}])[0].get("code") == "laboratory"
        ]
        
        assert len(lab_observations) == 2
        
        # Test INR result transformation (warfarin monitoring)
        inr_obs = lab_observations[0]
        assert inr_obs["code"]["text"] == "INR"
        assert inr_obs["valueQuantity"]["value"] == 2.3  # Critical for warfarin dosing
        assert inr_obs["valueQuantity"]["unit"] == "1"
        assert inr_obs["referenceRange"][0]["text"] == "Target range: 2.0-3.0"
        
        # Test digoxin level transformation (digoxin monitoring)
        digoxin_obs = lab_observations[1]
        assert digoxin_obs["code"]["text"] == "Digoxin"
        assert digoxin_obs["valueQuantity"]["value"] == 1.2  # Critical for digoxin safety
        assert digoxin_obs["valueQuantity"]["unit"] == "ng/mL"
        assert digoxin_obs["referenceRange"][0]["text"] == "Therapeutic range: 0.8-2.0 ng/mL"

    def test_ccda_datetime_format_transformation(self):
        """
        TEST: Verify CCDA datetime formats are correctly transformed to FHIR format.
        """
        # Test various CCDA datetime formats
        test_cases = [
            ("20240201", "2024-02-01"),
            ("20240201120000", "2024-02-01T12:00:00Z"),
            ("202402011230", "2024-02-01T12:30:00Z"),
            ("invalid", "invalid")  # Should pass through invalid formats
        ]
        
        for ccda_time, expected_fhir_time in test_cases:
            result = self.transformer._format_ccda_datetime(ccda_time)
            assert result == expected_fhir_time

    def test_ccda_interpretation_code_mapping(self):
        """
        TEST: Verify CCDA interpretation codes are correctly mapped.
        """
        test_mappings = {
            "H": "High",
            "L": "Low",
            "N": "Normal",
            "A": "Abnormal",
            "AA": "Critical abnormal",
            "UNKNOWN": "UNKNOWN"  # Should pass through unknown codes
        }
        
        for code, expected_display in test_mappings.items():
            result = self.transformer._map_interpretation_code(code)
            assert result == expected_display

    def test_ccda_medication_status_mapping(self):
        """
        TEST: Verify CCDA medication status codes are correctly mapped to FHIR.
        """
        test_mappings = {
            "active": "active",
            "completed": "completed",
            "cancelled": "cancelled",
            "stopped": "stopped",
            "unknown_status": "active"  # Should default to active
        }
        
        for ccda_status, expected_fhir_status in test_mappings.items():
            result = self.transformer._map_medication_status(ccda_status)
            assert result == expected_fhir_status

    def test_ccda_allergy_severity_mapping(self):
        """
        TEST: Verify CCDA allergy severity codes are correctly mapped to FHIR.
        """
        test_mappings = {
            "mild": "mild",
            "moderate": "moderate", 
            "severe": "severe",
            "Mild": "mild",  # Case insensitive
            "SEVERE": "severe",  # Case insensitive
            "unknown": None  # Should return None for unknown severities
        }
        
        for ccda_severity, expected_fhir_severity in test_mappings.items():
            result = self.transformer._map_allergy_severity(ccda_severity)
            assert result == expected_fhir_severity

    def test_ccda_transformation_error_handling(self):
        """
        TEST: Verify transformation handles errors gracefully.
        """
        # Test with invalid CCDA data structure
        invalid_ccda_data = {
            "invalid_structure": True
        }
        
        with pytest.raises(CCDATransformationError):
            self.transformer.transform_ccda_to_fhir_bundle(invalid_ccda_data)

    def test_ccda_patient_resource_creation(self):
        """
        TEST: Verify patient resource is correctly created from CCDA metadata.
        """
        metadata = {
            "document_id": "TEST-PATIENT-001",
            "title": "Test Document"
        }
        
        patient_resource = self.transformer._create_patient_resource(metadata)
        
        assert patient_resource["resourceType"] == "Patient"
        assert patient_resource["identifier"][0]["value"] == "TEST-PATIENT-001"
        assert patient_resource["identifier"][0]["system"] == "ccda-document-id"
        assert patient_resource["active"] is True

    def test_ccda_fhir_bundle_metadata_preservation(self, diabetes_ccda_document):
        """
        TEST: Verify FHIR bundle preserves CCDA transformation metadata.
        """
        # Parse and transform
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        
        # Verify transformation metadata is preserved
        transformation_metadata = fhir_bundle["_ccda_transformation"]
        
        assert transformation_metadata["source_document_type"] == "ccda"
        assert transformation_metadata["transformer_version"] == self.transformer.transformer_version
        assert "transformation_timestamp" in transformation_metadata
        assert "original_sections" in transformation_metadata
        
        # Verify original sections are documented
        original_sections = transformation_metadata["original_sections"]
        expected_sections = ["medications", "results", "vital_signs", "allergies"]
        for section in expected_sections:
            assert section in original_sections


class TestCCDATransformerPerformance:
    """Performance tests for CCDA to FHIR transformer."""
    
    def setup_method(self):
        """Setup performance test fixtures."""
        self.parser = CCDAParser()
        self.transformer = CCDAToFHIRTransformer()
    
    def test_ccda_transformation_performance(self, diabetes_ccda_document):
        """
        PERFORMANCE TEST: Verify transformation completes within time limits.
        """
        import time
        
        # Parse CCDA
        ccda_data = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Time the transformation
        start_time = time.time()
        fhir_bundle = self.transformer.transform_ccda_to_fhir_bundle(ccda_data)
        transformation_time = time.time() - start_time
        
        # Should transform within 2 seconds (reasonable for clinical use)
        assert transformation_time < 2.0
        assert fhir_bundle["resourceType"] == "Bundle"
        assert len(fhir_bundle["entry"]) > 0