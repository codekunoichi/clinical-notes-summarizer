"""
Patient-Friendly Clinical Summary Formatter.

This module provides the main PatientFriendlyFormatter class that converts
clinical summaries into patient-friendly "fridge magnet" format with multiple
output options including HTML, PDF, and plain text.
"""

import logging
import uuid
import re
import html
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, Template
from markupsafe import Markup

# PDF generation imports (optional)
PDF_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    PDF_AVAILABLE = True
except (ImportError, OSError) as e:
    # WeasyPrint may not be available or may lack system dependencies
    logger.warning(f"WeasyPrint not available - PDF generation will be limited: {e}")
    HTML = None
    CSS = None
    FontConfiguration = None

from src.models.clinical import ClinicalSummary, MedicationSummary, LabResultSummary, AppointmentSummary
from .models import (
    FormattedOutput,
    OutputFormat,
    AccessibilitySettings,
    VisualHierarchy,
    PrintSettings,
    FormattingPreferences,
    ContentSection,
    FormatterError,
    FormatterValidationResult,
    PatientAgeGroup,
    LanguageCode
)

# Configure logging
logger = logging.getLogger(__name__)


class PatientFriendlyFormatter:
    """
    Main formatter class for converting clinical summaries to patient-friendly format.
    
    This formatter implements the "fridge magnet" concept - creating scannable,
    mobile-responsive output that emphasizes critical information and can be
    easily printed for physical reference.
    """
    
    def __init__(self, 
                 accessibility_settings: Optional[AccessibilitySettings] = None,
                 visual_hierarchy: Optional[VisualHierarchy] = None,
                 print_settings: Optional[PrintSettings] = None,
                 formatting_preferences: Optional[FormattingPreferences] = None):
        """
        Initialize the patient-friendly formatter.
        
        Args:
            accessibility_settings: WCAG compliance and accessibility options
            visual_hierarchy: Configuration for information hierarchy
            print_settings: Settings for print-friendly output
            formatting_preferences: User preferences for formatting
        """
        self.formatter_version = "1.0.0"
        
        # Initialize settings with defaults if not provided
        self.accessibility_settings = accessibility_settings or AccessibilitySettings()
        self.visual_hierarchy = visual_hierarchy or VisualHierarchy()
        self.print_settings = print_settings or PrintSettings()
        self.formatting_preferences = formatting_preferences or FormattingPreferences()
        
        # Initialize Jinja2 environment for template rendering
        try:
            self.jinja_env = Environment(
                loader=PackageLoader('src.formatter', 'templates'),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
        except Exception as e:
            # Fallback to string templates if package loader fails
            logger.warning(f"Failed to load templates from package: {e}. Using fallback templates.")
            self.jinja_env = Environment(autoescape=select_autoescape(['html', 'xml']))
            self._initialize_fallback_templates()
        
        # Add custom filters and functions
        self._add_template_filters()
        
        # Initialize PDF generator
        if PDF_AVAILABLE:
            self.font_config = FontConfiguration()
            self.pdf_generator = True
        else:
            self.font_config = None
            self.pdf_generator = False
        
    def format_summary(self, 
                      clinical_summary: ClinicalSummary, 
                      output_format: OutputFormat,
                      custom_settings: Optional[Dict[str, Any]] = None) -> FormattedOutput:
        """
        Format a clinical summary into patient-friendly output.
        
        Args:
            clinical_summary: The clinical summary to format
            output_format: Desired output format (HTML, PDF, plain text)
            custom_settings: Optional custom settings for this formatting
            
        Returns:
            FormattedOutput with formatted content and metadata
            
        Raises:
            ValueError: If input is invalid or formatting fails
        """
        if clinical_summary is None:
            raise ValueError("Clinical summary cannot be None")
        
        if not isinstance(output_format, OutputFormat):
            if isinstance(output_format, str):
                try:
                    output_format = OutputFormat(output_format.lower())
                except ValueError:
                    raise ValueError(f"Invalid output format: {output_format}")
            else:
                raise ValueError("Invalid output format")
        
        # Apply custom settings if provided
        if custom_settings:
            self._apply_custom_settings(custom_settings)
        
        try:
            # Validate input clinical summary
            validation_result = self._validate_clinical_summary(clinical_summary)
            if not validation_result.passed:
                raise ValueError(f"Clinical summary validation failed: {validation_result.errors}")
            
            # Extract and organize content sections
            content_sections = self._extract_content_sections(clinical_summary)
            
            # Sort sections by priority according to visual hierarchy
            content_sections = self._apply_visual_hierarchy(content_sections)
            
            # Generate formatted output based on format type
            if output_format == OutputFormat.HTML:
                formatted_output = self._format_to_html(clinical_summary, content_sections)
            elif output_format == OutputFormat.PDF:
                formatted_output = self._format_to_pdf(clinical_summary, content_sections)
            elif output_format == OutputFormat.PLAIN_TEXT:
                formatted_output = self._format_to_plain_text(clinical_summary, content_sections)
            elif output_format == OutputFormat.JSON:
                formatted_output = self._format_to_json(clinical_summary, content_sections)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Set the content sections in the output
            formatted_output.sections = content_sections
            
            # Validate the formatted output
            final_validation = self._validate_formatted_output(formatted_output, clinical_summary)
            formatted_output.safety_validated = final_validation.passed
            
            if not final_validation.passed:
                logger.warning(f"Formatted output validation warnings: {final_validation.warnings}")
            
            return formatted_output
            
        except Exception as e:
            logger.error(f"Error formatting clinical summary: {str(e)}")
            raise ValueError(f"Formatting failed: {str(e)}") from e
    
    def set_accessibility_settings(self, settings: AccessibilitySettings) -> None:
        """Update accessibility settings."""
        self.accessibility_settings = settings
    
    def set_visual_hierarchy(self, hierarchy: VisualHierarchy) -> None:
        """Update visual hierarchy configuration."""
        self.visual_hierarchy = hierarchy
    
    def set_print_settings(self, settings: PrintSettings) -> None:
        """Update print settings."""
        self.print_settings = settings
    
    def set_formatting_preferences(self, preferences: FormattingPreferences) -> None:
        """Update formatting preferences."""
        self.formatting_preferences = preferences
    
    def set_patient_age_group(self, age_group: Union[str, PatientAgeGroup]) -> None:
        """Set patient age group for age-appropriate formatting."""
        if isinstance(age_group, str):
            age_group = PatientAgeGroup(age_group.lower())
        self.formatting_preferences.patient_age_group = age_group
    
    def set_locale(self, locale: Union[str, LanguageCode]) -> None:
        """Set locale for formatting."""
        if isinstance(locale, str):
            locale = LanguageCode(locale)
        self.formatting_preferences.language = locale
    
    def extract_text_content(self, html_content: str) -> str:
        """
        Extract plain text content from HTML for analysis.
        
        Args:
            html_content: HTML content to extract text from
            
        Returns:
            Plain text content without HTML tags
        """
        # Remove HTML tags
        text_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        text_content = html.unescape(text_content)
        
        # Clean up whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return text_content
    
    def _validate_clinical_summary(self, clinical_summary: ClinicalSummary) -> FormatterValidationResult:
        """
        Validate clinical summary before formatting.
        
        Args:
            clinical_summary: Clinical summary to validate
            
        Returns:
            FormatterValidationResult with validation status
        """
        validation_id = str(uuid.uuid4())
        errors = []
        warnings = []
        
        # Check required fields
        if not clinical_summary.summary_id:
            errors.append(FormatterError(
                error_id=str(uuid.uuid4()),
                error_type="missing_field",
                error_message="Clinical summary missing summary_id",
                severity="error"
            ))
        
        if not clinical_summary.patient_id:
            errors.append(FormatterError(
                error_id=str(uuid.uuid4()),
                error_type="missing_field", 
                error_message="Clinical summary missing patient_id",
                severity="error"
            ))
        
        # Check safety validation
        if not clinical_summary.safety_validation.passed:
            errors.append(FormatterError(
                error_id=str(uuid.uuid4()),
                error_type="safety_validation",
                error_message="Clinical summary failed safety validation",
                severity="critical"
            ))
        
        # Warn if no content to format
        if (not clinical_summary.medications and 
            not clinical_summary.lab_results and 
            not clinical_summary.appointments):
            warnings.append(FormatterError(
                error_id=str(uuid.uuid4()),
                error_type="empty_content",
                error_message="Clinical summary contains no clinical data to format",
                severity="warning"
            ))
        
        return FormatterValidationResult(
            validation_id=validation_id,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            safety_requirements_met=clinical_summary.safety_validation.passed,
            content_integrity_verified=len(errors) == 0
        )
    
    def _extract_content_sections(self, clinical_summary: ClinicalSummary) -> List[ContentSection]:
        """
        Extract and organize content into sections.
        
        Args:
            clinical_summary: Clinical summary to extract from
            
        Returns:
            List of ContentSection objects
        """
        sections = []
        
        # Emergency contact section (always first and critical)
        emergency_section = ContentSection(
            section_id="emergency_contact",
            section_type="emergency",
            title="In Case of Emergency",
            content="Call 911 or go to the nearest emergency room immediately",
            priority=1,
            critical=True,
            print_friendly=True
        )
        sections.append(emergency_section)
        
        # Medications section
        if clinical_summary.medications:
            med_content = self._format_medications_section(clinical_summary.medications)
            sections.append(ContentSection(
                section_id="medications",
                section_type="medication",
                title="Your Medications",
                content=med_content,
                priority=2,
                critical=True,
                print_friendly=True
            ))
        
        # Next appointment section
        if clinical_summary.appointments:
            # Find the next appointment (assume sorted)
            next_appointment = clinical_summary.appointments[0]
            appt_content = self._format_next_appointment_section(next_appointment)
            sections.append(ContentSection(
                section_id="next_appointment",
                section_type="appointment",
                title="Your Next Appointment",
                content=appt_content,
                priority=3,
                critical=True,
                print_friendly=True
            ))
        
        # Lab results section
        if clinical_summary.lab_results:
            lab_content = self._format_lab_results_section(clinical_summary.lab_results)
            sections.append(ContentSection(
                section_id="lab_results",
                section_type="lab",
                title="Your Test Results",
                content=lab_content,
                priority=4,
                critical=False,
                print_friendly=True
            ))
        
        # Care instructions section
        if clinical_summary.care_instructions:
            care_content = self._format_care_instructions_section(clinical_summary.care_instructions)
            sections.append(ContentSection(
                section_id="care_instructions",
                section_type="instructions",
                title="Important Care Instructions",
                content=care_content,
                priority=5,
                critical=False,
                print_friendly=True
            ))
        
        # Follow-up guidance section
        if clinical_summary.follow_up_guidance:
            followup_content = self._format_followup_section(clinical_summary.follow_up_guidance)
            sections.append(ContentSection(
                section_id="follow_up",
                section_type="guidance",
                title="Follow-up Information",
                content=followup_content,
                priority=6,
                critical=False,
                print_friendly=True
            ))
        
        # Disclaimers section (always last)
        disclaimer_content = self._format_disclaimers_section(clinical_summary.disclaimers)
        sections.append(ContentSection(
            section_id="disclaimers",
            section_type="legal",
            title="Important Information",
            content=disclaimer_content,
            priority=99,
            critical=True,
            print_friendly=True
        ))
        
        return sections
    
    def _format_medications_section(self, medications: List[MedicationSummary]) -> str:
        """Format medications into a readable section."""
        if not medications:
            return ""
        
        formatted_meds = []
        for med in medications:
            med_text = f"""
            <div class="medication-item">
                <h4 class="medication-name">{html.escape(med.medication_name)}</h4>
                <p class="medication-details">
                    <strong>Dose:</strong> {html.escape(med.dosage)}<br>
                    <strong>How often:</strong> {html.escape(med.frequency)}<br>
                    <strong>How to take:</strong> {html.escape(med.route)}<br>
                    <strong>Instructions:</strong> {html.escape(med.instructions)}
                </p>
            """
            
            if med.purpose:
                med_text += f'<p class="medication-purpose"><strong>Why you\'re taking this:</strong> {html.escape(med.purpose)}</p>'
            
            if med.important_notes:
                med_text += f'<p class="medication-notes"><strong>Important:</strong> {html.escape(med.important_notes)}</p>'
            
            med_text += "</div>"
            formatted_meds.append(med_text)
        
        return "\n".join(formatted_meds)
    
    def _format_next_appointment_section(self, appointment: AppointmentSummary) -> str:
        """Format next appointment into a readable section."""
        appt_text = f"""
        <div class="appointment-item">
            <p class="appointment-datetime">
                <strong>Date:</strong> {html.escape(appointment.date)}<br>
                <strong>Time:</strong> {html.escape(appointment.time)}
            </p>
            <p class="appointment-provider">
                <strong>Provider:</strong> {html.escape(appointment.provider)}
            </p>
            <p class="appointment-location">
                <strong>Location:</strong> {html.escape(appointment.location)}
            </p>
        """
        
        if appointment.phone:
            appt_text += f'<p class="appointment-phone"><strong>Phone:</strong> {html.escape(appointment.phone)}</p>'
        
        if appointment.purpose:
            appt_text += f'<p class="appointment-purpose"><strong>Purpose:</strong> {html.escape(appointment.purpose)}</p>'
        
        if appointment.preparation:
            appt_text += f'<p class="appointment-prep"><strong>What to bring:</strong> {html.escape(appointment.preparation)}</p>'
        
        appt_text += "</div>"
        return appt_text
    
    def _format_lab_results_section(self, lab_results: List[LabResultSummary]) -> str:
        """Format lab results into a readable section."""
        if not lab_results:
            return ""
        
        formatted_labs = []
        for lab in lab_results:
            lab_text = f"""
            <div class="lab-item">
                <h4 class="lab-name">{html.escape(lab.test_name)}</h4>
                <p class="lab-value">
                    <strong>Your result:</strong> {html.escape(lab.value)}
                """
            
            if lab.reference_range:
                lab_text += f'<br><strong>Normal range:</strong> {html.escape(lab.reference_range)}'
            
            lab_text += f'<br><strong>Status:</strong> {html.escape(lab.status)}</p>'
            
            if lab.explanation:
                lab_text += f'<p class="lab-explanation">{html.escape(lab.explanation)}</p>'
            
            lab_text += "</div>"
            formatted_labs.append(lab_text)
        
        return "\n".join(formatted_labs)
    
    def _format_care_instructions_section(self, instructions: str) -> str:
        """Format care instructions into a readable section."""
        return f'<div class="care-instructions">{html.escape(instructions)}</div>'
    
    def _format_followup_section(self, guidance: str) -> str:
        """Format follow-up guidance into a readable section."""
        return f'<div class="followup-guidance">{html.escape(guidance)}</div>'
    
    def _format_disclaimers_section(self, disclaimers: List[str]) -> str:
        """Format disclaimers into a readable section."""
        if not disclaimers:
            return ""
        
        formatted_disclaimers = []
        for disclaimer in disclaimers:
            formatted_disclaimers.append(f'<p class="disclaimer">{html.escape(disclaimer)}</p>')
        
        return "\n".join(formatted_disclaimers)
    
    def _apply_visual_hierarchy(self, sections: List[ContentSection]) -> List[ContentSection]:
        """Apply visual hierarchy to content sections."""
        # Sort by priority (lower number = higher priority)
        return sorted(sections, key=lambda x: x.priority)
    
    def _format_to_html(self, clinical_summary: ClinicalSummary, sections: List[ContentSection]) -> FormattedOutput:
        """Format clinical summary to HTML."""
        try:
            # Try to use template if available
            template = self.jinja_env.get_template('patient_summary.html')
        except:
            # Use fallback template
            template = self._get_fallback_html_template()
        
        # Prepare template context
        context = {
            'summary': clinical_summary,
            'sections': sections,
            'accessibility_settings': self.accessibility_settings,
            'visual_hierarchy': self.visual_hierarchy,
            'print_settings': self.print_settings,
            'formatting_preferences': self.formatting_preferences,
            'generated_at': datetime.utcnow(),
            'formatter_version': self.formatter_version
        }
        
        # Render HTML
        html_content = template.render(**context)
        
        return FormattedOutput(
            format=OutputFormat.HTML,
            content=html_content,
            content_type="text/html; charset=utf-8",
            accessibility_compliant=True,
            mobile_responsive=True,
            print_friendly=True,
            accessibility_settings=self.accessibility_settings,
            visual_hierarchy=self.visual_hierarchy,
            print_settings=self.print_settings,
            formatting_preferences=self.formatting_preferences
        )
    
    def _format_to_pdf(self, clinical_summary: ClinicalSummary, sections: List[ContentSection]) -> FormattedOutput:
        """Format clinical summary to PDF."""
        if not PDF_AVAILABLE or not self.pdf_generator:
            # Fallback to placeholder if PDF generation not available
            pdf_content = b'%PDF-1.4\n%Placeholder PDF content - WeasyPrint not available\n'
            
            return FormattedOutput(
                format=OutputFormat.PDF,
                content=pdf_content,
                content_type="application/pdf",
                accessibility_compliant=False,
                mobile_responsive=False,
                print_friendly=True,
                accessibility_settings=self.accessibility_settings,
                visual_hierarchy=self.visual_hierarchy,
                print_settings=self.print_settings,
                formatting_preferences=self.formatting_preferences
            )
        
        try:
            # Generate HTML first
            html_output = self._format_to_html(clinical_summary, sections)
            
            # Create PDF-specific CSS for better print formatting
            pdf_css = CSS(string="""
                @page {
                    size: letter;
                    margin: 0.5in;
                    @top-center {
                        content: "Patient Health Summary";
                        font-family: Arial, sans-serif;
                        font-size: 12pt;
                        color: #666;
                    }
                    @bottom-right {
                        content: "Page " counter(page) " of " counter(pages);
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                        color: #666;
                    }
                }
                
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.4;
                    color: #000;
                }
                
                .section {
                    break-inside: avoid;
                    margin-bottom: 1rem;
                    border: 2px solid #000;
                    padding: 1rem;
                }
                
                .emergency-section {
                    border: 4px solid #000;
                    background: #f5f5f5;
                    text-align: center;
                    font-weight: bold;
                }
                
                .section-title {
                    font-size: 16pt;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                    color: #000;
                }
                
                .medication-item,
                .appointment-item,
                .lab-item {
                    border: 1px solid #666;
                    padding: 0.5rem;
                    margin-bottom: 0.5rem;
                    background: #fafafa;
                }
                
                .critical-info {
                    background: #f0f0f0;
                    border: 2px solid #000;
                    padding: 0.25rem 0.5rem;
                    font-weight: bold;
                }
            """, font_config=self.font_config)
            
            # Generate PDF from HTML
            html_doc = HTML(string=html_output.content, base_url=".")
            pdf_content = html_doc.write_pdf(stylesheets=[pdf_css], font_config=self.font_config)
            
            return FormattedOutput(
                format=OutputFormat.PDF,
                content=pdf_content,
                content_type="application/pdf",
                accessibility_compliant=False,  # PDF accessibility would need additional work
                mobile_responsive=False,
                print_friendly=True,
                accessibility_settings=self.accessibility_settings,
                visual_hierarchy=self.visual_hierarchy,
                print_settings=self.print_settings,
                formatting_preferences=self.formatting_preferences
            )
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            # Fallback to placeholder on error
            pdf_content = b'%PDF-1.4\n%PDF generation failed - see logs for details\n'
            
            return FormattedOutput(
                format=OutputFormat.PDF,
                content=pdf_content,
                content_type="application/pdf",
                accessibility_compliant=False,
                mobile_responsive=False,
                print_friendly=True,
                accessibility_settings=self.accessibility_settings,
                visual_hierarchy=self.visual_hierarchy,
                print_settings=self.print_settings,
                formatting_preferences=self.formatting_preferences
            )
    
    def _format_to_plain_text(self, clinical_summary: ClinicalSummary, sections: List[ContentSection]) -> FormattedOutput:
        """Format clinical summary to plain text."""
        text_lines = []
        
        # Add header
        text_lines.append("PATIENT HEALTH SUMMARY")
        text_lines.append("=" * 50)
        text_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        text_lines.append("")
        
        # Add each section
        for section in sections:
            text_lines.append(section.title.upper())
            text_lines.append("-" * len(section.title))
            
            # Extract text content from HTML
            text_content = self.extract_text_content(section.content)
            text_lines.append(text_content)
            text_lines.append("")
        
        # Join all lines
        plain_text = "\n".join(text_lines)
        
        return FormattedOutput(
            format=OutputFormat.PLAIN_TEXT,
            content=plain_text,
            content_type="text/plain; charset=utf-8",
            accessibility_compliant=True,
            mobile_responsive=True,  # Plain text is always mobile-friendly
            print_friendly=True,
            accessibility_settings=self.accessibility_settings,
            visual_hierarchy=self.visual_hierarchy,
            print_settings=self.print_settings,
            formatting_preferences=self.formatting_preferences
        )
    
    def _format_to_json(self, clinical_summary: ClinicalSummary, sections: List[ContentSection]) -> FormattedOutput:
        """Format clinical summary to JSON."""
        import json
        
        # Create JSON structure
        json_data = {
            "summary_id": clinical_summary.summary_id,
            "patient_id": clinical_summary.patient_id,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": [
                {
                    "section_id": section.section_id,
                    "section_type": section.section_type,
                    "title": section.title,
                    "content": self.extract_text_content(section.content),
                    "priority": section.priority,
                    "critical": section.critical
                }
                for section in sections
            ],
            "formatter_version": self.formatter_version
        }
        
        json_content = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        return FormattedOutput(
            format=OutputFormat.JSON,
            content=json_content,
            content_type="application/json; charset=utf-8",
            accessibility_compliant=True,
            mobile_responsive=True,
            print_friendly=False,  # JSON not meant for printing
            accessibility_settings=self.accessibility_settings,
            visual_hierarchy=self.visual_hierarchy,
            print_settings=self.print_settings,
            formatting_preferences=self.formatting_preferences
        )
    
    def _validate_formatted_output(self, formatted_output: FormattedOutput, 
                                 clinical_summary: ClinicalSummary) -> FormatterValidationResult:
        """Validate the formatted output meets requirements."""
        validation_id = str(uuid.uuid4())
        errors = []
        warnings = []
        
        # Check content exists
        if not formatted_output.content:
            errors.append(FormatterError(
                error_id=str(uuid.uuid4()),
                error_type="empty_content",
                error_message="Formatted output is empty",
                severity="error"
            ))
        
        # Check critical information is present (for non-JSON formats)
        if formatted_output.format != OutputFormat.JSON:
            content_str = str(formatted_output.content)
            
            # Check medications are preserved
            for med in clinical_summary.medications:
                if med.medication_name not in content_str:
                    errors.append(FormatterError(
                        error_id=str(uuid.uuid4()),
                        error_type="missing_content",
                        error_message=f"Medication {med.medication_name} not found in output",
                        severity="critical"
                    ))
        
        return FormatterValidationResult(
            validation_id=validation_id,
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            content_integrity_verified=len(errors) == 0,
            accessibility_compliant=formatted_output.accessibility_compliant,
            safety_requirements_met=len([e for e in errors if e.severity == "critical"]) == 0
        )
    
    def _apply_custom_settings(self, custom_settings: Dict[str, Any]) -> None:
        """Apply custom settings for this formatting operation."""
        # This is a placeholder for custom settings application
        # In a full implementation, this would override current settings
        pass
    
    def _initialize_fallback_templates(self) -> None:
        """Initialize fallback templates if package templates can't be loaded."""
        # This will be implemented when creating the template files
        pass
    
    def _add_template_filters(self) -> None:
        """Add custom filters and functions to Jinja2 environment."""
        
        def format_date(date_str: str, format_style: str = "readable") -> str:
            """Format date string for display."""
            try:
                if format_style == "readable":
                    # Convert YYYY-MM-DD to more readable format
                    parts = date_str.split("-")
                    if len(parts) == 3:
                        return f"{parts[1]}/{parts[2]}/{parts[0]}"
                return date_str
            except:
                return date_str
        
        def emphasize_critical(text: str, is_critical: bool = False) -> str:
            """Add emphasis styling to critical information."""
            if is_critical:
                return f'<span class="critical-info">{html.escape(text)}</span>'
            return html.escape(text)
        
        # Add filters to Jinja2 environment
        self.jinja_env.filters['format_date'] = format_date
        self.jinja_env.filters['emphasize_critical'] = emphasize_critical
    
    def _get_fallback_html_template(self) -> Template:
        """Get fallback HTML template if package templates aren't available."""
        fallback_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Health Summary</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .critical-info { color: #d9534f; font-weight: bold; }
        .medication-item, .lab-item, .appointment-item { margin-bottom: 15px; }
        h1, h2, h3, h4 { color: #337ab7; }
        @media print { body { margin: 0; } .section { break-inside: avoid; } }
        @media (max-width: 600px) { .container { margin: 10px; } .section { padding: 10px; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Health Summary</h1>
        {% for section in sections %}
        <div class="section">
            <h2>{{ section.title }}</h2>
            {{ section.content|safe }}
        </div>
        {% endfor %}
        <p class="disclaimer">Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M UTC') }}</p>
    </div>
</body>
</html>
        """
        return Template(fallback_html)