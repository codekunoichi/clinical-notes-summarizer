"""
Comprehensive TDD Tests for CCDA Parser

This module contains Test-Driven Development tests for CCDA XML parsing
with healthcare safety requirements. All tests focus on exact preservation
of critical medical data and security validation.
"""

import pytest
import hashlib
from typing import Dict, Any, List

from src.summarizer.ccda_parser import (
    CCDAParser, 
    CCDAParsingError, 
    CCDASecurityError, 
    CCDAValidationError
)
from tests.fixtures.ccda_test_data import (
    CCDATestDataFactory,
    diabetes_ccda_document,
    cardiac_ccda_document,
    malicious_ccda_document,
    invalid_ccda_document,
    expected_diabetes_medications,
    expected_diabetes_labs,
    expected_diabetes_vitals,
    expected_diabetes_allergies
)


class TestCCDAParser:
    """Test CCDA parsing with healthcare safety requirements."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.parser = CCDAParser()
    
    def test_ccda_parser_initialization(self):
        """Test CCDA parser initializes with correct security settings."""
        assert self.parser.parser_version == "1.0.0"
        assert self.parser.max_document_size == 50 * 1024 * 1024
        assert "CCDA" in self.parser.supported_document_types
        assert self.parser.security_features["xxe_protection"] is True
        assert self.parser.security_features["dtd_validation"] is False
        assert self.parser.security_features["network_access"] is False
    
    def test_ccda_medication_exact_preservation(self, diabetes_ccda_document, expected_diabetes_medications):
        """
        CRITICAL TEST: Verify medication names and dosages are preserved exactly.
        
        This test ensures zero-tolerance medication data preservation.
        """
        # Parse CCDA document
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify medications section exists
        assert "medications" in result["sections"]
        medications = result["sections"]["medications"]
        
        # Verify correct number of medications
        assert len(medications) == 3
        
        # Test each medication for exact preservation
        for i, expected_med in enumerate(expected_diabetes_medications):
            actual_med = medications[i]
            
            # Verify exact medication name preservation
            assert actual_med["substance_name"] == expected_med["substance_name"]
            
            # Verify exact dosage preservation
            assert actual_med["dosage_amount"] == expected_med["dosage_amount"]
            assert actual_med["dosage_unit"] == expected_med["dosage_unit"]
            
            # Verify exact frequency preservation
            assert actual_med["frequency"] == expected_med["frequency"]
            
            # Verify route preservation
            assert actual_med["route"] == expected_med["route"]
            
            # Verify status preservation
            assert actual_med["status"] == expected_med["status"]
            
            # Verify preservation hash exists and is valid
            assert "preservation_hash" in actual_med
            assert len(actual_med["preservation_hash"]) == 16
            
            # Verify hash consistency (same input = same hash)
            test_hash = self._generate_test_preservation_hash(actual_med)
            assert actual_med["preservation_hash"] == test_hash

    def test_ccda_lab_value_preservation(self, diabetes_ccda_document, expected_diabetes_labs):
        """
        CRITICAL TEST: Verify lab values and units are never altered.
        
        This test ensures zero-tolerance lab data preservation.
        """
        # Parse CCDA document
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify results section exists
        assert "results" in result["sections"]
        lab_results = result["sections"]["results"]
        
        # Verify correct number of lab results
        assert len(lab_results) == 2
        
        # Test each lab result for exact preservation
        for i, expected_lab in enumerate(expected_diabetes_labs):
            actual_lab = lab_results[i]
            
            # Verify exact test name preservation
            assert actual_lab["test_name"] == expected_lab["test_name"]
            
            # Verify exact test code preservation
            assert actual_lab["test_code"] == expected_lab["test_code"]
            
            # Verify exact value preservation (critical for clinical decisions)
            assert actual_lab["value"] == expected_lab["value"]
            
            # Verify exact unit preservation (critical for interpretation)
            assert actual_lab["unit"] == expected_lab["unit"]
            
            # Verify interpretation preservation
            assert actual_lab["interpretation"] == expected_lab["interpretation"]
            
            # Verify reference range preservation
            assert actual_lab["reference_range"] == expected_lab["reference_range"]
            
            # Verify preservation hash exists
            assert "preservation_hash" in actual_lab
            assert len(actual_lab["preservation_hash"]) == 16

    def test_ccda_vital_signs_preservation(self, diabetes_ccda_document, expected_diabetes_vitals):
        """
        CRITICAL TEST: Verify vital signs values are preserved exactly.
        
        This test ensures zero-tolerance vital signs data preservation.
        """
        # Parse CCDA document
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify vital signs section exists
        assert "vital_signs" in result["sections"]
        vital_signs = result["sections"]["vital_signs"]
        
        # Verify correct number of vital signs
        assert len(vital_signs) == 3
        
        # Test each vital sign for exact preservation
        for i, expected_vital in enumerate(expected_diabetes_vitals):
            actual_vital = vital_signs[i]
            
            # Verify exact vital name preservation
            assert actual_vital["vital_name"] == expected_vital["vital_name"]
            
            # Verify exact vital code preservation
            assert actual_vital["vital_code"] == expected_vital["vital_code"]
            
            # Verify exact value preservation (critical for clinical assessment)
            assert actual_vital["value"] == expected_vital["value"]
            
            # Verify exact unit preservation
            assert actual_vital["unit"] == expected_vital["unit"]
            
            # Verify measurement time preservation
            assert actual_vital["measurement_time"] == expected_vital["measurement_time"]
            
            # Verify preservation hash exists
            assert "preservation_hash" in actual_vital
            assert len(actual_vital["preservation_hash"]) == 16

    def test_ccda_allergy_preservation(self, diabetes_ccda_document, expected_diabetes_allergies):
        """
        CRITICAL TEST: Verify allergy information is preserved exactly.
        
        This test ensures zero-tolerance allergy data preservation.
        """
        # Parse CCDA document
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify allergies section exists
        assert "allergies" in result["sections"]
        allergies = result["sections"]["allergies"]
        
        # Verify correct number of allergies
        assert len(allergies) == 1
        
        # Test allergy for exact preservation
        expected_allergy = expected_diabetes_allergies[0]
        actual_allergy = allergies[0]
        
        # Verify exact allergen preservation
        assert actual_allergy["allergen"] == expected_allergy["allergen"]
        
        # Verify exact severity preservation
        assert actual_allergy["severity"] == expected_allergy["severity"]
        
        # Verify preservation hash exists
        assert "preservation_hash" in actual_allergy
        assert len(actual_allergy["preservation_hash"]) == 16

    def test_ccda_xml_security_validation(self, malicious_ccda_document):
        """
        SECURITY TEST: Verify malicious XML content is rejected.
        
        This test ensures XML security threats are detected and blocked.
        """
        # Malicious CCDA with DTD and external entities should be rejected
        with pytest.raises(CCDASecurityError) as excinfo:
            self.parser.parse_ccda_document(malicious_ccda_document)
        
        # Verify appropriate security error message
        assert "DTD declarations are not allowed" in str(excinfo.value)

    def test_ccda_oversized_document_rejection(self):
        """
        SECURITY TEST: Verify oversized documents are rejected.
        
        This test ensures document size limits are enforced for security.
        """
        # Create oversized document (larger than 50MB limit)
        oversized_content = "x" * (51 * 1024 * 1024)
        oversized_ccda = f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <data>{oversized_content}</data>
</ClinicalDocument>"""
        
        with pytest.raises(CCDASecurityError) as excinfo:
            self.parser.parse_ccda_document(oversized_ccda)
        
        assert "exceeds maximum size" in str(excinfo.value)

    def test_ccda_empty_document_rejection(self):
        """
        SECURITY TEST: Verify empty or invalid content is rejected.
        """
        with pytest.raises(CCDASecurityError):
            self.parser.parse_ccda_document("")
        
        with pytest.raises(CCDASecurityError):
            self.parser.parse_ccda_document("   ")
        
        with pytest.raises(CCDASecurityError):
            self.parser.parse_ccda_document(None)

    def test_ccda_external_entity_detection(self):
        """
        SECURITY TEST: Verify external entity references are detected.
        """
        malicious_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <data>&externalEntity;</data>
  <system>SYSTEM "file:///etc/passwd"</system>
