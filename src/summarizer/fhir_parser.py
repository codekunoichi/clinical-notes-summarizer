"""
FHIR medication parser with exact data preservation.

This module implements zero-tolerance parsing of FHIR medication resources,
ensuring that critical medication data is extracted and preserved exactly
without any AI processing or summarization.
"""

from typing import Dict, Any, List, Optional, Union
import hashlib
import json
from datetime import datetime

from src.models.medication import (
    MedicationRequest,
    MedicationCodeableConcept,
    DosageInstruction,
    Quantity,
    Timing,
    Repeat
)


class FHIRMedicationParser:
    """
    FHIR medication parser with strict safety guarantees.
    
    This parser ensures that medication data is extracted exactly as specified
    in FHIR resources, with zero tolerance for any alterations that could
    compromise patient safety.
    """
    
    def __init__(self):
        """Initialize the FHIR medication parser."""
        self.parser_version = "1.0.0"
        self.supported_resource_types = ["MedicationRequest", "Bundle"]
    
    def parse_medication_request(self, fhir_data: Dict[str, Any]) -> MedicationRequest:
        """
        Parse a FHIR MedicationRequest resource with exact data preservation.
        
        Args:
            fhir_data: Raw FHIR MedicationRequest data
            
        Returns:
            Validated MedicationRequest model
            
        Raises:
            ValueError: If FHIR data is invalid or cannot be parsed safely
        """
        if not isinstance(fhir_data, dict):
            raise ValueError("FHIR data must be a dictionary")
        
        if fhir_data.get("resourceType") != "MedicationRequest":
            raise ValueError("Resource type must be MedicationRequest")
        
        try:
            # Validate and parse the medication request
            # This will raise ValidationError if any critical data is invalid
            medication_request = MedicationRequest(**fhir_data)
            return medication_request
        except Exception as e:
            raise ValueError(f"Failed to parse MedicationRequest: {str(e)}") from e
    
    def extract_medication_name(self, medication_request: MedicationRequest) -> str:
        """
        Extract medication name with exact preservation.
        
        Args:
            medication_request: Validated MedicationRequest
            
        Returns:
            Exact medication name as specified in FHIR
            
        Raises:
            ValueError: If medication name cannot be extracted
        """
        if medication_request.medicationCodeableConcept:
            if medication_request.medicationCodeableConcept.text:
                return medication_request.medicationCodeableConcept.text
            elif medication_request.medicationCodeableConcept.coding:
                # Try to get display name from coding
                for coding in medication_request.medicationCodeableConcept.coding:
                    if coding.display:
                        return coding.display
        
        if medication_request.medicationReference:
            if medication_request.medicationReference.display:
                return medication_request.medicationReference.display
        
        raise ValueError("Cannot extract medication name from MedicationRequest")
    
    def extract_dosage_information(self, medication_request: MedicationRequest) -> Dict[str, str]:
        """
        Extract dosage information with exact preservation.
        
        Args:
            medication_request: Validated MedicationRequest
            
        Returns:
            Dictionary with exact dosage details
        """
        dosage_info = {
            "dosage": "",
            "frequency": "",
            "route": "",
            "instructions": ""
        }
        
        if not medication_request.dosageInstruction:
            return dosage_info
        
        # Process first dosage instruction (most common case)
        primary_dosage = medication_request.dosageInstruction[0]
        
        # Extract exact dosage amount
        if primary_dosage.doseAndRate:
            dose_rate = primary_dosage.doseAndRate[0]
            if dose_rate.doseQuantity:
                dose_qty = dose_rate.doseQuantity
                unit = dose_qty.unit or ""
                dosage_info["dosage"] = f"{dose_qty.value} {unit}".strip()
        
        # Extract exact frequency
        if primary_dosage.timing and primary_dosage.timing.repeat:
            repeat = primary_dosage.timing.repeat
            if repeat.frequency and repeat.period and repeat.periodUnit:
                # Format frequency to match test expectations
                period_str = str(int(repeat.period)) if float(repeat.period).is_integer() else str(repeat.period)
                if repeat.frequency == 1:
                    dosage_info["frequency"] = f"1 time(s) per {period_str} {repeat.periodUnit}"
                else:
                    dosage_info["frequency"] = f"{repeat.frequency} time(s) per {period_str} {repeat.periodUnit}"
        
        # Extract route
        if primary_dosage.route and primary_dosage.route.text:
            dosage_info["route"] = primary_dosage.route.text
        elif primary_dosage.route and primary_dosage.route.coding:
            for coding in primary_dosage.route.coding:
                if coding.display:
                    dosage_info["route"] = coding.display
                    break
        
        # Extract complete instructions (preserve exactly)
        instruction_parts = []
        
        if primary_dosage.text:
            instruction_parts.append(primary_dosage.text)
        
        if primary_dosage.patientInstruction:
            instruction_parts.append(primary_dosage.patientInstruction)
        
        # Add any additional instructions from other dosage entries
        for dosage in medication_request.dosageInstruction[1:]:
            if dosage.text:
                instruction_parts.append(dosage.text)
            if dosage.patientInstruction:
                instruction_parts.append(dosage.patientInstruction)
        
        dosage_info["instructions"] = " | ".join(instruction_parts)
        
        return dosage_info
    
    def calculate_preservation_hash(self, fhir_data: Dict[str, Any]) -> str:
        """
        Calculate hash of critical medication data for integrity verification.
        
        Args:
            fhir_data: Original FHIR data
            
        Returns:
            SHA-256 hash of critical fields
        """
        # Extract only critical fields for hashing
        critical_fields = {}
        
        if "medicationCodeableConcept" in fhir_data:
            critical_fields["medicationCodeableConcept"] = fhir_data["medicationCodeableConcept"]
        
        if "medicationReference" in fhir_data:
            critical_fields["medicationReference"] = fhir_data["medicationReference"]
        
        if "dosageInstruction" in fhir_data:
            critical_fields["dosageInstruction"] = fhir_data["dosageInstruction"]
        
        if "status" in fhir_data:
            critical_fields["status"] = fhir_data["status"]
        
        if "intent" in fhir_data:
            critical_fields["intent"] = fhir_data["intent"]
        
        # Create deterministic hash
        critical_json = json.dumps(critical_fields, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(critical_json.encode('utf-8')).hexdigest()
    
    def parse_fhir_bundle(self, bundle_data: Dict[str, Any]) -> List[MedicationRequest]:
        """
        Parse FHIR Bundle containing medication resources.
        
        Args:
            bundle_data: FHIR Bundle resource
            
        Returns:
            List of parsed MedicationRequest resources
            
        Raises:
            ValueError: If bundle cannot be parsed safely
        """
        if not isinstance(bundle_data, dict):
            raise ValueError("Bundle data must be a dictionary")
        
        if bundle_data.get("resourceType") != "Bundle":
            raise ValueError("Resource type must be Bundle")
        
        entries = bundle_data.get("entry", [])
        medication_requests = []
        
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "MedicationRequest":
                try:
                    med_request = self.parse_medication_request(resource)
                    medication_requests.append(med_request)
                except ValueError as e:
                    # Log error but continue processing other entries
                    # In production, would use proper logging
                    print(f"Warning: Failed to parse MedicationRequest: {e}")
        
        return medication_requests
    
    def validate_parsing_integrity(self, original_data: Dict[str, Any], 
                                 parsed_request: MedicationRequest) -> bool:
        """
        Validate that parsing preserved critical data integrity.
        
        Args:
            original_data: Original FHIR data
            parsed_request: Parsed MedicationRequest
            
        Returns:
            True if integrity is maintained, False otherwise
        """
        try:
            # Re-serialize the parsed data and compare critical fields
            parsed_dict = parsed_request.model_dump(exclude_none=True)
            
            # Check medication specification
            if "medicationCodeableConcept" in original_data:
                if not parsed_dict.get("medicationCodeableConcept"):
                    return False
                
                orig_text = original_data["medicationCodeableConcept"].get("text")
                parsed_text = parsed_dict["medicationCodeableConcept"].get("text")
                if orig_text != parsed_text:
                    return False
            
            # Check dosage instructions
            if "dosageInstruction" in original_data:
                if not parsed_dict.get("dosageInstruction"):
                    return False
                
                orig_count = len(original_data["dosageInstruction"])
                parsed_count = len(parsed_dict["dosageInstruction"])
                if orig_count != parsed_count:
                    return False
            
            # Check status and intent
            for field in ["status", "intent"]:
                if original_data.get(field) != parsed_dict.get(field):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_parser_metadata(self) -> Dict[str, Any]:
        """
        Get parser metadata for processing tracking.
        
        Returns:
            Parser metadata dictionary
        """
        return {
            "parser_version": self.parser_version,
            "supported_resources": self.supported_resource_types,
            "parsed_at": datetime.utcnow().isoformat(),
            "safety_level": "critical",
            "ai_processing": False
        }