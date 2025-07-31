"""
Clinical data summarizer package.

This package contains the core processing logic for transforming clinical data
into patient-friendly summaries while maintaining strict safety standards.
"""

from .fhir_parser import FHIRMedicationParser
from .hybrid_processor import HybridClinicalProcessor

__all__ = [
    "FHIRMedicationParser",
    "HybridClinicalProcessor"
]