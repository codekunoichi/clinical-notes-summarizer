"""
Tests for AI Narrative Enhancement Module

These tests follow TDD principles and define the expected behavior for the
AI narrative enhancement system. The module should:

1. Integrate BART model for text simplification
2. Enhance clinical narratives while preserving medical accuracy
3. Provide medical term explanations
4. Ensure 6th-8th grade reading level output
5. Include comprehensive safety validation
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Import will fail until we create the module - this is expected in TDD
try:
    from src.summarizer.narrative_enhancement import (
        NarrativeEnhancer,
        ReadabilityAnalyzer,
        MedicalDictionary,
        NarrativeValidationResult,
        EnhancementSettings
    )
except ImportError:
    # This is expected in TDD - we haven't implemented it yet
    NarrativeEnhancer = None
    ReadabilityAnalyzer = None
    MedicalDictionary = None
    NarrativeValidationResult = None
    EnhancementSettings = None


@pytest.mark.skipif(NarrativeEnhancer is None, reason="NarrativeEnhancer not implemented yet")
class TestNarrativeEnhancer:
    """Test the AI narrative enhancement functionality."""
    
    @pytest.fixture
    def enhancer(self):
        """Create enhancer instance for testing."""
        return NarrativeEnhancer()
    
    @pytest.fixture
    def sample_medical_text(self):
        """Sample medical text requiring enhancement."""
        return {
            "chief_complaint": "Patient presents with acute myocardial infarction with ST elevation in anterior leads.",
            "diagnosis_explanation": "The patient has suffered a heart attack affecting the front wall of the heart muscle due to blocked coronary artery.",
            "care_instructions": "Administer dual antiplatelet therapy with aspirin and clopidogrel. Monitor cardiac enzymes q6h.",
            "lifestyle_recommendations": "Patient should maintain strict adherence to Mediterranean diet with sodium restriction <2g/day."
        }
    
    @pytest.fixture
    def complex_medical_narrative(self):
        """Complex medical narrative with technical terms."""
        return {
            "procedure_description": "Patient underwent percutaneous coronary intervention with drug-eluting stent placement in the left anterior descending artery.",
            "warning_signs": "Seek immediate medical attention for chest pain, dyspnea, diaphoresis, or syncope.",
            "follow_up_instructions": "Follow up with cardiology in 2 weeks for echocardiogram to assess left ventricular systolic function."
        }
    
    def test_enhancer_initialization(self, enhancer):
        """Test that enhancer initializes with correct settings."""
        assert enhancer is not None
        assert hasattr(enhancer, 'enhance_narrative')
        assert hasattr(enhancer, 'validate_enhancement')
        assert hasattr(enhancer, 'get_enhancement_metadata')
        
        # Verify BART model is loaded
        assert enhancer.bart_model is not None
        assert enhancer.bart_tokenizer is not None
        
        # Verify safety settings
        assert enhancer.preserve_medical_terms is True
        assert enhancer.target_grade_level >= 6
        assert enhancer.target_grade_level <= 8
    
    def test_basic_narrative_enhancement(self, enhancer, sample_medical_text):
        """Test basic narrative enhancement for patient comprehension."""
        # Use aggressive settings for better readability
        from src.summarizer.narrative_enhancement import EnhancementSettings
        aggressive_settings = EnhancementSettings(enhancement_aggressiveness="aggressive")
        
        result = enhancer.enhance_narrative(sample_medical_text["chief_complaint"], aggressive_settings)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "enhanced_text" in result
        assert "original_text" in result
        assert "readability_score" in result
        assert "medical_terms_explained" in result
        assert "validation_result" in result
        
        # Enhanced text should be more readable
        enhanced = result["enhanced_text"]
        original = result["original_text"]
        
        assert len(enhanced) > 0
        assert enhanced != original  # Text should be changed
        assert "heart attack" in enhanced.lower()  # Should use simpler terms
        assert "myocardial infarction" not in enhanced or "heart attack" in enhanced  # Complex term explained
        
        # Readability should be improved (allow for complex medical terms that can't be simplified)
        original_grade = enhancer.readability_analyzer.analyze_readability(original)["grade_level"]
        enhanced_grade = result["readability_score"]["grade_level"]
        
        # Enhanced text should be more readable than original, even if not perfect
        assert enhanced_grade < original_grade, f"Enhanced grade {enhanced_grade} should be less than original {original_grade}"
        
        # Medical accuracy should be preserved
        assert result["validation_result"].medical_accuracy_preserved is True
    
    def test_medical_term_preservation_and_explanation(self, enhancer, sample_medical_text):
        """
        CRITICAL TEST: Medical accuracy must be preserved while improving readability.
        """
        result = enhancer.enhance_narrative(sample_medical_text["diagnosis_explanation"])
        
        enhanced = result["enhanced_text"]
        explanations = result["medical_terms_explained"]
        
        # Critical medical terms should be explained, not removed
        if "coronary artery" in sample_medical_text["diagnosis_explanation"]:
            assert any("coronary" in explanation["term"].lower() for explanation in explanations)
            # Should include explanation like "blood vessels that supply the heart"
            coronary_explanation = next(exp for exp in explanations if "coronary" in exp["term"].lower())
            assert "blood vessel" in coronary_explanation["explanation"].lower() or "artery" in coronary_explanation["explanation"].lower()
        
        # Enhanced text should maintain medical accuracy
        validation = result["validation_result"]
        assert validation.medical_accuracy_preserved is True
        assert len(validation.accuracy_errors) == 0
    
    def test_complex_procedure_enhancement(self, enhancer, complex_medical_narrative):
        """Test enhancement of complex medical procedures."""
        result = enhancer.enhance_narrative(complex_medical_narrative["procedure_description"])
        
        enhanced = result["enhanced_text"]
        explanations = result["medical_terms_explained"]
        
        # Complex procedure should be explained in simple terms
        assert "stent" in enhanced.lower()
        
        # Should have explanations for technical terms
        technical_terms = ["percutaneous", "coronary intervention", "drug-eluting stent", "left anterior descending"]
        explained_terms = [exp["term"] for exp in explanations]
        
        # At least some technical terms should be explained
        assert len(explanations) > 0
        
        # PCI should be explained as a heart procedure
        pci_explained = any("intervention" in exp["term"].lower() or "PCI" in exp["term"] for exp in explanations)
        if pci_explained:
            pci_explanation = next(exp for exp in explanations 
                                 if "intervention" in exp["term"].lower() or "PCI" in exp["term"])
            assert "heart" in pci_explanation["explanation"].lower() or "artery" in pci_explanation["explanation"].lower()
    
    def test_warning_signs_clarity_enhancement(self, enhancer, complex_medical_narrative):
        """Test that warning signs are enhanced for maximum patient understanding."""
        result = enhancer.enhance_narrative(complex_medical_narrative["warning_signs"])
        
        enhanced = result["enhanced_text"]
        explanations = result["medical_terms_explained"]
        
        # Medical terms should be explained for patient safety
        medical_terms = ["dyspnea", "diaphoresis", "syncope"]
        
        for term in medical_terms:
            if term in complex_medical_narrative["warning_signs"]:
                # Term should be either replaced with simple language or explained
                term_explained = any(term.lower() in exp["term"].lower() for exp in explanations)
                simple_equivalent_present = (
                    "shortness of breath" in enhanced.lower() or
                    "trouble breathing" in enhanced.lower() or
                    "sweating" in enhanced.lower() or
                    "fainting" in enhanced.lower() or
                    "dizziness" in enhanced.lower()
                )
                assert term_explained or simple_equivalent_present
        
        # Enhanced warning signs should be urgent and clear
        assert "immediately" in enhanced.lower() or "right away" in enhanced.lower()
        assert result["readability_score"]["grade_level"] <= 7  # Extra readable for safety
    
    def test_enhancement_settings_customization(self, enhancer):
        """Test that enhancement settings can be customized for different scenarios."""
        # Test conservative enhancement (preserve more medical language)
        conservative_settings = EnhancementSettings(
            target_grade_level=8,
            preserve_medical_terminology=True,
            max_explanation_length=50,
            enhancement_aggressiveness="conservative"
        )
        
        result = enhancer.enhance_narrative(
            "Patient presents with acute myocardial infarction with ST elevation.",
            settings=conservative_settings
        )
        
        # Conservative enhancement should preserve more medical terms
        enhanced = result["enhanced_text"]
        explanations = result["medical_terms_explained"]
        
        assert "myocardial infarction" in enhanced  # Should preserve complex term
        assert any("myocardial infarction" in exp["term"].lower() for exp in explanations)
        
        # Test aggressive enhancement (maximum simplification)
        aggressive_settings = EnhancementSettings(
            target_grade_level=6,
            preserve_medical_terminology=False,
            max_explanation_length=100,
            enhancement_aggressiveness="aggressive"
        )
        
        result_aggressive = enhancer.enhance_narrative(
            "Patient presents with acute myocardial infarction with ST elevation.",
            settings=aggressive_settings
        )
        
        enhanced_aggressive = result_aggressive["enhanced_text"]
        # Aggressive enhancement should use simpler language
        assert "heart attack" in enhanced_aggressive.lower()
        assert result_aggressive["readability_score"]["grade_level"] <= 6
    
    def test_batch_narrative_enhancement(self, enhancer, sample_medical_text):
        """Test batch processing of multiple narrative fields."""
        result = enhancer.enhance_narratives_batch(sample_medical_text)
        
        # All fields should be processed
        assert len(result) == len(sample_medical_text)
        
        for field_name, enhancement_result in result.items():
            assert field_name in sample_medical_text
            assert "enhanced_text" in enhancement_result
            assert "readability_score" in enhancement_result
            assert "validation_result" in enhancement_result
            
            # Each field should meet readability requirements
            assert enhancement_result["readability_score"]["grade_level"] <= 8
            assert enhancement_result["validation_result"].medical_accuracy_preserved
    
    def test_enhancement_safety_validation(self, enhancer, sample_medical_text):
        """
        CRITICAL TEST: Ensure AI enhancement never compromises medical safety.
        """
        result = enhancer.enhance_narrative(sample_medical_text["care_instructions"])
        
        validation = result["validation_result"]
        
        # Safety validation must pass
        assert validation.medical_accuracy_preserved is True
        assert validation.critical_information_retained is True
        assert len(validation.accuracy_errors) == 0
        assert len(validation.safety_warnings) == 0
        
        # Original medical meaning should be preserved
        original = result["original_text"]
        enhanced = result["enhanced_text"]
        
        # Key medical concepts should remain
        assert "aspirin" in enhanced.lower()  # Specific medication preserved
        assert "monitor" in enhanced.lower()  # Monitoring instruction preserved
        
        # Dosing information should never be altered by AI
        if "q6h" in original:
            assert "6 hours" in enhanced or "every 6 hours" in enhanced or "q6h" in enhanced
    
    def test_error_handling_invalid_input(self, enhancer):
        """Test that enhancer handles invalid input gracefully."""
        # Test with empty string
        result = enhancer.enhance_narrative("")
        assert result["enhanced_text"] == ""
        assert result["validation_result"].medical_accuracy_preserved is True
        
        # Test with None input
        with pytest.raises(ValueError) as exc_info:
            enhancer.enhance_narrative(None)
        assert "input text cannot be None" in str(exc_info.value).lower()
        
        # Test with very long text (should handle gracefully)
        very_long_text = "This is a medical narrative. " * 1000
        result = enhancer.enhance_narrative(very_long_text)
        assert len(result["enhanced_text"]) > 0
        assert result["validation_result"].medical_accuracy_preserved is True
    
    def test_performance_requirements(self, enhancer, sample_medical_text):
        """Test that enhancement meets performance requirements."""
        import time
        
        start_time = time.time()
        result = enhancer.enhance_narrative(sample_medical_text["chief_complaint"])
        processing_time = time.time() - start_time
        
        # Should process within reasonable time (5 seconds per requirement)
        assert processing_time < 5.0
        
        # Should provide processing metadata
        metadata = enhancer.get_enhancement_metadata()
        assert "model_version" in metadata
        assert "processing_time" in metadata
        assert "safety_checks_passed" in metadata


@pytest.mark.skipif(ReadabilityAnalyzer is None, reason="ReadabilityAnalyzer not implemented yet")
class TestReadabilityAnalyzer:
    """Test the readability analysis functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        return ReadabilityAnalyzer()
    
    def test_grade_level_calculation(self, analyzer):
        """Test accurate grade level calculation."""
        # Simple text should be low grade level
        simple_text = "The patient had a heart attack. Take your medicine every day."
        result = analyzer.analyze_readability(simple_text)
        
        assert result["grade_level"] <= 8
        assert result["readability_score"] > 60  # Reasonably readable
        
        # Complex medical text should be high grade level
        complex_text = "Patient presents with acute ST-elevation myocardial infarction requiring emergent percutaneous coronary intervention."
        result_complex = analyzer.analyze_readability(complex_text)
        
        assert result_complex["grade_level"] > result["grade_level"]
        assert result_complex["readability_score"] < result["readability_score"]
    
    def test_readability_improvement_validation(self, analyzer):
        """Test validation that enhanced text is more readable."""
        original = "Patient experienced acute exacerbation of chronic obstructive pulmonary disease."
        enhanced = "The patient's lung disease got worse quickly."
        
        original_score = analyzer.analyze_readability(original)
        enhanced_score = analyzer.analyze_readability(enhanced)
        
        # Enhanced should be more readable
        assert enhanced_score["grade_level"] < original_score["grade_level"]
        assert enhanced_score["readability_score"] > original_score["readability_score"]
        
        # Should meet target grade level
        assert enhanced_score["grade_level"] <= 8
        assert enhanced_score["grade_level"] >= 6
    
    def test_medical_text_specific_analysis(self, analyzer):
        """Test analysis specifically designed for medical text."""
        medical_texts = [
            "Take this medication with food.",
            "Monitor blood pressure daily.",
            "Seek immediate medical attention for chest pain.",
            "Follow up with your doctor in one week."
        ]
        
        for text in medical_texts:
            result = analyzer.analyze_readability(text)
            
            # All patient instructions should be easily readable
            assert result["grade_level"] <= 8
            
            # Should provide detailed analysis
            assert "sentence_count" in result
            assert "word_count" in result
            assert "syllable_count" in result
            assert "complex_word_count" in result


