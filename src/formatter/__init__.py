"""
Patient-friendly output formatter package.

This package provides functionality to format clinical summaries into
patient-friendly "fridge magnet" format with multiple output options.
"""

from .patient_friendly import PatientFriendlyFormatter, FormattedOutput, OutputFormat
from .models import AccessibilitySettings, VisualHierarchy, PrintSettings

__all__ = [
    "PatientFriendlyFormatter",
    "FormattedOutput", 
    "OutputFormat",
    "AccessibilitySettings",
    "VisualHierarchy",
    "PrintSettings"
]