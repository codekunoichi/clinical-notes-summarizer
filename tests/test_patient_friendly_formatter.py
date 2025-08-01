"""
Test cases for the Patient-Friendly Output Formatter.

Tests the "fridge magnet" format output for various clinical scenarios
with comprehensive safety and accessibility validation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.models.clinical import (
    ClinicalSummary,
    MedicationSummary,
    LabResultSummary,
    AppointmentSummary,
    ProcessingMetadata,
    SafetyValidation,
    ProcessingType,
    SafetyLevel
)
from src.formatter.patient_friendly import (
    PatientFriendlyFormatter,
    FormattedOutput,
    OutputFormat,
    AccessibilitySettings,
    VisualHierarchy,
    PrintSettings
)


class TestPatientFriendlyFormatter:
    """Test suite for patient-friendly output formatter."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.formatter = PatientFriendlyFormatter()
        
        # Create base processing metadata
        self.base_metadata = ProcessingMetadata(
            safety_level=SafetyLevel.CRITICAL,
            processing_type=ProcessingType.PRESERVED,
            ai_processed=False,
            validation_passed=True,
            validation_errors=[]
        )
        
        # Create base safety validation
        self.base_safety = SafetyValidation(
            validation_id="test-validation-001",
            data_type="clinical_summary",
            passed=True,
            errors=[],
            warnings=[],
            critical_fields_preserved={"medications": True},
            ai_processing_flags={"medications": False}
        )
    
    def create_sample_clinical_summary(self, scenario: str = "diabetes") -> ClinicalSummary:
        """Create sample clinical summary for different scenarios."""
        
        if scenario == "diabetes":
            # Diabetes management scenario
            medications = [
                MedicationSummary(
                    medication_name="Metformin",
                    dosage="500 mg",
                    frequency="twice daily",
                    route="oral",
                    instructions="Take with meals",
                    purpose="To help control blood sugar levels",
                    important_notes="May cause stomach upset if taken without food",
                    metadata=self.base_metadata
                ),
                MedicationSummary(
                    medication_name="Insulin Glargine",
                    dosage="20 units",
                    frequency="once daily",
                    route="subcutaneous injection",
                    instructions="Inject at bedtime",
                    purpose="Long-acting insulin to control overnight blood sugar",
                    important_notes="Rotate injection sites to prevent lipodystrophy",
                    metadata=self.base_metadata
                )
            ]
            
            appointments = [
                AppointmentSummary(
                    date="2025-08-15",
                    time="9:00 AM",
                    provider="Dr. Sarah Johnson",
                    location="Endocrinology Clinic, 123 Medical Center Dr",
                    phone="(555) 123-4567",
                    purpose="Diabetes management follow-up",
                    preparation="Bring glucose meter and log book",
                    metadata=self.base_metadata
                )
            ]
            
            lab_results = [
                LabResultSummary(
                    test_name="Hemoglobin A1C",
                    value="7.2%",
                    reference_range="< 7.0%",
                    status="slightly elevated",
                    explanation="This shows your average blood sugar over the past 3 months",
                    metadata=self.base_metadata
                )
            ]
            
        elif scenario == "post_surgical":
            # Post-surgical care scenario
            medications = [
                MedicationSummary(
                    medication_name="Ibuprofen",
                    dosage="600 mg",
                    frequency="every 6 hours",
                    route="oral",
                    instructions="Take with food, maximum 4 doses per day",
                    purpose="Pain and swelling management",
                    important_notes="Do not exceed maximum daily dose",
                    metadata=self.base_metadata
                ),
                MedicationSummary(
                    medication_name="Cephalexin",
                    dosage="500 mg",
                    frequency="four times daily",
                    route="oral",
                    instructions="Take every 6 hours for 7 days",
                    purpose="Prevent infection at surgical site",
                    important_notes="Complete entire course even if feeling better",
                    metadata=self.base_metadata
                )
            ]
            
            appointments = [
                AppointmentSummary(
                    date="2025-08-10",
                    time="2:00 PM",
                    provider="Dr. Michael Chen",
                    location="Surgical Associates, 456 Hospital Blvd",
                    phone="(555) 987-6543",
                    purpose="Post-operative wound check",
                    preparation="Wear loose clothing for easy access to surgical site",
                    metadata=self.base_metadata
                )
            ]
            
            lab_results = []
            
        elif scenario == "emergency_discharge":
            # Emergency department discharge scenario
            medications = [
                MedicationSummary(
                    medication_name="Albuterol Inhaler",
                    dosage="2 puffs",
                    frequency="every 4-6 hours as needed",
                    route="inhalation",
                    instructions="Shake well before use, rinse mouth after",
                    purpose="Open airways during asthma symptoms",
                    important_notes="Seek immediate care if not effective",
                    metadata=self.base_metadata
                )
            ]
            
            appointments = [
                AppointmentSummary(
                    date="2025-08-05",
                    time="10:00 AM",
                    provider="Dr. Lisa Wang",
                    location="Primary Care Clinic, 789 Health St",
                    phone="(555) 456-7890",
                    purpose="Follow-up for asthma exacerbation",
                    preparation="Bring inhaler and peak flow meter",
                    metadata=self.base_metadata
                )
            ]
            
            lab_results = []
            
        else:
            # Default minimal scenario
            medications = []
            appointments = []
            lab_results = []
        
        return ClinicalSummary(
            summary_id="test-summary-001",
            patient_id="patient-123",
            medications=medications,
            lab_results=lab_results,
            appointments=appointments,
            chief_complaint="Managing ongoing health conditions",
            diagnosis_explanation="Working with your healthcare team to optimize treatment",
            care_instructions="Follow medication schedule and attend appointments",
            follow_up_guidance="Contact provider with questions or concerns",
            safety_validation=self.base_safety,
            processing_metadata=self.base_metadata,
            disclaimers=[]
        )
    
    def test_formatter_initialization(self):
        """Test that formatter initializes correctly with default settings."""
        formatter = PatientFriendlyFormatter()
        
        assert formatter is not None
        assert formatter.accessibility_settings is not None
        assert formatter.visual_hierarchy is not None
        assert formatter.print_settings is not None
    
    def test_format_diabetes_scenario_html(self):
        """Test formatting diabetes management summary to HTML."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify output structure
        assert isinstance(formatted_output, FormattedOutput)
        assert formatted_output.format == OutputFormat.HTML
        assert formatted_output.content is not None
        assert len(formatted_output.content) > 0
        
        # Verify critical information is present
        assert "Metformin" in formatted_output.content
        assert "500 mg" in formatted_output.content
        assert "twice daily" in formatted_output.content
        assert "Dr. Sarah Johnson" in formatted_output.content
        assert "2025-08-15" in formatted_output.content
        
        # Verify safety disclaimers are included
        assert "educational purposes only" in formatted_output.content.lower()
        assert "emergency" in formatted_output.content.lower()
        
        # Verify accessibility attributes
        assert formatted_output.accessibility_compliant
        assert formatted_output.mobile_responsive
        assert formatted_output.print_friendly
    
    def test_format_post_surgical_scenario_html(self):
        """Test formatting post-surgical care summary to HTML."""
        clinical_summary = self.create_sample_clinical_summary("post_surgical")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify post-surgical specific content
        assert "Ibuprofen" in formatted_output.content
        assert "600 mg" in formatted_output.content
        assert "every 6 hours" in formatted_output.content
        assert "Cephalexin" in formatted_output.content
        assert "Post-operative wound check" in formatted_output.content
        
        # Verify critical post-surgical instructions
        assert "Complete entire course" in formatted_output.content
        assert "surgical site" in formatted_output.content.lower()
    
    def test_format_emergency_discharge_scenario_html(self):
        """Test formatting emergency discharge summary to HTML."""
        clinical_summary = self.create_sample_clinical_summary("emergency_discharge")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify emergency-specific content
        assert "Albuterol" in formatted_output.content
        assert "2 puffs" in formatted_output.content
        assert "as needed" in formatted_output.content
        assert "asthma" in formatted_output.content.lower()
        
        # Verify emergency instructions
        assert "immediate care" in formatted_output.content.lower()
        assert "not effective" in formatted_output.content.lower()
    
    def test_format_summary_to_pdf(self):
        """Test formatting clinical summary to PDF."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.PDF
        )
        
        # Verify PDF output structure
        assert formatted_output.format == OutputFormat.PDF
        assert formatted_output.content_type == "application/pdf"
        assert formatted_output.content is not None
        assert isinstance(formatted_output.content, bytes)
        
        # Verify PDF is valid (basic check)
        assert formatted_output.content.startswith(b'%PDF')
        assert formatted_output.print_friendly
    
    def test_format_summary_to_plain_text(self):
        """Test formatting clinical summary to plain text."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.PLAIN_TEXT
        )
        
        # Verify plain text output
        assert formatted_output.format == OutputFormat.PLAIN_TEXT
        assert formatted_output.content_type == "text/plain"
        assert isinstance(formatted_output.content, str)
        
        # Verify accessibility for screen readers
        assert formatted_output.accessibility_compliant
        
        # Verify content structure without HTML tags
        assert "<" not in formatted_output.content
        assert ">" not in formatted_output.content
        assert "Metformin" in formatted_output.content
        assert "Dr. Sarah Johnson" in formatted_output.content
    
    def test_critical_information_prominence(self):
        """Test that critical information is prominently displayed."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify critical sections are marked with high priority
        content = formatted_output.content
        
        # Emergency contact info should be prominent
        assert 'class="critical-info"' in content or 'emergency' in content.lower()
        
        # Medication information should be in priority section
        assert 'medication' in content.lower()
        assert 'Metformin' in content
        
        # Next appointment should be prominent
        assert 'appointment' in content.lower()
        assert '2025-08-15' in content
    
    def test_mobile_responsive_design(self):
        """Test that HTML output includes mobile-responsive design elements."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify mobile-responsive meta tags and CSS
        assert 'viewport' in content
        assert 'mobile' in content.lower() or 'responsive' in content.lower()
        assert formatted_output.mobile_responsive
        
        # Verify flexible layout elements
        assert 'flex' in content or 'grid' in content or '@media' in content
    
    def test_print_friendly_layout(self):
        """Test that output includes print-friendly styling."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify print-specific CSS rules
        assert '@media print' in content or 'print' in content.lower()
        assert formatted_output.print_friendly
        
        # Verify content is structured for printing
        assert 'page-break' in content or 'break-' in content
    
    def test_accessibility_compliance_wcag(self):
        """Test WCAG 2.1 AA accessibility compliance."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify accessibility attributes  
        assert 'alt=' in content or 'aria-' in content
        assert 'role=' in content
        assert formatted_output.accessibility_compliant
        
        # Verify heading hierarchy
        assert '<h1' in content
        assert '<h2' in content or '<h3' in content
        
        # Verify color contrast considerations
        assert 'color:' in content or 'background' in content
    
    def test_visual_hierarchy_implementation(self):
        """Test proper visual hierarchy for patient comprehension."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify hierarchical structure
        assert content.find('<h1') < content.find('<h2') or content.find('<h1') < content.find('<h3')
        
        # Verify important sections are prominently styled
        assert 'font-weight: bold' in content or 'font-weight:bold' in content
        assert 'font-size:' in content or 'font-size:' in content
    
    def test_error_handling_invalid_input(self):
        """Test error handling for invalid input data."""
        # Test with None input
        with pytest.raises(ValueError, match="Clinical summary cannot be None"):
            self.formatter.format_summary(None, OutputFormat.HTML)
        
        # Test with invalid output format
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        with pytest.raises(ValueError, match="Invalid output format"):
            self.formatter.format_summary(clinical_summary, "invalid_format")
    
    def test_safety_validation_preservation(self):
        """Test that safety validation information is preserved in output."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        # Modify safety validation to include warnings
        clinical_summary.safety_validation.warnings = ["Test warning message"]
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify safety information is included
        content = formatted_output.content
        assert "validation" in content.lower() or "safety" in content.lower()
        
        # Verify warnings are displayed if present
        if clinical_summary.safety_validation.warnings:
            assert "warning" in content.lower()
    
    def test_medication_formatting_accuracy(self):
        """Test that medication information is formatted accurately without alteration."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        original_med = clinical_summary.medications[0]
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify exact medication details are preserved
        assert original_med.medication_name in content
        assert original_med.dosage in content
        assert original_med.frequency in content
        assert original_med.route in content
        assert original_med.instructions in content
    
    def test_emergency_information_prominence(self):
        """Test that emergency information is prominently displayed."""
        clinical_summary = self.create_sample_clinical_summary("emergency_discharge")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify emergency information is prominent
        assert "emergency" in content.lower()
        assert "911" in content or "call" in content.lower()
        
        # Verify emergency styling
        assert 'emergency' in content.lower() or 'urgent' in content.lower()
    
    def test_pediatric_formatting_considerations(self):
        """Test formatting considerations for pediatric patients."""
        # This would test age-appropriate language and formatting
        # For now, we'll test the basic structure
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        # Simulate pediatric patient scenario
        formatter_with_pediatric_settings = PatientFriendlyFormatter()
        formatter_with_pediatric_settings.set_patient_age_group("pediatric")
        
        formatted_output = formatter_with_pediatric_settings.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Basic test - full implementation would include age-appropriate language
        assert formatted_output is not None
        assert formatted_output.content is not None
    
    def test_geriatric_formatting_considerations(self):
        """Test formatting considerations for geriatric patients."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        # Simulate geriatric patient scenario with larger fonts and simpler layout
        formatter_with_geriatric_settings = PatientFriendlyFormatter()
        formatter_with_geriatric_settings.set_patient_age_group("geriatric")
        
        formatted_output = formatter_with_geriatric_settings.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        content = formatted_output.content
        
        # Verify larger fonts and clear spacing for geriatric patients
        assert 'font-size' in content
        assert formatted_output.accessibility_compliant
    
    def test_multilingual_structure_preparation(self):
        """Test that formatter structure supports future multilingual implementation."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        # Test basic structure for future localization
        formatter_with_locale = PatientFriendlyFormatter()
        formatter_with_locale.set_locale("en-US")  # Default locale
        
        formatted_output = formatter_with_locale.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Basic test - full implementation would include locale-specific formatting
        assert formatted_output is not None
        assert formatted_output.locale == "en-US"
    
    def test_performance_large_summary(self):
        """Test formatter performance with large clinical summaries."""
        # Create large clinical summary with many medications and appointments
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        # Add many medications to test performance
        for i in range(10):
            med = MedicationSummary(
                medication_name=f"Test Medication {i}",
                dosage=f"{i*10} mg",
                frequency="once daily",
                route="oral",
                instructions=f"Take medication {i} as directed",
                metadata=self.base_metadata
            )
            clinical_summary.medications.append(med)
        
        # Test formatting time (should be under 5 seconds per requirements)
        import time
        start_time = time.time()
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance requirement (<5 seconds)
        assert processing_time < 5.0, f"Formatting took {processing_time} seconds, should be < 5"
        assert formatted_output is not None
    
    def test_content_length_for_fridge_magnet_format(self):
        """Test that content is appropriately sized for fridge magnet format."""
        clinical_summary = self.create_sample_clinical_summary("diabetes")
        
        formatted_output = self.formatter.format_summary(
            clinical_summary,
            output_format=OutputFormat.HTML
        )
        
        # Verify content is concise but complete
        content_text = self.formatter.extract_text_content(formatted_output.content)
        
        # Should be comprehensive but scannable (estimated ~500-2000 characters)
        assert 500 <= len(content_text) <= 3000, f"Content length {len(content_text)} should be 500-3000 chars for fridge magnet format"
        
        # Verify all critical information is still present
        assert "Metformin" in content_text
        assert "Dr. Sarah Johnson" in content_text
        assert "2025-08-15" in content_text