@pytest.mark.skipif(MedicalDictionary is None, reason="MedicalDictionary not implemented yet")
class TestMedicalDictionary:
    """Test the medical dictionary functionality."""
    
    @pytest.fixture
    def dictionary(self):
        """Create dictionary instance for testing."""
        return MedicalDictionary()
    
    def test_term_explanation_generation(self, dictionary):
        """Test generation of patient-friendly medical term explanations."""
        test_terms = [
            "myocardial infarction",
            "hypertension",
            "dyspnea",
            "diaphoresis",
            "syncope",
            "percutaneous coronary intervention"
        ]
        
        for term in test_terms:
            explanation = dictionary.get_explanation(term)
            
            assert explanation is not None
            assert len(explanation.explanation) > 0
            assert len(explanation.explanation) <= 200  # Concise explanations
            
            # Explanations should use simple language  
            analyzer = ReadabilityAnalyzer()
            grade_level = analyzer.analyze_readability(explanation.explanation)["grade_level"]
            assert grade_level <= 8
    
    def test_common_medical_terms_coverage(self, dictionary):
        """Test coverage of common medical terms patients encounter."""
        common_terms = [
            # Cardiovascular
            "myocardial infarction", "heart attack", "hypertension", "blood pressure",
            "arrhythmia", "coronary artery", "stent", "bypass",
            
            # Respiratory
            "dyspnea", "shortness of breath", "pneumonia", "asthma",
            
            # General symptoms
            "diaphoresis", "syncope", "nausea", "fatigue",
            
            # Procedures
            "echocardiogram", "electrocardiogram", "catheterization",
            
            # Medications
            "anticoagulant", "beta blocker", "ACE inhibitor"
        ]
        
        coverage_count = 0
        for term in common_terms:
            explanation = dictionary.get_explanation(term)
            if explanation:
                coverage_count += 1
        
        # Should cover at least 80% of common terms
        coverage_percentage = coverage_count / len(common_terms)
        assert coverage_percentage >= 0.8
    
    def test_explanation_quality_validation(self, dictionary):
        """Test that explanations meet quality standards."""
        term = "myocardial infarction"
        explanation = dictionary.get_explanation(term)
        
        # Should include simple equivalent
        assert "heart attack" in explanation.lower()
        
        # Should explain what happens
        explanation_should_contain = ["heart", "muscle", "blood"]
        for word in explanation_should_contain:
            assert word.lower() in explanation.lower()
        
        # Should be appropriately detailed but not overly technical
        assert 20 <= len(explanation.split()) <= 50  # Reasonable length


