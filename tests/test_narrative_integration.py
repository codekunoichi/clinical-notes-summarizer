"""
Integration tests for AI narrative enhancement with hybrid clinical processor.

These tests validate the complete end-to-end pipeline including:
- FHIR data parsing and extraction
- Critical data preservation (medications, labs, vitals)
- AI narrative enhancement for patient comprehension
- Safety validation and medical accuracy preservation
- Clinical validation scenarios with realistic examples
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime

from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.summarizer.narrative_enhancement import EnhancementSettings
from src.models.clinical import SafetyLevel, ProcessingType


class TestNarrativeIntegration:
    """Test complete integration of narrative enhancement with hybrid processor."""
    
    @pytest.fixture
    def processor_with_ai(self):
        """Create processor with AI enhancement enabled."""
        return HybridClinicalProcessor(enable_ai_enhancement=True)
    
    @pytest.fixture
    def processor_without_ai(self):
        """Create processor with AI enhancement disabled."""
        return HybridClinicalProcessor(enable_ai_enhancement=False)
    
    @pytest.fixture
    def cardiac_emergency_bundle(self):
        """FHIR bundle for cardiac emergency scenario."""
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "cardiac-patient-001",
                        "name": [{"family": "CardiacPatient", "given": ["John"]}],
                        "gender": "male",
                        "birthDate": "1965-03-15"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "condition-001",
                        "code": {
                            "text": "Patient presents with acute ST-elevation myocardial infarction requiring emergent percutaneous coronary intervention"
                        },
                        "clinicalStatus": {
                            "coding": [{"display": "Active"}]
                        }
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-aspirin",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/cardiac-patient-001"},
                        "medicationCodeableConcept": {
                            "text": "Aspirin 81mg tablets"
                        },
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily",
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-clopidogrel",
                        "status": "active", 
                        "intent": "order",
                        "subject": {"reference": "Patient/cardiac-patient-001"},
                        "medicationCodeableConcept": {
                            "text": "Clopidogrel 75mg tablets"
                        },
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily",
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "CarePlan",
                        "id": "care-plan-001",
                        "description": "Administer dual antiplatelet therapy with aspirin and clopidogrel. Monitor cardiac enzymes q6h. Patient should maintain strict adherence to Mediterranean diet with sodium restriction <2g/day."
                    }
                }
            ]
        }
    
    def test_ai_enhancement_vs_no_ai_comparison(self, processor_with_ai, processor_without_ai, cardiac_emergency_bundle):
        """
        Compare processing with and without AI enhancement to ensure AI improves readability
        while preserving critical medical information.
        """
        # Process with AI enhancement
        result_with_ai = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Process without AI enhancement  
        result_without_ai = processor_without_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Both should have same number of medications
        assert len(result_with_ai.medications) == len(result_without_ai.medications)
        assert len(result_with_ai.medications) == 2  # Aspirin and Clopidogrel
        
        # Medication details should be identical (preserved exactly)
        for ai_med, no_ai_med in zip(result_with_ai.medications, result_without_ai.medications):
            assert ai_med.medication_name == no_ai_med.medication_name
            assert ai_med.dosage == no_ai_med.dosage
            assert ai_med.frequency == no_ai_med.frequency
            assert ai_med.route == no_ai_med.route
            assert ai_med.instructions == no_ai_med.instructions
        
        # AI version should have enhanced narratives
        assert result_with_ai.chief_complaint is not None
        assert result_without_ai.chief_complaint is None
        
        assert result_with_ai.care_instructions is not None
        assert result_without_ai.care_instructions is None
        
        # AI version should show appropriate processing metadata
        assert result_with_ai.processing_metadata.ai_processed is True
        assert result_with_ai.processing_metadata.processing_type == ProcessingType.AI_ENHANCED
        assert result_with_ai.processing_metadata.safety_level == SafetyLevel.NARRATIVE
        
        # Non-AI version should show no AI processing
        assert result_without_ai.processing_metadata.ai_processed is False
        assert result_without_ai.processing_metadata.processing_type == ProcessingType.PRESERVED
        assert result_without_ai.processing_metadata.safety_level == SafetyLevel.CRITICAL
        
        # Safety validation should pass for both
        assert result_with_ai.safety_validation.passed is True
        assert result_without_ai.safety_validation.passed is True
    
    def test_medical_term_simplification_in_cardiac_scenario(self, processor_with_ai, cardiac_emergency_bundle):
        """
        Test that complex cardiac medical terms are appropriately simplified for patients
        while maintaining medical accuracy.
        """
        result = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Should have enhanced chief complaint
        assert result.chief_complaint is not None
        chief_complaint = result.chief_complaint.lower()
        
        # Should contain patient-friendly terms
        assert "heart attack" in chief_complaint or "myocardial infarction" in chief_complaint
        
        # Should contain explanation for complex procedure if mentioned
        if "percutaneous coronary intervention" in result.chief_complaint.lower():
            assert "heart" in chief_complaint and ("procedure" in chief_complaint or "intervention" in chief_complaint)
        
        # Care instructions should be simplified
        if result.care_instructions:
            care_text = result.care_instructions.lower()
            
            # Should have simplified medication instructions
            if "dual antiplatelet therapy" in care_text:
                assert "blood thinner" in care_text or "prevent clots" in care_text or "aspirin" in care_text
            
            # Should have simplified monitoring instructions
            if "q6h" in care_text:
                assert "6 hours" in care_text or "every 6 hours" in care_text
        
        # All medication information should remain exact
        for medication in result.medications:
            # Medication names should be preserved exactly
            assert medication.medication_name in ["Aspirin 81mg tablets", "Clopidogrel 75mg tablets"]
            
            # Dosages should be preserved exactly
            assert medication.dosage == "1 tablet"
            assert medication.frequency == "1 time(s) per 1 d"
    
    def test_enhancement_settings_impact(self, processor_with_ai, cardiac_emergency_bundle):
        """
        Test that different enhancement settings produce appropriate results.
        """
        # Test conservative settings
        conservative_settings = EnhancementSettings(
            enhancement_aggressiveness="conservative",
            preserve_medical_terminology=True
        )
        processor_with_ai.set_enhancement_settings(conservative_settings)
        
        result_conservative = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Test aggressive settings
        aggressive_settings = EnhancementSettings(
            enhancement_aggressiveness="aggressive",
            preserve_medical_terminology=False,
            target_grade_level=6
        )
        processor_with_ai.set_enhancement_settings(aggressive_settings)
        
        result_aggressive = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Both should have chief complaints
        assert result_conservative.chief_complaint is not None
        assert result_aggressive.chief_complaint is not None
        
        # Aggressive setting should be more readable (shorter or simpler)
        conservative_text = result_conservative.chief_complaint.lower()
        aggressive_text = result_aggressive.chief_complaint.lower()
        
        # Conservative should preserve more medical terms
        if "myocardial infarction" in conservative_text:
            # Aggressive should more likely use "heart attack"
            assert "heart attack" in aggressive_text
        
        # Both should preserve medication safety
        assert len(result_conservative.medications) == len(result_aggressive.medications)
        for cons_med, agg_med in zip(result_conservative.medications, result_aggressive.medications):
            assert cons_med.medication_name == agg_med.medication_name
            assert cons_med.dosage == agg_med.dosage
    
    def test_safety_validation_for_enhanced_narratives(self, processor_with_ai, cardiac_emergency_bundle):
        """
        Test that safety validation catches any potential issues with AI-enhanced narratives.
        """
        result = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        # Safety validation should pass
        assert result.safety_validation.passed is True
        assert len(result.safety_validation.errors) == 0
        
        # Critical medical information should be preserved
        assert result.safety_validation.critical_fields_preserved.get("medications", False)
        
        # AI processing should be correctly flagged for narrative fields only
        ai_flags = result.safety_validation.ai_processing_flags
        
        # Medications should never be AI processed
        assert ai_flags.get("medications", True) is False  # Should be False (not AI processed)
        
        # Check that all required disclaimers are present
        assert len(result.disclaimers) >= 3
        disclaimer_text = " ".join(result.disclaimers).lower()
        assert "educational purposes" in disclaimer_text
        assert "consult" in disclaimer_text
        assert "emergency" in disclaimer_text
    
    def test_error_handling_in_integration(self, processor_with_ai):
        """
        Test that the integrated system handles errors gracefully.
        """
        # Test with malformed FHIR bundle
        malformed_bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "status": "active",
                        # Missing required fields
                    }
                }
            ]
        }
        
        # Should handle errors gracefully without crashing
        try:
            result = processor_with_ai.process_clinical_data(malformed_bundle)
            # If it succeeds, should have safe defaults
            assert result.patient_id is not None
            assert result.safety_validation.passed in [True, False]  # Should have validation result
        except Exception as e:
            # If it fails, should fail gracefully with clear error
            assert "validation" in str(e).lower() or "processing" in str(e).lower()
    
    def test_performance_requirements(self, processor_with_ai, cardiac_emergency_bundle):
        """
        Test that the integrated system meets performance requirements.
        """
        import time
        
        start_time = time.time()
        result = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        processing_time = time.time() - start_time
        
        # Should process within 5 seconds as per requirements
        assert processing_time < 5.0, f"Processing took {processing_time:.2f} seconds, should be < 5s"
        
        # Should successfully generate summary
        assert result is not None
        assert result.summary_id is not None
        assert result.patient_id is not None
    
    def test_readability_improvement_validation(self, processor_with_ai, cardiac_emergency_bundle):
        """
        Test that AI enhancement actually improves readability while preserving accuracy.
        """
        result = processor_with_ai.process_clinical_data(cardiac_emergency_bundle)
        
        if result.chief_complaint:
            # Original complex medical text
            original_text = "Patient presents with acute ST-elevation myocardial infarction requiring emergent percutaneous coronary intervention"
            
            # Enhanced text should be different and more readable
            enhanced_text = result.chief_complaint
            
            assert enhanced_text != original_text
            
            # Should contain patient-friendly language
            enhanced_lower = enhanced_text.lower()
            assert any(term in enhanced_lower for term in [
                "heart attack", "heart", "sudden", "blood vessel", "artery", "procedure"
            ])
            
            # Should still contain critical medical concepts (even if explained)
            medical_concepts_preserved = any(concept in enhanced_lower for concept in [
                "myocardial", "heart", "artery", "coronary", "intervention", "procedure"
            ])
            assert medical_concepts_preserved, f"Enhanced text lost medical concepts: {enhanced_text}"


class TestClinicalValidationScenarios:
    """Test realistic clinical scenarios with comprehensive validation."""
    
    @pytest.fixture
    def processor(self):
        """Create processor for clinical validation."""
        return HybridClinicalProcessor(enable_ai_enhancement=True)
    
    def test_diabetes_management_scenario(self, processor):
        """
        Test comprehensive diabetes management scenario with multiple medications
        and complex care instructions.
        """
        diabetes_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "diabetes-patient",
                        "name": [{"family": "DiabetesPatient", "given": ["Maria"]}]
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "diabetes-condition",
                        "code": {
                            "text": "Type 2 diabetes mellitus with diabetic nephropathy and peripheral neuropathy"
                        }
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "metformin",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/diabetes-patient"},
                        "medicationCodeableConcept": {"text": "Metformin 500mg tablets"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth twice daily with meals",
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
                            "timing": {"repeat": {"frequency": 2, "period": 1, "periodUnit": "d"}}
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "CarePlan",
                        "id": "diabetes-care-plan",
                        "description": "Monitor blood glucose levels q.i.d. Maintain HbA1c <7%. Follow diabetic diet with carbohydrate counting. Regular podiatric examinations for neuropathy monitoring."
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(diabetes_bundle)
        
        # Should successfully process diabetes scenario
        assert result is not None
        assert len(result.medications) == 1
        
        # Medication should be preserved exactly
        metformin = result.medications[0]
        assert metformin.medication_name == "Metformin 500mg tablets"
        assert metformin.dosage == "1 tablet"
        assert "twice daily" in metformin.frequency or "2" in metformin.frequency
        
        # Narrative should be enhanced for patient understanding
        if result.chief_complaint:
            complaint_text = result.chief_complaint.lower()
            # Should explain diabetes in patient-friendly terms
            assert "diabetes" in complaint_text
            # Should explain complications
            assert any(term in complaint_text for term in ["kidney", "nerve", "feet"])
        
        if result.care_instructions:
            care_text = result.care_instructions.lower()
            # Should simplify medical abbreviations
            if "q.i.d" in care_text:
                assert "4 times" in care_text or "four times" in care_text
            # Should explain HbA1c
            if "hba1c" in care_text:
                assert "blood sugar" in care_text or "glucose" in care_text
    
    def test_pediatric_asthma_scenario(self, processor):
        """
        Test pediatric asthma scenario with age-appropriate simplification.
        """
        pediatric_bundle = {
            "resourceType": "Bundle",
            "type": "collection", 
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pediatric-patient",
                        "name": [{"family": "AsthmaChild", "given": ["Tommy"]}],
                        "birthDate": "2015-08-10"  # 8 years old
                    }
                },
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": "asthma-condition",
                        "code": {
                            "text": "Moderate persistent asthma with recurrent exacerbations requiring bronchodilator therapy"
                        }
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "albuterol",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/pediatric-patient"},
                        "medicationCodeableConcept": {"text": "Albuterol HFA inhaler 90 mcg/actuation"},
                        "dosageInstruction": [{
                            "text": "Inhale 2 puffs every 4 hours as needed for wheezing or shortness of breath",
                            "doseAndRate": [{"doseQuantity": {"value": 2, "unit": "puff"}}]
                        }]
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(pediatric_bundle)
        
        # Should process pediatric scenario appropriately
        assert result is not None
        assert len(result.medications) == 1
        
        # Medication details preserved
        albuterol = result.medications[0]
        assert "Albuterol" in albuterol.medication_name
        assert albuterol.dosage == "2 puff"
        
        # Narrative should be simplified for pediatric understanding
        if result.chief_complaint:
            complaint_text = result.chief_complaint.lower()
            # Should use child-friendly language
            assert "asthma" in complaint_text
            # Should explain breathing problems simply
            assert any(term in complaint_text for term in [
                "breathing", "breath", "lungs", "wheeze", "cough"
            ])
    
    def test_geriatric_polypharmacy_scenario(self, processor):
        """
        Test complex geriatric scenario with multiple medications and interactions.
        """
        geriatric_bundle = {
            "resourceType": "Bundle", 
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "geriatric-patient",
                        "name": [{"family": "Elderly", "given": ["Eleanor"]}],
                        "birthDate": "1945-11-22"  # 78 years old
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "warfarin",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/geriatric-patient"},
                        "medicationCodeableConcept": {"text": "Warfarin sodium 2.5mg tablets"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet once daily, adjust based on INR results",
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "CarePlan",
                        "id": "anticoagulation-plan",
                        "description": "Anticoagulation therapy for atrial fibrillation. Monitor INR weekly. Target INR 2.0-3.0. Watch for bleeding complications including epistaxis, hematuria, or melena."
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(geriatric_bundle)
        
        # Should handle complex geriatric medication
        assert result is not None
        assert len(result.medications) == 1
        
        # Warfarin details must be preserved exactly (high-risk medication)
        warfarin = result.medications[0]
        assert "Warfarin" in warfarin.medication_name
        assert "2.5mg" in warfarin.medication_name
        assert warfarin.dosage == "1 tablet"
        
        # Care instructions should explain complex medical monitoring
        if result.care_instructions:
            care_text = result.care_instructions.lower()
            # Should explain INR monitoring in patient-friendly terms
            if "inr" in care_text:
                assert any(term in care_text for term in [
                    "blood test", "blood level", "clotting", "bleeding"
                ])
            # Should explain bleeding risks clearly
            assert any(warning in care_text for warning in [
                "bleeding", "blood", "bruising"
            ])


class TestSafetyAndComplianceValidation:
    """Test safety and compliance requirements for healthcare applications."""
    
    @pytest.fixture
    def processor(self):
        """Create processor for safety testing."""
        return HybridClinicalProcessor(enable_ai_enhancement=True)
    
    def test_medication_safety_never_compromised(self, processor):
        """
        CRITICAL TEST: Ensure medication safety is never compromised by AI processing.
        """
        high_risk_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "high-risk-patient"
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "insulin",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/high-risk-patient"},
                        "medicationCodeableConcept": {"text": "Insulin glargine 100 units/mL pen"},
                        "dosageInstruction": [{
                            "text": "Inject 28 units subcutaneously once daily at bedtime",
                            "doseAndRate": [{"doseQuantity": {"value": 28, "unit": "units"}}]
                        }]
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "digoxin",
                        "status": "active",
                        "intent": "order", 
                        "subject": {"reference": "Patient/high-risk-patient"},
                        "medicationCodeableConcept": {"text": "Digoxin 0.25mg tablets"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily",
                            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                        }]
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(high_risk_bundle)
        
        # Should process high-risk medications
        assert len(result.medications) == 2
        
        # Every high-risk medication detail must be preserved exactly
        medication_names = [med.medication_name for med in result.medications]
        assert "Insulin glargine 100 units/mL pen" in medication_names
        assert "Digoxin 0.25mg tablets" in medication_names
        
        # Insulin dosing must be exact (life-threatening if wrong)
        insulin = next(med for med in result.medications if "Insulin" in med.medication_name)
        assert "28 units" in insulin.dosage
        
        # Digoxin dosing must be exact (narrow therapeutic window)
        digoxin = next(med for med in result.medications if "Digoxin" in med.medication_name)
        assert "1 tablet" in digoxin.dosage
        assert "0.25mg" in digoxin.medication_name
        
        # Safety validation must pass
        assert result.safety_validation.passed is True
        assert len(result.safety_validation.errors) == 0
    
    def test_disclaimer_compliance(self, processor):
        """
        Test that all required healthcare disclaimers are included.
        """
        simple_bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "patient"}}
            ]
        }
        
        result = processor.process_clinical_data(simple_bundle)
        
        # Should have all required disclaimers
        assert len(result.disclaimers) >= 3
        
        disclaimer_text = " ".join(result.disclaimers).lower()
        
        # Required disclaimer elements
        assert "educational purposes only" in disclaimer_text
        assert "does not replace professional medical advice" in disclaimer_text
        assert "consult your healthcare provider" in disclaimer_text
        assert "emergency" in disclaimer_text
        assert "911" in disclaimer_text
    
    def test_processing_auditability(self, processor):
        """
        Test that all processing is fully auditable and traceable.
        """
        test_bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "audit-patient"}},
                {
                    "resource": {
                        "resourceType": "Condition",
                        "code": {"text": "Patient has hypertension requiring medication management"}
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(test_bundle)
        
        # Should have complete processing metadata
        metadata = result.processing_metadata
        
        assert metadata.processed_at is not None
        assert metadata.processing_version is not None
        assert metadata.safety_level is not None
        assert metadata.processing_type is not None
        assert isinstance(metadata.ai_processed, bool)
        assert isinstance(metadata.validation_passed, bool)
        assert isinstance(metadata.validation_errors, list)
        
        # Should have safety validation details
        safety = result.safety_validation
        
        assert safety.validation_id is not None
        assert safety.data_type is not None
        assert isinstance(safety.passed, bool)
        assert isinstance(safety.errors, list)
        assert isinstance(safety.warnings, list)
        assert isinstance(safety.critical_fields_preserved, dict)
        assert isinstance(safety.ai_processing_flags, dict)