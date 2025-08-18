"""
CCDA to FHIR Transformer

This module transforms CCDA-parsed data into FHIR-compatible format to leverage
the existing hybrid clinical processing pipeline while maintaining exact preservation
of critical medical data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class CCDATransformationError(Exception):
    """Exception for CCDA to FHIR transformation errors."""
    pass


class CCDAToFHIRTransformer:
    """
    Transform CCDA parsed data to FHIR-compatible internal format.
    
    This enables the existing FHIR processing pipeline to handle CCDA data
    while maintaining the same safety guarantees and processing workflow.
    """
    
    def __init__(self):
        """Initialize CCDA to FHIR transformer."""
        self.transformer_version = "1.0.0"
        
        # CCDA to FHIR code mappings
        self.vital_sign_mappings = {
            "8480-6": "systolic_bp",      # Systolic blood pressure
            "8462-4": "diastolic_bp",     # Diastolic blood pressure
            "8867-4": "heart_rate",       # Heart rate
            "8310-5": "body_temperature", # Body temperature
            "39156-5": "bmi",             # Body mass index
            "8302-2": "height",           # Body height
            "29463-7": "weight"           # Body weight
        }
        
        # Lab test common mappings
        self.lab_test_mappings = {
            "4548-4": "hemoglobin_a1c",   # Hemoglobin A1c
            "2345-7": "glucose",          # Glucose
            "2093-3": "cholesterol",      # Cholesterol
            "718-7": "hemoglobin",        # Hemoglobin
            "33747-0": "hematocrit"       # Hematocrit
        }
    
    def transform_ccda_to_fhir_bundle(self, ccda_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform complete CCDA data to FHIR Bundle format.
        
        Args:
            ccda_data: Parsed CCDA data from CCDAParser
            
        Returns:
            FHIR Bundle compatible with existing processing pipeline
        """
        try:
            bundle_id = str(uuid.uuid4())
            
            # Create FHIR Bundle structure
            fhir_bundle = {
                "resourceType": "Bundle",
                "id": bundle_id,
                "meta": {
                    "source": "ccda_transformation",
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
                },
                "type": "document",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "entry": []
            }
            
            # Add patient resource (simplified)
            patient_resource = self._create_patient_resource(ccda_data.get('metadata', {}))
            fhir_bundle["entry"].append({
                "resource": patient_resource,
                "fullUrl": f"urn:uuid:{uuid.uuid4()}"
            })
            
            # Transform sections to FHIR resources
            sections = ccda_data.get('sections', {})
            
            # Transform medications
            if 'medications' in sections:
                medication_resources = self._transform_medications(sections['medications'])
                for resource in medication_resources:
                    fhir_bundle["entry"].append({
                        "resource": resource,
                        "fullUrl": f"urn:uuid:{uuid.uuid4()}"
                    })
            
            # Transform lab results
            if 'results' in sections:
                observation_resources = self._transform_lab_results(sections['results'])
                for resource in observation_resources:
                    fhir_bundle["entry"].append({
                        "resource": resource,
                        "fullUrl": f"urn:uuid:{uuid.uuid4()}"
                    })
            
            # Transform vital signs
            if 'vital_signs' in sections:
                vital_resources = self._transform_vital_signs(sections['vital_signs'])
                for resource in vital_resources:
                    fhir_bundle["entry"].append({
                        "resource": resource,
                        "fullUrl": f"urn:uuid:{uuid.uuid4()}"
                    })
            
            # Transform allergies
            if 'allergies' in sections:
                allergy_resources = self._transform_allergies(sections['allergies'])
                for resource in allergy_resources:
                    fhir_bundle["entry"].append({
                        "resource": resource,
                        "fullUrl": f"urn:uuid:{uuid.uuid4()}"
                    })
            
            # Add transformation metadata
            fhir_bundle["_ccda_transformation"] = {
                "source_document_type": "ccda",
                "transformer_version": self.transformer_version,
                "original_sections": list(sections.keys()),
                "transformation_timestamp": datetime.utcnow().isoformat()
            }
            
            return fhir_bundle
            
        except Exception as e:
            logger.error(f"CCDA to FHIR transformation failed: {str(e)}")
            raise CCDATransformationError(f"Failed to transform CCDA to FHIR: {str(e)}")
    
    def _create_patient_resource(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified patient resource from CCDA metadata."""
        return {
            "resourceType": "Patient",
            "id": str(uuid.uuid4()),
            "meta": {
                "source": "ccda_transformation"
            },
            "identifier": [{
                "value": metadata.get('document_id', 'unknown'),
                "system": "ccda-document-id"
            }],
            "active": True
        }
    
    def _transform_medications(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform CCDA medications to FHIR MedicationRequest resources.
        
        CRITICAL: Preserves exact medication data - no AI processing.
        """
        fhir_medications = []
        
        for med in medications:
            try:
                # Create MedicationRequest resource
                med_request = {
                    "resourceType": "MedicationRequest",
                    "id": str(uuid.uuid4()),
                    "meta": {
                        "source": "ccda_medication_transformation"
                    },
                    "status": self._map_medication_status(med.get('status', 'active')),
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "text": med.get('substance_name', 'Unknown medication')
                    },
                    "subject": {
                        "reference": "Patient/patient-id"
                    }
                }
                
                # Add dosage information with exact preservation
                dosage_instruction = {}
                
                if med.get('dosage_amount') and med.get('dosage_unit'):
                    dosage_instruction["doseAndRate"] = [{
                        "doseQuantity": {
                            "value": float(med['dosage_amount']) if med['dosage_amount'].replace('.', '').isdigit() else None,
                            "unit": med['dosage_unit']
                        }
                    }]
                
                if med.get('frequency'):
                    dosage_instruction["text"] = f"{med.get('substance_name')} {med.get('dosage_amount', '')} {med.get('dosage_unit', '')} - {med['frequency']}"
                
                if med.get('route'):
                    dosage_instruction["route"] = {
                        "text": med['route']
                    }
                
                if dosage_instruction:
                    med_request["dosageInstruction"] = [dosage_instruction]
                
                # Preserve original CCDA data and hash
                med_request["_ccda_preservation"] = {
                    "original_data": med,
                    "preservation_hash": med.get('preservation_hash'),
                    "safety_level": "CRITICAL"
                }
                
                fhir_medications.append(med_request)
                
            except Exception as e:
                logger.error(f"Error transforming medication {med.get('substance_name', 'unknown')}: {str(e)}")
                continue
        
        return fhir_medications
    
    def _transform_lab_results(self, lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform CCDA lab results to FHIR Observation resources.
        
        CRITICAL: Preserves exact lab values - no AI processing.
        """
        fhir_observations = []
        
        for lab in lab_results:
            try:
                # Create Observation resource
                observation = {
                    "resourceType": "Observation",
                    "id": str(uuid.uuid4()),
                    "meta": {
                        "source": "ccda_lab_transformation"
                    },
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory"
                        }]
                    }],
                    "code": {
                        "text": lab.get('test_name', 'Unknown test')
                    },
                    "subject": {
                        "reference": "Patient/patient-id"
                    }
                }
                
                # Add test code if available
                if lab.get('test_code'):
                    observation["code"]["coding"] = [{
                        "code": lab['test_code'],
                        "display": lab.get('test_name')
                    }]
                
                # Add value with exact preservation
                if lab.get('value'):
                    value_quantity = {
                        "value": float(lab['value']) if lab['value'].replace('.', '').replace('-', '').isdigit() else None
                    }
                    
                    if lab.get('unit'):
                        value_quantity["unit"] = lab['unit']
                        value_quantity["code"] = lab['unit']
                    
                    observation["valueQuantity"] = value_quantity
                
                # Add reference range
                if lab.get('reference_range'):
                    observation["referenceRange"] = [{
                        "text": lab['reference_range']
                    }]
                
                # Add interpretation (abnormal flags)
                if lab.get('interpretation'):
                    observation["interpretation"] = [{
                        "coding": [{
                            "code": lab['interpretation'],
                            "display": self._map_interpretation_code(lab['interpretation'])
                        }]
                    }]
                
                # Preserve original CCDA data and hash
                observation["_ccda_preservation"] = {
                    "original_data": lab,
                    "preservation_hash": lab.get('preservation_hash'),
                    "safety_level": "CRITICAL"
                }
                
                fhir_observations.append(observation)
                
            except Exception as e:
                logger.error(f"Error transforming lab result {lab.get('test_name', 'unknown')}: {str(e)}")
                continue
        
        return fhir_observations
    
    def _transform_vital_signs(self, vital_signs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform CCDA vital signs to FHIR Observation resources.
        
        CRITICAL: Preserves exact vital sign values - no AI processing.
        """
        fhir_vitals = []
        
        for vital in vital_signs:
            try:
                # Create Observation resource
                observation = {
                    "resourceType": "Observation",
                    "id": str(uuid.uuid4()),
                    "meta": {
                        "source": "ccda_vital_transformation"
                    },
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }]
                    }],
                    "code": {
                        "text": vital.get('vital_name', 'Unknown vital sign')
                    },
                    "subject": {
                        "reference": "Patient/patient-id"
                    }
                }
                
                # Add vital sign code if available
                if vital.get('vital_code'):
                    observation["code"]["coding"] = [{
                        "system": "http://loinc.org",
                        "code": vital['vital_code'],
                        "display": vital.get('vital_name')
                    }]
                
                # Add value with exact preservation
                if vital.get('value'):
                    value_quantity = {
                        "value": float(vital['value']) if vital['value'].replace('.', '').replace('/', '').isdigit() else None
                    }
                    
                    if vital.get('unit'):
                        value_quantity["unit"] = vital['unit']
                        value_quantity["code"] = vital['unit']
                    
                    observation["valueQuantity"] = value_quantity
                
                # Add effective time if available
                if vital.get('measurement_time'):
                    observation["effectiveDateTime"] = self._format_ccda_datetime(vital['measurement_time'])
                
                # Preserve original CCDA data and hash
                observation["_ccda_preservation"] = {
                    "original_data": vital,
                    "preservation_hash": vital.get('preservation_hash'),
                    "safety_level": "CRITICAL"
                }
                
                fhir_vitals.append(observation)
                
            except Exception as e:
                logger.error(f"Error transforming vital sign {vital.get('vital_name', 'unknown')}: {str(e)}")
                continue
        
        return fhir_vitals
    
    def _transform_allergies(self, allergies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform CCDA allergies to FHIR AllergyIntolerance resources.
        
        CRITICAL: Preserves exact allergy information - no AI processing.
        """
        fhir_allergies = []
        
        for allergy in allergies:
            try:
                # Create AllergyIntolerance resource
                allergy_intolerance = {
                    "resourceType": "AllergyIntolerance",
                    "id": str(uuid.uuid4()),
                    "meta": {
                        "source": "ccda_allergy_transformation"
                    },
                    "clinicalStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                            "code": "active",
                            "display": "Active"
                        }]
                    },
                    "code": {
                        "text": allergy.get('allergen', 'Unknown allergen')
                    },
                    "patient": {
                        "reference": "Patient/patient-id"
                    }
                }
                
                # Add severity if available
                if allergy.get('severity'):
                    severity_code = self._map_allergy_severity(allergy['severity'])
                    if severity_code:
                        allergy_intolerance["reaction"] = [{
                            "severity": severity_code
                        }]
                
                # Preserve original CCDA data and hash
                allergy_intolerance["_ccda_preservation"] = {
                    "original_data": allergy,
                    "preservation_hash": allergy.get('preservation_hash'),
                    "safety_level": "CRITICAL"
                }
                
                fhir_allergies.append(allergy_intolerance)
                
            except Exception as e:
                logger.error(f"Error transforming allergy {allergy.get('allergen', 'unknown')}: {str(e)}")
                continue
        
        return fhir_allergies
    
    def _map_medication_status(self, ccda_status: str) -> str:
        """Map CCDA medication status to FHIR status."""
        status_mapping = {
            "active": "active",
            "completed": "completed", 
            "cancelled": "cancelled",
            "stopped": "stopped"
        }
        return status_mapping.get(ccda_status.lower(), "active")
    
    def _map_interpretation_code(self, interp_code: str) -> str:
        """Map CCDA interpretation code to display name."""
        interpretation_mapping = {
            "H": "High",
            "L": "Low", 
            "N": "Normal",
            "A": "Abnormal",
            "AA": "Critical abnormal"
        }
        return interpretation_mapping.get(interp_code, interp_code)
    
    def _map_allergy_severity(self, severity: str) -> Optional[str]:
        """Map CCDA allergy severity to FHIR severity."""
        severity_mapping = {
            "mild": "mild",
            "moderate": "moderate",
            "severe": "severe"
        }
        return severity_mapping.get(severity.lower())
    
    def _format_ccda_datetime(self, ccda_time: str) -> str:
        """Format CCDA datetime to FHIR datetime."""
        try:
            # CCDA format: YYYYMMDDHHMMSS
            if len(ccda_time) >= 8:
                year = ccda_time[:4]
                month = ccda_time[4:6]
                day = ccda_time[6:8]
                
                if len(ccda_time) >= 14:
                    hour = ccda_time[8:10]
                    minute = ccda_time[10:12]
                    second = ccda_time[12:14]
                    return f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"
                else:
                    return f"{year}-{month}-{day}"
            
            return ccda_time  # Return as-is if format not recognized
            
        except Exception as e:
            logger.warning(f"Error formatting CCDA datetime {ccda_time}: {str(e)}")
            return ccda_time
    
    def validate_transformation_integrity(self, original_ccda: Dict[str, Any], fhir_bundle: Dict[str, Any]) -> bool:
        """
        Validate that critical data was preserved during transformation.
        
        Returns True if all critical data preservation hashes match.
        """
        try:
            # Extract preservation hashes from FHIR bundle
            fhir_hashes = set()
            for entry in fhir_bundle.get('entry', []):
                resource = entry.get('resource', {})
                preservation_data = resource.get('_ccda_preservation', {})
                if preservation_data.get('preservation_hash'):
                    fhir_hashes.add(preservation_data['preservation_hash'])
            
            # Extract original hashes from CCDA data
            original_hashes = set()
            sections = original_ccda.get('sections', {})
            for section_name, section_data in sections.items():
                for item in section_data:
                    if item.get('preservation_hash'):
                        original_hashes.add(item['preservation_hash'])
            
            # Verify all original hashes are present in transformed data
            missing_hashes = original_hashes - fhir_hashes
            if missing_hashes:
                logger.error(f"Data integrity validation failed. Missing hashes: {missing_hashes}")
                return False
            
            logger.info(f"Data integrity validation passed. Verified {len(original_hashes)} preservation hashes.")
            return True
            
        except Exception as e:
            logger.error(f"Error during transformation integrity validation: {str(e)}")
            return False