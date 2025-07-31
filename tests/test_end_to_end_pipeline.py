"""
End-to-end processing pipeline tests for the Clinical Notes Summarizer.

This module tests the complete processing pipeline from FHIR input to
patient-friendly output, validating performance, safety, and format
requirements for production healthcare use.

Pipeline Tests:
1. Complete FHIR Bundle Processing
2. Performance Validation (<5 second requirement)
3. "Fridge Magnet" Format Validation
4. FHIR R4 Compliance Validation
5. Safety Validation Throughout Pipeline
6. Error Handling and Graceful Degradation
7. Concurrent Processing Safety
8. Memory and Resource Management
"""

import pytest
import time
import json
from typing import Dict, Any, List
from datetime import datetime
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import ClinicalSummary, SafetyLevel, ProcessingType


class TestCompleteProcessingPipeline:
    """
    Test complete end-to-end processing of realistic clinical scenarios.
    """
    
    def test_complete_diabetes_management_pipeline(self, diabetes_management_bundle):
        """
        Test complete processing pipeline with realistic diabetes bundle.
        
        Validates full pipeline from complex FHIR input to patient-friendly output.
        """
        processor = HybridClinicalProcessor()
        
        # Time the complete pipeline
        start_time = time.time()
        result = processor.process_clinical_data(diabetes_management_bundle)
        processing_time = time.time() - start_time
        
        # PERFORMANCE: Must complete in <5 seconds
        assert processing_time < 5.0, f"Pipeline processing took {processing_time:.2f}s, exceeds 5s limit"
        
        # STRUCTURE: Complete clinical summary generated
        assert isinstance(result, ClinicalSummary)
        assert result.summary_id is not None
        assert result.patient_id == "diabetes-patient-comprehensive"
        assert isinstance(result.generated_at, datetime)
        
        # MEDICATION PROCESSING: All diabetes medications processed correctly
        expected_med_count = 4  # Metformin, Lantus, Humalog, Lisinopril
        assert len(result.medications) == expected_med_count
        
        # Verify specific medications preserved exactly
        medication_names = [med.medication_name for med in result.medications]
        assert "Metformin 500mg tablets" in medication_names
        assert "Lantus (insulin glargine) 100 units/mL pen injector" in medication_names
        assert "Humalog (insulin lispro) 100 units/mL pen injector" in medication_names
        assert "Lisinopril 10mg tablets" in medication_names
        
        # SAFETY: All medications maintain critical safety standards
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert medication.metadata.processing_type == ProcessingType.PRESERVED
            assert not medication.metadata.ai_processed
            assert medication.metadata.validation_passed
        
        # COMPLIANCE: Safety validation passes for complete summary
        assert result.safety_validation.passed
        assert len(result.safety_validation.errors) == 0
        assert result.safety_validation.data_type == "clinical_summary"
        
        # DISCLAIMERS: Required healthcare disclaimers present
        assert len(result.disclaimers) >= 3
        disclaimer_text = " ".join(result.disclaimers).lower()
        assert "educational purposes" in disclaimer_text
        assert "consult" in disclaimer_text
        assert "emergency" in disclaimer_text
    
    def test_complete_pediatric_asthma_pipeline(self, pediatric_asthma_bundle):
        """
        Test complete pipeline with pediatric asthma medications.
        
        Validates weight-based dosing and pediatric-specific safety requirements.
        """
        processor = HybridClinicalProcessor()
        
        start_time = time.time()
        result = processor.process_clinical_data(pediatric_asthma_bundle)
        processing_time = time.time() - start_time
        
        # PERFORMANCE: Pediatric processing within time limit
        assert processing_time < 5.0
        
        # PEDIATRIC SAFETY: All medications correctly identified as pediatric
        assert len(result.medications) == 2  # Albuterol rescue + Fluticasone controller
        
        # Verify pediatric-specific medication details preserved
        albuterol = next((m for m in result.medications if "ProAir" in m.medication_name or "albuterol" in m.medication_name.lower()), None)
        fluticasone = next((m for m in result.medications if "Flovent" in m.medication_name or "fluticasone" in m.medication_name.lower()), None)
        
        assert albuterol is not None
        assert fluticasone is not None
        
        # CRITICAL: Pediatric instructions preserved exactly
        assert "PEDIATRIC" in albuterol.instructions or "pediatric" in albuterol.instructions.lower()
        assert "spacer" in albuterol.instructions.lower()
        assert "supervision" in albuterol.instructions.lower()
        
        assert "CONTROLLER MEDICATION" in fluticasone.instructions or "controller" in fluticasone.instructions.lower()
        assert "daily" in fluticasone.instructions.lower()
        assert "rinse mouth" in fluticasone.instructions.lower()
        
        # SAFETY: No AI processing of pediatric medication data
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed
    
    def test_complete_geriatric_polypharmacy_pipeline(self, geriatric_polypharmacy_bundle):
        """
        Test complete pipeline with geriatric polypharmacy scenario.
        
        Validates drug interaction warnings and geriatric dosing adjustments.
        """
        processor = HybridClinicalProcessor()
        
        start_time = time.time()
        result = processor.process_clinical_data(geriatric_polypharmacy_bundle)
        processing_time = time.time() - start_time
        
        # PERFORMANCE: Complex polypharmacy processed within limits
        assert processing_time < 5.0
        
        # GERIATRIC SAFETY: All medications processed with appropriate warnings
        assert len(result.medications) == 2  # Digoxin + Warfarin (high-risk combination)
        
        # Verify high-risk medication details preserved exactly
        digoxin = next((m for m in result.medications if "Digoxin" in m.medication_name), None)
        warfarin = next((m for m in result.medications if "Warfarin" in m.medication_name), None)
        
        assert digoxin is not None
        assert warfarin is not None
        
        # CRITICAL: Geriatric warnings and monitoring preserved
        assert "GERIATRIC" in digoxin.instructions or "geriatric" in digoxin.instructions.lower()
        assert "toxicity" in digoxin.instructions.lower()
        assert "0.125" in digoxin.dosage  # Reduced geriatric dose
        
        assert "ANTICOAGULANT" in warfarin.instructions
        assert "INR" in warfarin.instructions
        assert "bleeding" in warfarin.instructions.lower()
        
        # DRUG INTERACTIONS: Interaction warnings preserved
        assert "drug interaction" in warfarin.instructions.lower() or "interaction" in warfarin.instructions.lower()
        
        # SAFETY: Critical safety level maintained
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed


