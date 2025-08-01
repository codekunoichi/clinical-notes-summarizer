"""
Pydantic models for patient-friendly output formatter.

These models define the structure and validation for different output formats,
accessibility settings, and visual hierarchy configurations.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats for patient-friendly summaries."""
    HTML = "html"
    PDF = "pdf"
    PLAIN_TEXT = "plain_text"
    JSON = "json"  # For API responses


class AccessibilityLevel(str, Enum):
    """WCAG accessibility compliance levels."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class PatientAgeGroup(str, Enum):
    """Patient age group for targeted formatting."""
    PEDIATRIC = "pediatric"  # 0-17 years
    ADULT = "adult"         # 18-64 years  
    GERIATRIC = "geriatric" # 65+ years


class LanguageCode(str, Enum):
    """Supported language codes (ISO 639-1)."""
    EN_US = "en-US"
    EN_GB = "en-GB" 
    ES_US = "es-US"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    # Add more as needed


class AccessibilitySettings(BaseModel):
    """
    Accessibility settings for WCAG compliance and enhanced usability.
    
    These settings ensure the output meets healthcare accessibility standards.
    """
    wcag_level: AccessibilityLevel = Field(AccessibilityLevel.AA, description="WCAG compliance level")
    high_contrast: bool = Field(False, description="Enable high contrast color scheme")
    large_fonts: bool = Field(False, description="Use larger font sizes throughout")
    screen_reader_optimized: bool = Field(True, description="Optimize for screen readers")
    keyboard_navigation: bool = Field(True, description="Support keyboard-only navigation")
    aria_labels: bool = Field(True, description="Include comprehensive ARIA labels")
    alt_text_images: bool = Field(True, description="Provide alt text for all images")
    color_blind_friendly: bool = Field(True, description="Use colorblind-friendly color palette")
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )


class VisualHierarchy(BaseModel):
    """
    Configuration for visual hierarchy to emphasize important information.
    
    This ensures critical medical information is prominently displayed.
    """
    primary_sections: List[str] = Field(
        default=["emergency_contact", "medications", "next_appointment"],
        description="Top priority sections displayed first"
    )
    secondary_sections: List[str] = Field(
        default=["lab_results", "care_instructions"],
        description="Important but secondary information"
    )
    emphasis_elements: List[str] = Field(
        default=["critical_alerts", "emergency_contact", "urgent_instructions"],
        description="Elements requiring visual emphasis"
    )
    fold_priority: List[str] = Field(
        default=["medications", "emergency_contact", "next_appointment"],
        description="Information that must be visible above the fold"
    )
    
    @field_validator('primary_sections', 'secondary_sections', 'emphasis_elements', 'fold_priority')
    @classmethod
    def validate_non_empty(cls, v):
        """Ensure section lists are not empty."""
        if not v:
            raise ValueError("Section lists cannot be empty")
        return v


class PrintSettings(BaseModel):
    """
    Settings for print-friendly formatting (fridge magnet concept).
    
    These settings optimize the output for physical printing and posting.
    """
    page_size: str = Field("letter", description="Page size for printing (letter, a4, etc.)")
    margins: Dict[str, str] = Field(
        default={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
        description="Page margins for printing"
    )
    font_size_base: str = Field("12pt", description="Base font size for printed output")
    font_size_headers: str = Field("16pt", description="Header font size for printed output")
    line_height: str = Field("1.4", description="Line height for readability")
    print_background: bool = Field(False, description="Include background colors/images in print")
    page_breaks: bool = Field(True, description="Allow page breaks between major sections")
    header_footer: bool = Field(True, description="Include page headers and footers")
    
    @field_validator('font_size_base', 'font_size_headers')
    @classmethod
    def validate_font_size(cls, v):
        """Validate font size format."""
        if not (v.endswith('pt') or v.endswith('px') or v.endswith('em')):
            raise ValueError("Font size must include units (pt, px, em)")
        return v


class FormattingPreferences(BaseModel):
    """
    User preferences for output formatting.
    
    These preferences allow customization while maintaining safety standards.
    """
    patient_age_group: PatientAgeGroup = Field(PatientAgeGroup.ADULT, description="Patient age group")
    language: LanguageCode = Field(LanguageCode.EN_US, description="Output language")
    simplified_language: bool = Field(True, description="Use simplified medical language")
    include_icons: bool = Field(True, description="Include helpful icons and symbols")
    color_coding: bool = Field(True, description="Use color coding for different types of information")
    compact_layout: bool = Field(False, description="Use more compact layout to save space")
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )


class ContentSection(BaseModel):
    """
    Individual content section with metadata.
    
    Represents a formatted section of the clinical summary.
    """
    section_id: str = Field(..., description="Unique identifier for this section")
    section_type: str = Field(..., description="Type of section (medication, appointment, etc.)")
    title: str = Field(..., description="Human-readable section title")
    content: str = Field(..., description="Formatted section content")
    priority: int = Field(1, description="Display priority (1=highest)")
    critical: bool = Field(False, description="Whether this section contains critical information")
    print_friendly: bool = Field(True, description="Whether this section is suitable for printing")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority is positive integer."""
        if v < 1:
            raise ValueError("Priority must be 1 or greater")
        return v