</ClinicalDocument>"""
        
        with pytest.raises(CCDASecurityError) as excinfo:
            self.parser.parse_ccda_document(malicious_xml)
        
        assert "External entity references are not allowed" in str(excinfo.value)

    def test_ccda_invalid_xml_structure(self, invalid_ccda_document):
        """
        VALIDATION TEST: Verify invalid CCDA structure is detected.
        """
        with pytest.raises(CCDAValidationError) as excinfo:
            self.parser.parse_ccda_document(invalid_ccda_document)
        
        assert "Invalid root element" in str(excinfo.value)

    def test_ccda_malformed_xml_rejection(self):
        """
        VALIDATION TEST: Verify malformed XML is rejected.
        """
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <unclosed_tag>
  <another_tag>content</another_tag>
</ClinicalDocument>"""
        
        with pytest.raises(CCDAParsingError):
            self.parser.parse_ccda_document(malformed_xml)

    def test_ccda_document_metadata_extraction(self, diabetes_ccda_document):
        """
        TEST: Verify document metadata is correctly extracted.
        """
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify metadata structure
        assert "metadata" in result
        metadata = result["metadata"]
        
        # Verify document ID extraction
        assert metadata["document_id"] == "CCDA-DIABETES-001"
        
        # Verify title extraction
        assert metadata["title"] == "Diabetes Management Summary"
        
        # Verify effective time extraction
        assert metadata["effective_time"] == "20240201120000"
        
        # Verify template IDs are extracted
        assert "template_ids" in metadata
        assert "2.16.840.1.113883.10.20.22.1.1" in metadata["template_ids"]

    def test_ccda_to_fhir_transformation_integrity(self, diabetes_ccda_document):
        """
        INTEGRATION TEST: Verify CCDA data maintains integrity through transformation.
        
        This test ensures that critical data preservation is maintained when
        CCDA data is prepared for FHIR processing pipeline.
        """
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify all critical sections were parsed
        sections = result["sections"]
        assert "medications" in sections
        assert "results" in sections
        assert "vital_signs" in sections
        assert "allergies" in sections
        
        # Verify preservation hashes are present for all critical data
        for medication in sections["medications"]:
            assert "preservation_hash" in medication
            assert medication["preservation_hash"] is not None
        
        for lab_result in sections["results"]:
            assert "preservation_hash" in lab_result
            assert lab_result["preservation_hash"] is not None
        
        for vital_sign in sections["vital_signs"]:
            assert "preservation_hash" in vital_sign
            assert vital_sign["preservation_hash"] is not None

    def test_ccda_processing_timestamp_validation(self, diabetes_ccda_document):
        """
        TEST: Verify processing metadata is correctly added.
        """
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify processing metadata
        assert result["document_type"] == "ccda"
        assert result["parser_version"] == self.parser.parser_version
        assert "processing_timestamp" in result
        assert result["security_validated"] is True

    def test_ccda_cardiac_medication_preservation(self, cardiac_ccda_document):
        """
        CRITICAL TEST: Verify cardiac medications with narrow therapeutic windows.
        
        Tests preservation of digoxin and warfarin - medications where exact
        dosing is critical for patient safety.
        """
        result = self.parser.parse_ccda_document(cardiac_ccda_document)
        
        medications = result["sections"]["medications"]
        assert len(medications) == 2
        
        # Test digoxin (narrow therapeutic window)
        digoxin = medications[0]
        assert digoxin["substance_name"] == "Digoxin 0.125 MG Oral Tablet"
        assert digoxin["dosage_amount"] == "0.125"  # Critical precision
        assert digoxin["dosage_unit"] == "mg"
        assert digoxin["frequency"] == "Every 24 h"
        
        # Test warfarin (variable dosing based on INR)
        warfarin = medications[1]
        assert warfarin["substance_name"] == "Warfarin Sodium 2.5 MG Oral Tablet"
        assert warfarin["dosage_amount"] == "2.5"  # Critical precision
        assert warfarin["dosage_unit"] == "mg"
        assert warfarin["frequency"] == "Every 24 h"

    def test_ccda_cardiac_lab_monitoring(self, cardiac_ccda_document):
        """
        CRITICAL TEST: Verify lab results for medication monitoring.
        
        Tests preservation of INR and digoxin levels - critical for
        medication safety monitoring.
        """
        result = self.parser.parse_ccda_document(cardiac_ccda_document)
        
        lab_results = result["sections"]["results"]
        assert len(lab_results) == 2
        
        # Test INR result (warfarin monitoring)
        inr_result = lab_results[0]
        assert inr_result["test_name"] == "INR"
        assert inr_result["test_code"] == "6301-6"
        assert inr_result["value"] == "2.3"  # Critical for warfarin dosing
        assert inr_result["unit"] == "1"
        assert inr_result["reference_range"] == "Target range: 2.0-3.0"
        
        # Test digoxin level (digoxin monitoring)
        digoxin_result = lab_results[1]
        assert digoxin_result["test_name"] == "Digoxin"
        assert digoxin_result["test_code"] == "10535-3"
        assert digoxin_result["value"] == "1.2"  # Critical for digoxin safety
        assert digoxin_result["unit"] == "ng/mL"
        assert digoxin_result["reference_range"] == "Therapeutic range: 0.8-2.0 ng/mL"

    def test_ccda_preservation_hash_consistency(self, diabetes_ccda_document):
        """
        INTEGRITY TEST: Verify preservation hashes are consistent and deterministic.
        
        This ensures that the same clinical data always produces the same hash,
        enabling reliable integrity validation.
        """
        # Parse document twice
        result1 = self.parser.parse_ccda_document(diabetes_ccda_document)
        result2 = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify medication hashes are identical
        meds1 = result1["sections"]["medications"]
        meds2 = result2["sections"]["medications"]
        
        for i in range(len(meds1)):
            assert meds1[i]["preservation_hash"] == meds2[i]["preservation_hash"]
        
        # Verify lab result hashes are identical
        labs1 = result1["sections"]["results"]
        labs2 = result2["sections"]["results"]
        
        for i in range(len(labs1)):
            assert labs1[i]["preservation_hash"] == labs2[i]["preservation_hash"]

    def test_ccda_section_template_id_recognition(self, diabetes_ccda_document):
        """
        TEST: Verify CCDA section template IDs are correctly recognized.
        """
        result = self.parser.parse_ccda_document(diabetes_ccda_document)
        
        # Verify all expected sections are recognized by template ID
        sections = result["sections"]
        expected_sections = ["medications", "results", "vital_signs", "allergies"]
        
        for expected_section in expected_sections:
            assert expected_section in sections
            assert len(sections[expected_section]) > 0

    def test_ccda_error_handling_graceful_degradation(self):
        """
        TEST: Verify parser handles partial document corruption gracefully.
        """
        # CCDA with corrupted medication section but valid structure
        partial_ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id extension="PARTIAL-001" root="1.2.3.4.5"/>
  <code code="34133-9" displayName="Test"/>
  <title>Partial Document</title>
  <effectiveTime value="20240201120000"/>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
          <code code="10160-0" displayName="MEDICATIONS"/>
          <title>MEDICATIONS</title>
          <!-- Corrupted entry - should not crash parser -->
          <entry>
            <substanceAdministration>
              <consumable>
                <!-- Missing required elements -->
              </consumable>
            </substanceAdministration>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        
        # Should not raise exception, but return empty medications list
        result = self.parser.parse_ccda_document(partial_ccda)
        assert "medications" in result["sections"]
        # Corrupted entry should be skipped, resulting in empty list
        assert len(result["sections"]["medications"]) == 0

    def _generate_test_preservation_hash(self, data: Dict[str, Any]) -> str:
        """Generate preservation hash for testing consistency."""
        critical_fields = sorted([
            f"{k}:{v}" for k, v in data.items() 
            if k not in ['preservation_hash', 'ai_enhancement_allowed']
        ])
        data_string = "|".join(critical_fields)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()[:16]