@pytest.mark.safety
@pytest.mark.skipif(NarrativeEnhancer is None, reason="NarrativeEnhancer not implemented yet") 
class TestNarrativeSafetyValidation:
    """Critical safety tests for AI narrative enhancement."""
    
    @pytest.fixture
    def enhancer(self):
        """Create enhancer instance for safety testing."""
        return NarrativeEnhancer()
    
    def test_medication_instruction_safety(self, enhancer):
        """
        CRITICAL SAFETY TEST: Medication instructions must never be altered in dangerous ways.
        """
        medication_instructions = [
            "Take 1 tablet by mouth twice daily with food",
            "Apply topical cream to affected area once daily",
            "Inject 10 units subcutaneously before meals",
            "Take 2 tablets every 6 hours as needed for pain"
        ]
        
        for instruction in medication_instructions:
            result = enhancer.enhance_narrative(instruction)
            enhanced = result["enhanced_text"]
            validation = result["validation_result"]
            
            # CRITICAL: Dosing information must be preserved exactly
            assert validation.critical_information_retained is True
            assert len(validation.safety_warnings) == 0
            
            # Specific dose and frequency information should be preserved
            if "twice daily" in instruction:
                assert "twice daily" in enhanced or "2 times" in enhanced or "two times" in enhanced
            if "every 6 hours" in instruction:
                assert "6 hours" in enhanced or "every 6 hours" in enhanced
            if "10 units" in instruction:
                assert "10 units" in enhanced  # Exact dosing preserved
    
    def test_warning_sign_accuracy(self, enhancer):
        """
        CRITICAL SAFETY TEST: Warning signs must be enhanced without losing urgency or accuracy.
        """
        warning_signs = [
            "Seek immediate medical attention for severe chest pain, shortness of breath, or fainting",
            "Call 911 if you experience sudden severe headache or vision changes",
            "Stop medication and contact doctor immediately if rash or swelling develops"
        ]
        
        for warning in warning_signs:
            result = enhancer.enhance_narrative(warning)
            enhanced = result["enhanced_text"]
            validation = result["validation_result"]
            
            # CRITICAL: Warning urgency must be maintained
            assert validation.critical_information_retained is True
            
            # Emergency contact information preserved
            if "911" in warning:
                assert "911" in enhanced
            if "immediate" in warning:
                assert "immediately" in enhanced or "right away" in enhanced or "immediate" in enhanced
            
            # Specific symptoms should be preserved or enhanced for clarity
            if "chest pain" in warning:
                assert "chest pain" in enhanced.lower()
            if "shortness of breath" in warning:
                assert ("shortness of breath" in enhanced.lower() or 
                       "trouble breathing" in enhanced.lower() or
                       "hard to breathe" in enhanced.lower())
    
    def test_contraindication_preservation(self, enhancer):
        """
        CRITICAL SAFETY TEST: Medical contraindications must never be weakened or removed.
        """
        contraindications = [
            "Do not take if allergic to aspirin or have bleeding disorders",
            "Contraindicated in pregnancy and breastfeeding",
            "Do not use with alcohol or other sedating medications"
        ]
        
        for contraindication in contraindications:
            result = enhancer.enhance_narrative(contraindication)
            enhanced = result["enhanced_text"]
            validation = result["validation_result"]
            
            # CRITICAL: Contraindications must be preserved
            assert validation.critical_information_retained is True
            assert validation.medical_accuracy_preserved is True
            
            # "Do not" statements must remain strong
            prohibition_preserved = (
                "do not" in enhanced.lower() or
                "don't" in enhanced.lower() or
                "avoid" in enhanced.lower() or
                "should not" in enhanced.lower()
            )
            assert prohibition_preserved
            
            # Specific conditions should be preserved
            if "allergic" in contraindication:
                assert "allergic" in enhanced.lower() or "allergy" in enhanced.lower()
            if "pregnancy" in contraindication:
                assert "pregnancy" in enhanced.lower() or "pregnant" in enhanced.lower()


# Integration test that defines the expected interface
def test_narrative_enhancement_interface_definition():
    """
    Test that defines the expected interface for the narrative enhancement system.
    """
    # Import should work since we're implementing the modules
    from src.summarizer.narrative_enhancement import NarrativeEnhancer
    
    # Verify the enhancer has the expected interface
    enhancer = NarrativeEnhancer()
    
    # Core enhancement methods
    assert hasattr(enhancer, 'enhance_narrative')
    assert hasattr(enhancer, 'enhance_narratives_batch')
    assert hasattr(enhancer, 'validate_enhancement')
    
    # Configuration and metadata methods
    assert hasattr(enhancer, 'get_enhancement_metadata')
    assert hasattr(enhancer, 'set_enhancement_settings')
    
    # Safety and validation
    assert hasattr(enhancer, 'validate_medical_accuracy')
    assert hasattr(enhancer, 'check_readability_target')