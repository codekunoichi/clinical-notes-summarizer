"""
Translation Services for Clinical Notes Summarizer

This module provides multilingual translation capabilities for patient-friendly
clinical summaries with healthcare-specific safety guarantees.

Key Principles:
1. NEVER translate critical medical data (medications, dosages, lab values)
2. ONLY translate narrative sections for patient comprehension  
3. Maintain medical accuracy and cultural appropriateness
4. Ensure HIPAA compliance with PHI protection
"""

from .fridge_magnet_translator import FridgeMagnetTranslator

__all__ = [
    "FridgeMagnetTranslator",
]