class TestCCDAParserPerformance:
    """Performance tests for CCDA parser."""
    
    def setup_method(self):
        """Setup performance test fixtures."""
        self.parser = CCDAParser()
    
    def test_ccda_large_document_processing_time(self):
        """
        PERFORMANCE TEST: Verify large CCDA documents process within time limits.
        """
        import time
        
        # Create large CCDA document (not oversized, but substantial)
        large_ccda = self._create_large_ccda_document()
        
        start_time = time.time()
        result = self.parser.parse_ccda_document(large_ccda)
        processing_time = time.time() - start_time
        
        # Should process within 5 seconds (reasonable for clinical use)
        assert processing_time < 5.0
        assert result["document_type"] == "ccda"
        assert result["security_validated"] is True
    
    def _create_large_ccda_document(self) -> str:
        """Create large but valid CCDA document for performance testing."""
        # Create CCDA with many medication entries
        base_ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id extension="LARGE-001" root="1.2.3.4.5"/>
  <code code="34133-9" displayName="Large Document"/>
  <title>Large Test Document</title>
  <effectiveTime value="20240201120000"/>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
          <code code="10160-0" displayName="MEDICATIONS"/>
          <title>MEDICATIONS</title>"""
        
        # Add many medication entries
        for i in range(100):
            base_ccda += f"""
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-{i:03d}"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="24" unit="h"/>
              </effectiveTime>
              <routeCode code="PO" displayName="Oral"/>
              <doseQuantity value="1" unit="TAB"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="12345{i}" displayName="Test Medication {i}"/>
                    <name>Test Medication {i}</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>"""
        
        base_ccda += """
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        
        return base_ccda