class FormattedOutput(BaseModel):
    """
    Complete formatted output with metadata and compliance information.
    
    This is the main output model containing the formatted patient-friendly summary.
    """
    format: OutputFormat = Field(..., description="Output format type")
    content: Union[str, bytes] = Field(..., description="Formatted content")
    content_type: str = Field(..., description="MIME type of the content")
    
    # Structure and sections
    sections: List[ContentSection] = Field(default_factory=list, description="Individual content sections")
    
    # Compliance and quality flags
    accessibility_compliant: bool = Field(True, description="Meets accessibility requirements")
    mobile_responsive: bool = Field(True, description="Optimized for mobile devices")
    print_friendly: bool = Field(True, description="Optimized for printing")
    safety_validated: bool = Field(True, description="Passed safety validation checks")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When output was generated")
    generator_version: str = Field("1.0.0", description="Version of formatter used")
    locale: str = Field("en-US", description="Locale used for formatting")
    
    # Settings used for generation
    accessibility_settings: AccessibilitySettings = Field(default_factory=AccessibilitySettings)
    visual_hierarchy: VisualHierarchy = Field(default_factory=VisualHierarchy)
    print_settings: PrintSettings = Field(default_factory=PrintSettings)
    formatting_preferences: FormattingPreferences = Field(default_factory=FormattingPreferences)
    
    # Quality metrics
    content_length: int = Field(0, description="Content length in characters")
    estimated_reading_time: int = Field(0, description="Estimated reading time in seconds")
    readability_score: Optional[float] = Field(None, description="Readability score (0-100)")
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v, info):
        """Validate content type matches format."""
        format_type = info.data.get('format') if info.data else None
        
        if format_type == OutputFormat.HTML and not v.startswith('text/html'):
            raise ValueError("HTML format must have text/html content type")
        elif format_type == OutputFormat.PDF and v != 'application/pdf':
            raise ValueError("PDF format must have application/pdf content type")
        elif format_type == OutputFormat.PLAIN_TEXT and not v.startswith('text/plain'):
            raise ValueError("Plain text format must have text/plain content type")
        elif format_type == OutputFormat.JSON and not v.startswith('application/json'):
            raise ValueError("JSON format must have application/json content type")
        
        return v
    
    @field_validator('content_length')
    @classmethod
    def calculate_content_length(cls, v, info):
        """Calculate content length from content."""
        content = info.data.get('content') if info.data else None
        if content:
            if isinstance(content, str):
                return len(content)
            elif isinstance(content, bytes):
                return len(content)
        return v
    
    @field_validator('estimated_reading_time')
    @classmethod
    def calculate_reading_time(cls, v, info):
        """Calculate estimated reading time (assumes 200 words per minute)."""
        content = info.data.get('content') if info.data else None
        if content and isinstance(content, str):
            # Rough estimate: 200 words per minute, average 5 characters per word
            word_count = len(content) / 5
            return int((word_count / 200) * 60)  # Convert to seconds
        return v
    
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )


class FormatterError(BaseModel):
    """
    Error information for formatter failures.
    
    Used to track and report formatting errors with context.
    """
    error_id: str = Field(..., description="Unique identifier for this error")
    error_type: str = Field(..., description="Type of error (validation, processing, etc.)")
    error_message: str = Field(..., description="Human-readable error message")
    section_affected: Optional[str] = Field(None, description="Section where error occurred")
    severity: str = Field("error", description="Error severity (warning, error, critical)")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="When error occurred")
    
    # Context information
    input_data_type: Optional[str] = Field(None, description="Type of input data being processed")
    output_format: Optional[OutputFormat] = Field(None, description="Target output format")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        """Validate error severity level."""
        valid_severities = ['warning', 'error', 'critical']
        if v not in valid_severities:
            raise ValueError(f"Severity must be one of: {valid_severities}")
        return v


class FormatterValidationResult(BaseModel):
    """
    Results of formatter validation checks.
    
    Used to ensure output meets all safety and quality requirements.
    """
    validation_id: str = Field(..., description="Unique identifier for this validation")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation occurred")
    
    # Overall results
    passed: bool = Field(..., description="Whether validation passed overall")
    errors: List[FormatterError] = Field(default_factory=list, description="Validation errors")
    warnings: List[FormatterError] = Field(default_factory=list, description="Validation warnings")
    
    # Specific validation checks
    accessibility_compliant: bool = Field(True, description="Meets accessibility requirements")
    safety_requirements_met: bool = Field(True, description="Meets healthcare safety requirements")
    content_integrity_verified: bool = Field(True, description="Critical content preserved accurately")
    print_quality_acceptable: bool = Field(True, description="Print quality meets standards")
    mobile_compatibility_verified: bool = Field(True, description="Mobile compatibility verified")
    
    # Quality metrics
    readability_acceptable: bool = Field(True, description="Content readability meets standards")
    content_completeness: float = Field(1.0, description="Percentage of original content preserved")
    
    @field_validator('passed')
    @classmethod
    def validate_no_errors_if_passed(cls, v, info):
        """Ensure validation cannot pass if there are errors."""
        errors = info.data.get('errors', []) if info.data else []
        if v and errors:
            raise ValueError("Validation cannot pass if there are errors")
        return v
    
    @field_validator('content_completeness')
    @classmethod
    def validate_completeness_range(cls, v):
        """Validate completeness is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Content completeness must be between 0 and 1")
        return v