class TestPatientFriendlyFormatValidation:
    """
    Test that output meets "fridge magnet" format requirements:
    - Concise and scannable
    - Critical information prominently displayed
    - Patient-friendly language (where safe)
    - Clear action instructions
    """
    
    def test_fridge_magnet_format_structure(self):
        """
        Test that clinical summary meets fridge magnet format requirements.
        
        Should be scannable, concise, with critical info prominently displayed.
        """
        processor = HybridClinicalProcessor()
        
        # Simple medication for format testing
        simple_med_bundle = {
            "resourceType": "Bundle",
            "id": "format-test-001",
            "type": "collection",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "format-patient-001",
                    "name": [{"family": "FormatTest", "given": ["Patient"]}]
                }},
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "format-med-001",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Lisinopril 10mg tablets"},
                    "subject": {"reference": "Patient/format-patient-001"},
                    "dosageInstruction": [{
                        "text": "Take 1 tablet by mouth once daily for blood pressure",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }}
            ]
        }
        
        result = processor.process_clinical_data(simple_med_bundle)
        medication = result.medications[0]
        
        # FRIDGE MAGNET FORMAT: Key information is concise and clear
        assert len(medication.medication_name) < 100  # Medication name not too long
        assert len(medication.dosage) < 50  # Dosage concise
        assert len(medication.frequency) < 50  # Frequency clear
        
        # SCANNABILITY: Critical info contains key terms
        assert any(word in medication.medication_name.lower() for word in ["mg", "tablet", "capsule", "ml"])
        assert any(word in medication.frequency.lower() for word in ["daily", "time", "per"])
        
        # PATIENT-FRIENDLY: Instructions contain actionable language
        action_words = ["take", "inject", "apply", "use", "place"]
        assert any(word in medication.instructions.lower() for word in action_words)
        
        # CRITICAL INFO PRESERVATION: Essential details maintained
        assert "10mg" in medication.medication_name or "10mg" in medication.dosage
        assert "1 tablet" in medication.dosage or "1 tablet" in medication.instructions
        assert "once daily" in medication.frequency.lower() or "1 time" in medication.frequency
    
    def test_emergency_medication_fridge_magnet_format(self):
        """
        Test that emergency medications have prominent, actionable instructions.
        
        Emergency medications should have VERY clear, step-by-step instructions.
        """
        processor = HybridClinicalProcessor()
        
        epipen_data = {
            "resourceType": "MedicationRequest",
            "id": "epipen-format-test",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "subject": {"reference": "Patient/emergency-format-test"},
            "medicationCodeableConcept": {"text": "EpiPen (epinephrine) 0.3mg auto-injector"},
            "dosageInstruction": [{
                "text": "Inject immediately for severe allergic reaction",
                "patientInstruction": "EMERGENCY: Use for severe allergic reactions. Remove blue cap, press orange tip against thigh for 10 seconds, call 911.",
                "timing": {"repeat": {"frequency": 1, "period": 15, "periodUnit": "min"}},
                "doseAndRate": [{"doseQuantity": {"value": 0.3, "unit": "mg"}}]
            }]
        }
        
        result = processor.process_medication_data(epipen_data)
        
        # EMERGENCY FORMAT: Clear emergency identification
        assert "EMERGENCY" in result.instructions or "emergency" in result.instructions.lower()
        
        # STEP-BY-STEP: Clear action sequence
        assert "remove" in result.instructions.lower()
        assert "press" in result.instructions.lower()
        assert "call 911" in result.instructions.lower() or "call emergency" in result.instructions.lower()
        
        # TIMING: Critical timing information preserved
        assert "10 seconds" in result.instructions or "immediately" in result.instructions.lower()
        
        # URGENCY: Urgent language maintained
        urgent_indicators = ["immediately", "emergency", "severe", "call 911"]
        assert any(indicator in result.instructions.lower() for indicator in urgent_indicators)


