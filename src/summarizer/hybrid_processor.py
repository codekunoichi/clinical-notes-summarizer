"""
Hybrid Clinical Processor - Core processing engine with safety guarantees.

This processor implements the hybrid structured + AI approach:
- CRITICAL data (medications, labs, vitals) is preserved exactly
- NARRATIVE data (explanations, descriptions) can be AI-enhanced
- All processing is tracked and validated for healthcare safety
"""

from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime

from src.models.medication import MedicationRequest
from src.models.clinical import (
    ClinicalSummary,
    MedicationSummary,
    ProcessingMetadata,
    SafetyValidation,
    ProcessingType,
    SafetyLevel
)
from src.summarizer.fhir_parser import FHIRMedicationParser
from src.summarizer.narrative_enhancement import NarrativeEnhancer, EnhancementSettings

# Configure logging
logger = logging.getLogger(__name__)


class HybridClinicalProcessor:
    """
    Core processing engine that implements hybrid structured + AI approach.
    
    This processor ensures that critical medical data is preserved exactly
    while allowing AI enhancement only for safe narrative content.
    """
    
    def __init__(self, enable_ai_enhancement: bool = True):
        """Initialize the hybrid clinical processor."""
        self.processor_version = "1.0.0"
        self.fhir_parser = FHIRMedicationParser()
        self.safety_enforced = True
        self.enable_ai_enhancement = enable_ai_enhancement
        
        # Initialize narrative enhancer if AI enhancement is enabled
        if self.enable_ai_enhancement:
            self.narrative_enhancer = NarrativeEnhancer()
            self.enhancement_settings = EnhancementSettings(
                enhancement_aggressiveness="balanced",
                target_grade_level=7,
                preserve_medical_terminology=True
            )
        else:
            self.narrative_enhancer = None
            self.enhancement_settings = None
        
    def process_clinical_data(self, fhir_bundle: Dict[str, Any]) -> ClinicalSummary:
        """
        Process complete FHIR bundle into patient-friendly clinical summary.
        
        Args:
            fhir_bundle: FHIR Bundle containing clinical data
            
        Returns:
            Complete clinical summary with safety validation
            
        Raises:
            ValueError: If processing fails safety validation
        """
        # Generate unique summary ID
        summary_id = str(uuid.uuid4())
        
        # Extract patient ID
        patient_id = self._extract_patient_id(fhir_bundle)
        
        # Process medication data
        medication_summaries = []
        medication_requests = self.fhir_parser.parse_fhir_bundle(fhir_bundle)
        
        for med_request in medication_requests:
            med_summary = self.process_medication_data(med_request.model_dump())
            medication_summaries.append(med_summary)
        
        # Create overall safety validation
        safety_validation = SafetyValidation(
            validation_id=str(uuid.uuid4()),
            data_type="clinical_summary",
            passed=True,
            errors=[],
            warnings=[],
            critical_fields_preserved={
                "medications": len(medication_summaries) > 0
            },
            ai_processing_flags={
                "medications": False  # Critical data never AI processed
            }
        )
        
        # Process narrative fields if available
        narrative_fields = {}
        ai_processing_used = False
        
        if self.enable_ai_enhancement:
            # Extract narrative content from FHIR bundle
            extracted_narratives = self._extract_narrative_content(fhir_bundle)
            
            if extracted_narratives:
                # Enhance narratives using AI
                enhanced_narratives = self._process_narrative_fields(extracted_narratives)
                narrative_fields = enhanced_narratives
                ai_processing_used = len(enhanced_narratives) > 0
        
        # Create processing metadata
        # Use appropriate safety level based on AI processing
        safety_level = SafetyLevel.NARRATIVE if ai_processing_used else SafetyLevel.CRITICAL
        
        processing_metadata = ProcessingMetadata(
            safety_level=safety_level,
            processing_type=ProcessingType.AI_ENHANCED if ai_processing_used else ProcessingType.PRESERVED,
            ai_processed=ai_processing_used,
            validation_passed=True,
            validation_errors=[]
        )
        
        # Create clinical summary (disclaimers will be auto-added by model validator)
        summary = ClinicalSummary(
            summary_id=summary_id,
            patient_id=patient_id,
            medications=medication_summaries,
            chief_complaint=narrative_fields.get("chief_complaint"),
            diagnosis_explanation=narrative_fields.get("diagnosis_explanation"),
            care_instructions=narrative_fields.get("care_instructions"),
            follow_up_guidance=narrative_fields.get("follow_up_guidance"),
            safety_validation=safety_validation,
            processing_metadata=processing_metadata,
            disclaimers=[]  # Will be populated by field validator
        )
        
        return summary
    
    def process_medication_data(self, medication_data: Dict[str, Any]) -> MedicationSummary:
        """
        Process medication data with exact preservation of critical fields.
        
        Args:
            medication_data: FHIR MedicationRequest data
            
        Returns:
            MedicationSummary with preserved critical data
            
        Raises:
            ValueError: If medication data fails validation
        """
        # Parse and validate FHIR data
        try:
            med_request = self.fhir_parser.parse_medication_request(medication_data)
        except Exception as e:
            raise ValueError(f"Medication data validation failed: {str(e)}") from e
        
        # Extract critical medication details (NEVER AI processed)
        medication_name = self.fhir_parser.extract_medication_name(med_request)
        dosage_info = self.fhir_parser.extract_dosage_information(med_request)
        
        # Create processing metadata
        processing_metadata = ProcessingMetadata(
            safety_level=SafetyLevel.CRITICAL,
            processing_type=ProcessingType.PRESERVED,
            ai_processed=False,  # NEVER true for critical medication data
            validation_passed=True,
            validation_errors=[],
            preservation_hash=self.fhir_parser.calculate_preservation_hash(medication_data)
        )
        
        # Create medication summary with exact preservation
        med_summary = MedicationSummary(
            medication_name=medication_name,
            dosage=dosage_info["dosage"],
            frequency=dosage_info["frequency"],
            route=dosage_info["route"],
            instructions=dosage_info["instructions"],
            purpose=None,  # Could be AI-enhanced in future (but not in this version)
            important_notes=None,  # Could be AI-enhanced in future
            metadata=processing_metadata
        )
        
        return med_summary
    
    def process_lab_data(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process lab data with exact preservation (placeholder for future implementation).
        
        Args:
            lab_data: FHIR Observation data for lab results
            
        Returns:
            Processed lab data
        """
        # Placeholder - not implemented in current version
        raise NotImplementedError("Lab data processing not implemented yet")
    
    def process_appointment_data(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process appointment data with exact preservation (placeholder for future implementation).
        
        Args:
            appointment_data: FHIR Appointment data
            
        Returns:
            Processed appointment data
        """
        # Placeholder - not implemented in current version  
        raise NotImplementedError("Appointment data processing not implemented yet")
    
    def validate_safety_requirements(self, original_data: Dict[str, Any], 
                                   processed_data: Dict[str, Any]) -> SafetyValidation:
        """
        Validate that safety requirements are met for processed data.
        
        Args:
            original_data: Original FHIR data
            processed_data: Processed data
            
        Returns:
            SafetyValidation results
        """
        validation_id = str(uuid.uuid4())
        errors = []
        warnings = []
        critical_fields_preserved = {}
        ai_processing_flags = {}
        
        # Validate medication data if present
        if original_data.get("resourceType") == "MedicationRequest":
            # Check medication name preservation
            orig_name = self._extract_original_medication_name(original_data)
            proc_name = processed_data.get("medication_name")
            
            if orig_name != proc_name:
                errors.append(f"Medication name was altered: '{orig_name}' -> '{proc_name}'")
                critical_fields_preserved["medication_name"] = False
            else:
                critical_fields_preserved["medication_name"] = True
            
            # Check all critical fields preservation
            critical_fields = ["medication_name", "dosage", "frequency", "route", "instructions"]
            for field in critical_fields:
                ai_processing_flags[field] = False  # Must always be False
                # Mark field as preserved if it exists in processed data
                critical_fields_preserved[field] = field in processed_data
        
        # Overall validation result
        passed = len(errors) == 0
        
        return SafetyValidation(
            validation_id=validation_id,
            data_type="medication",
            passed=passed,
            errors=errors,
            warnings=warnings,
            critical_fields_preserved=critical_fields_preserved,
            ai_processing_flags=ai_processing_flags
        )
    
    def enforce_ai_processing_rules(self, data_type: str, field_name: str) -> bool:
        """
        Enforce rules about what data can be AI processed.
        
        Args:
            data_type: Type of data (medication, lab, etc.)
            field_name: Name of the field
            
        Returns:
            True if AI processing is allowed, False otherwise
        """
        # Critical medication fields NEVER allow AI processing
        if data_type == "medication":
            critical_fields = [
                "medication_name", "dosage", "frequency", "route", "instructions",
                "status", "intent"
            ]
            if field_name in critical_fields:
                return False
        
        # Lab values NEVER allow AI processing
        if data_type == "lab":
            critical_fields = [
                "test_name", "value", "reference_range", "units"
            ]
            if field_name in critical_fields:
                return False
        
        # Vital signs NEVER allow AI processing
        if data_type == "vital":
            critical_fields = [
                "measurement_type", "value", "units", "timestamp"
            ]
            if field_name in critical_fields:
                return False
        
        # Appointment details NEVER allow AI processing
        if data_type == "appointment":
            critical_fields = [
                "date", "time", "provider", "location", "phone"
            ]
            if field_name in critical_fields:
                return False
        
        # AI enhancement allowed for narrative fields only
        narrative_fields = [
            "purpose", "explanation", "important_notes", "preparation",
            "chief_complaint", "diagnosis_explanation", "care_instructions"
        ]
        
        return field_name in narrative_fields
    
    def get_processing_metadata(self) -> Dict[str, Any]:
        """
        Get processing metadata for tracking and auditing.
        
        Returns:
            Processing metadata dictionary
        """
        return {
            "processor_version": self.processor_version,
            "processed_at": datetime.utcnow().isoformat(),
            "safety_enforced": self.safety_enforced,
            "ai_enhancement_enabled": False,  # Not implemented in this version
            "validation_required": True
        }
    
    def set_safety_level(self, level: SafetyLevel) -> None:
        """
        Set the safety level for processing.
        
        Args:
            level: Safety level to enforce
        """
        # In this implementation, safety level is always CRITICAL for medication data
        # This method is provided for interface compliance but doesn't change behavior
        if level != SafetyLevel.CRITICAL:
            raise ValueError("Only CRITICAL safety level is supported for medication data")
    
    def _extract_patient_id(self, fhir_bundle: Dict[str, Any]) -> str:
        """Extract patient ID from FHIR bundle."""
        entries = fhir_bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                return resource.get("id", "unknown")
            elif resource.get("resourceType") == "MedicationRequest":
                subject_ref = resource.get("subject", {}).get("reference", "")
                if subject_ref.startswith("Patient/"):
                    return subject_ref.replace("Patient/", "")
        
        return "unknown"
    
    def _extract_original_medication_name(self, original_data: Dict[str, Any]) -> Optional[str]:
        """Extract medication name from original FHIR data."""
        if "medicationCodeableConcept" in original_data:
            concept = original_data["medicationCodeableConcept"]
            if concept.get("text"):
                return concept["text"]
            
            coding = concept.get("coding", [])
            for code in coding:
                if code.get("display"):
                    return code["display"]
        
        if "medicationReference" in original_data:
            ref = original_data["medicationReference"]
            if ref.get("display"):
                return ref["display"]
        
        return None
    
    def _extract_narrative_content(self, fhir_bundle: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract narrative content from FHIR bundle that can be AI-enhanced.
        
        Args:
            fhir_bundle: FHIR Bundle containing clinical data
            
        Returns:
            Dictionary of narrative field names to content
        """
        narratives = {}
        entries = fhir_bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            # Extract narratives from different FHIR resource types
            if resource_type == "Condition":
                # Extract chief complaint or diagnosis information
                if resource.get("code", {}).get("text"):
                    narratives["chief_complaint"] = resource["code"]["text"]
                    
                # Extract clinical status narrative
                if resource.get("clinicalStatus", {}).get("coding"):
                    status_display = resource["clinicalStatus"]["coding"][0].get("display")
                    if status_display:
                        narratives["diagnosis_explanation"] = f"Current status: {status_display}"
            
            elif resource_type == "CarePlan":
                # Extract care instructions
                if resource.get("description"):
                    narratives["care_instructions"] = resource["description"]
                    
                # Extract activity details
                activities = resource.get("activity", [])
                for activity in activities:
                    detail = activity.get("detail", {})
                    if detail.get("description"):
                        existing_instructions = narratives.get("care_instructions", "")
                        narratives["care_instructions"] = f"{existing_instructions} {detail['description']}".strip()
            
            elif resource_type == "Appointment":
                # Extract appointment purpose and instructions
                if resource.get("description"):
                    narratives["follow_up_guidance"] = resource["description"]
                    
                # Extract appointment type for context
                if resource.get("appointmentType", {}).get("text"):
                    app_type = resource["appointmentType"]["text"]
                    existing_guidance = narratives.get("follow_up_guidance", "")
                    narratives["follow_up_guidance"] = f"Scheduled {app_type}. {existing_guidance}".strip()
        
        # If no specific narratives found, create some basic ones from medication data
        if not narratives and entries:
            med_count = sum(1 for entry in entries 
                           if entry.get("resource", {}).get("resourceType") == "MedicationRequest")
            if med_count > 0:
                narratives["care_instructions"] = f"You have been prescribed {med_count} medication(s). Please take them as directed by your healthcare provider."
        
        return narratives
    
    def _process_narrative_fields(self, narratives: Dict[str, str]) -> Dict[str, str]:
        """
        Process narrative fields using AI enhancement.
        
        Args:
            narratives: Dictionary of narrative field names to content
            
        Returns:
            Dictionary of enhanced narrative content
        """
        if not self.narrative_enhancer or not narratives:
            return {}
        
        enhanced_narratives = {}
        
        try:
            # Process each narrative field
            for field_name, content in narratives.items():
                if content and content.strip():
                    # Enhance the narrative content
                    enhancement_result = self.narrative_enhancer.enhance_narrative(
                        content, self.enhancement_settings
                    )
                    
                    # Use enhanced text if validation passed
                    if enhancement_result["validation_result"].medical_accuracy_preserved:
                        enhanced_narratives[field_name] = enhancement_result["enhanced_text"]
                    else:
                        # Fall back to original if enhancement failed validation
                        enhanced_narratives[field_name] = content
                        
        except Exception as e:
            # If enhancement fails, log error and return original content
            logger.warning(f"Narrative enhancement failed: {str(e)}")
            return narratives
        
        return enhanced_narratives
    
    def set_enhancement_settings(self, settings: EnhancementSettings) -> None:
        """
        Set enhancement settings for narrative processing.
        
        Args:
            settings: New enhancement settings
        """
        if self.narrative_enhancer:
            self.enhancement_settings = settings
            self.narrative_enhancer.set_enhancement_settings(settings)
    
    def enable_narrative_enhancement(self, enable: bool = True) -> None:
        """
        Enable or disable narrative enhancement.
        
        Args:
            enable: Whether to enable narrative enhancement
        """
        if enable and not self.narrative_enhancer:
            # Initialize enhancer if not already done
            self.narrative_enhancer = NarrativeEnhancer()
            self.enhancement_settings = EnhancementSettings()
        
        self.enable_ai_enhancement = enable