class TestFormatterModels:
    """Test the formatter output models."""
    
    def test_formatted_output_model_validation(self):
        """Test FormattedOutput model validation."""
        # Valid formatted output
        output = FormattedOutput(
            format=OutputFormat.HTML,
            content="<html>test content</html>",
            content_type="text/html",
            accessibility_compliant=True,
            mobile_responsive=True,
            print_friendly=True
        )
        
        assert output.format == OutputFormat.HTML
        assert output.content_type == "text/html"
        assert output.accessibility_compliant
        assert output.mobile_responsive
        assert output.print_friendly
    
    def test_accessibility_settings_model(self):
        """Test AccessibilitySettings model."""
        settings = AccessibilitySettings(
            wcag_level="AA",
            high_contrast=True,
            large_fonts=False,
            screen_reader_optimized=True
        )
        
        assert settings.wcag_level == "AA"
        assert settings.high_contrast
        assert not settings.large_fonts
        assert settings.screen_reader_optimized
    
    def test_visual_hierarchy_model(self):
        """Test VisualHierarchy model."""
        hierarchy = VisualHierarchy(
            primary_sections=["medications", "appointments"],
            secondary_sections=["lab_results"],
            emphasis_elements=["emergency_contact", "critical_alerts"]
        )
        
        assert "medications" in hierarchy.primary_sections
        assert "appointments" in hierarchy.primary_sections
        assert "lab_results" in hierarchy.secondary_sections
        assert "emergency_contact" in hierarchy.emphasis_elements


class TestFormatterIntegration:
    """Test formatter integration with existing clinical processing."""
    
    def test_integration_with_hybrid_processor(self):
        """Test formatter integration with HybridClinicalProcessor."""
        # This test would verify end-to-end processing
        # from FHIR input to formatted patient-friendly output
        
        # Mock FHIR bundle
        mock_fhir_bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "medicationCodeableConcept": {
                            "text": "Metformin"
                        },
                        "dosageInstruction": [
                            {
                                "text": "500 mg twice daily with meals"
                            }
                        ]
                    }
                }
            ]
        }
        
        # Import would happen here - testing the integration concept
        # from src.summarizer.hybrid_processor import HybridClinicalProcessor
        # processor = HybridClinicalProcessor()
        # clinical_summary = processor.process_clinical_data(mock_fhir_bundle)
        # 
        # formatter = PatientFriendlyFormatter()
        # formatted_output = formatter.format_summary(clinical_summary, OutputFormat.HTML)
        # 
        # assert formatted_output is not None
        # assert "Metformin" in formatted_output.content
        
        # For now, just verify the structure is ready for integration
        assert True  # Placeholder for actual integration test