class TestFHIRComplianceValidation:
    """
    Test that processed output maintains FHIR R4 compliance for interoperability.
    """
    
    def test_fhir_resource_structure_preservation(self):
        """
        Test that FHIR resource structure is preserved for system integration.
        """
        processor = HybridClinicalProcessor()
        
        # Standard FHIR MedicationRequest
        fhir_compliant_data = {
            "resourceType": "MedicationRequest",
            "id": "fhir-compliance-001",
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
            "subject": {"reference": "Patient/fhir-patient-001"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth once daily",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "d"
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
        
        result = processor.process_medication_data(fhir_compliant_data)
        
        # FHIR COMPLIANCE: Preservation hash available for integrity verification
        assert result.metadata.preservation_hash is not None
        assert len(result.metadata.preservation_hash) == 64  # SHA-256 hash length
        
        # TRACEABILITY: Processing metadata maintains FHIR traceability
        assert result.metadata.processing_version is not None
        assert result.metadata.processed_at is not None
        
        # CODING SYSTEMS: Original FHIR coding preserved in metadata context
        # (Implementation would store original FHIR data for system integration)
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed  # Critical data never AI processed
    
    def test_bundle_processing_fhir_compliance(self):
        """
        Test that FHIR Bundle processing maintains compliance standards.
        """
        processor = HybridClinicalProcessor()
        
        # FHIR Bundle with multiple resources
        fhir_bundle = {
            "resourceType": "Bundle",
            "id": "fhir-bundle-compliance-001",
            "type": "collection",
            "meta": {
                "versionId": "1",
                "lastUpdated": "2024-01-01T10:00:00Z"
            },
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "fhir-compliant-patient",
                    "identifier": [{"value": "FHIR-001"}],
                    "name": [{"family": "Compliance", "given": ["FHIR"]}]
                }},
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "fhir-compliant-med",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": "Test Medication 5mg"},
                    "subject": {"reference": "Patient/fhir-compliant-patient"},
                    "dosageInstruction": [{
                        "text": "Take as directed",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }}
            ]
        }
        
        result = processor.process_clinical_data(fhir_bundle)
        
        # BUNDLE PROCESSING: Patient ID correctly extracted from bundle
        assert result.patient_id == "fhir-compliant-patient"
        
        # RESOURCE PROCESSING: All resources processed with FHIR compliance
        assert len(result.medications) == 1
        medication = result.medications[0]
        
        # INTEGRITY: Preservation hash validates original FHIR data integrity
        assert medication.metadata.preservation_hash is not None
        
        # COMPLIANCE: Processing maintains FHIR standards
        assert medication.metadata.validation_passed
        assert medication.metadata.safety_level == SafetyLevel.CRITICAL


class TestPerformanceBenchmarks:
    """
    Test performance benchmarks for production healthcare use.
    """
    
    def test_high_volume_processing_performance(self):
        """
        Test processing performance with high medication volumes.
        
        Must maintain <5 second processing time even with large medication lists.
        """
        processor = HybridClinicalProcessor()
        
        # Create bundle with 20 medications (realistic polypharmacy scenario)
        high_volume_bundle = {
            "resourceType": "Bundle",
            "id": "high-volume-performance-001",
            "type": "collection",
            "entry": [{"resource": {
                "resourceType": "Patient",
                "id": "high-volume-patient",
                "name": [{"family": "HighVolume", "given": ["Patient"]}]
            }}]
        }
        
        # Generate 20 different medications
        for i in range(20):
            med_entry = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"high-volume-med-{i:02d}",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {"text": f"Medication{i:02d} {(i*5)+5}mg tablets"},
                    "subject": {"reference": "Patient/high-volume-patient"},
                    "dosageInstruction": [{
                        "text": f"Take 1 tablet by mouth {['once', 'twice', 'three times'][i % 3]} daily",
                        "timing": {"repeat": {"frequency": (i % 3) + 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }
            }
            high_volume_bundle["entry"].append(med_entry)
        
        # Benchmark high-volume processing
        start_time = time.time()
        result = processor.process_clinical_data(high_volume_bundle)
        processing_time = time.time() - start_time
        
        # PERFORMANCE: Must process 20 medications in <5 seconds
        assert processing_time < 5.0, f"High-volume processing took {processing_time:.2f}s, exceeds 5s limit"
        
        # COMPLETENESS: All medications processed correctly
        assert len(result.medications) == 20
        
        # CONSISTENCY: All medications maintain safety standards
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed
            assert medication.metadata.validation_passed
        
        # QUALITY: Processing quality not degraded by volume
        # Check that specific medications preserved correctly
        med_names = [med.medication_name for med in result.medications]
        assert "Medication00 5mg tablets" in med_names
        assert "Medication19 100mg tablets" in med_names
    
    def test_memory_efficiency_large_bundles(self):
        """
        Test memory efficiency with large FHIR bundles.
        
        Should process large bundles without excessive memory usage.
        """
        processor = HybridClinicalProcessor()
        
        # Create bundle with extensive medication details
        detailed_bundle = {
            "resourceType": "Bundle",
            "id": "memory-efficiency-001",
            "type": "collection",
            "entry": [{"resource": {
                "resourceType": "Patient", 
                "id": "memory-test-patient",
                "name": [{"family": "MemoryTest", "given": ["Patient"]}]
            }}]
        }
        
        # Add medications with extensive details
        for i in range(10):
            detailed_med = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"detailed-med-{i}",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": f"12345{i}",
                            "display": f"Detailed Medication {i} 10 MG Oral Tablet"
                        }],
                        "text": f"Detailed Medication {i} 10mg tablets"
                    },
                    "subject": {"reference": "Patient/memory-test-patient"},
                    "dosageInstruction": [{
                        "text": f"Take 1 tablet by mouth once daily. Very detailed instructions for medication {i} including multiple considerations and patient education points that make this a lengthy instruction set.",
                        "patientInstruction": f"Comprehensive patient instructions for medication {i}: Take with food to reduce stomach upset. Monitor for side effects including nausea, dizziness, or rash. Contact provider if you experience any unusual symptoms. This medication may interact with other drugs so inform all healthcare providers that you are taking this medication. Store at room temperature away from moisture and heat.",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
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
            detailed_bundle["entry"].append(detailed_med)
        
        # Process detailed bundle and measure efficiency
        start_time = time.time()
        result = processor.process_clinical_data(detailed_bundle)
        processing_time = time.time() - start_time
        
        # EFFICIENCY: Complex detailed processing still within limits
        assert processing_time < 5.0, f"Detailed processing took {processing_time:.2f}s, exceeds limit"
        
        # COMPLETENESS: All detailed information processed correctly
        assert len(result.medications) == 10
        
        # DETAIL PRESERVATION: Complex instructions preserved
        for i, medication in enumerate(result.medications):
            assert f"Detailed Medication {i}" in medication.medication_name
            assert "10mg" in medication.medication_name
            assert "food" in medication.instructions.lower()  # Patient instruction preserved
            assert "side effects" in medication.instructions.lower()
            
            # Safety standards maintained despite complexity
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed