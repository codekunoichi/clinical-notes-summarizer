"""
CCDA XML Parser with Healthcare Safety Guarantees

This module provides secure parsing of CCDA (Continuity of Care Document) XML files
with exact preservation of critical medical data and protection against XML-based attacks.
"""

import hashlib
import logging
from typing import Dict, List, Any, Optional
from xml.etree.ElementTree import ParseError
import defusedxml.ElementTree as ET
from defusedxml import defuse_stdlib
from lxml import etree, html
from datetime import datetime

# Defuse standard library XML parsers against XXE attacks
defuse_stdlib()

logger = logging.getLogger(__name__)


class CCDAParsingError(Exception):
    """Base exception for CCDA parsing errors."""
    pass


class CCDASecurityError(CCDAParsingError):
    """Exception for XML security validation failures."""
    pass


class CCDAValidationError(CCDAParsingError):
    """Exception for CCDA document validation failures.""" 
    pass


class CCDAParser:
    """
    Secure CCDA XML parser with healthcare safety guarantees.
    
    Implements strict security measures and exact preservation of critical medical data.
    """
    
    # CCDA Template IDs for standard sections
    CCDA_SECTION_TEMPLATES = {
        "2.16.840.1.113883.10.20.22.2.1.1": "medications",
        "2.16.840.1.113883.10.20.22.2.3.1": "results",  # Labs
        "2.16.840.1.113883.10.20.22.2.4.1": "vital_signs", 
        "2.16.840.1.113883.10.20.22.2.5.1": "procedures",
        "2.16.840.1.113883.10.20.22.2.6.1": "allergies",
        "2.16.840.1.113883.10.20.22.2.10": "plan_of_care"
    }
    
    # XML namespaces used in CCDA documents
    XML_NAMESPACES = {
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'voc': 'urn:hl7-org:v3/voc'
    }
    
    def __init__(self):
        """Initialize CCDA parser with security settings."""
        self.parser_version = "1.0.0"
        self.max_document_size = 50 * 1024 * 1024  # 50MB limit
        self.supported_document_types = ["CCDA", "ContinuityOfCareDocument"]
        
        # Security settings
        self.security_features = {
            "xxe_protection": True,
            "dtd_validation": False,
            "entity_expansion": False,
            "network_access": False
        }
        
    def parse_ccda_document(self, ccda_xml: str) -> Dict[str, Any]:
        """
        Parse CCDA XML document with comprehensive security validation.
        
        Args:
            ccda_xml: Raw CCDA XML content as string
            
        Returns:
            Dict containing parsed CCDA sections and metadata
            
        Raises:
            CCDASecurityError: If XML security validation fails
            CCDAValidationError: If CCDA structure validation fails
            CCDAParsingError: If general parsing errors occur
        """
        try:
            # Step 1: Security validation
            self._validate_xml_security(ccda_xml)
            
            # Step 2: Parse XML with secure parser
            root = self._parse_xml_securely(ccda_xml)
            
            # Step 3: Validate CCDA document structure
            self._validate_ccda_structure(root)
            
            # Step 4: Extract document metadata
            metadata = self._extract_document_metadata(root)
            
            # Step 5: Parse sections
            sections = self._parse_sections(root)
            
            return {
                "document_type": "ccda",
                "parser_version": self.parser_version,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata,
                "sections": sections,
                "security_validated": True
            }
            
        except Exception as e:
            logger.error(f"CCDA parsing failed: {str(e)}")
            raise CCDAParsingError(f"Failed to parse CCDA document: {str(e)}")
    
    def _validate_xml_security(self, xml_content: str) -> None:
        """
        Validate XML content against security threats.
        
        Protects against:
        - XXE (XML External Entity) attacks
        - DTD (Document Type Definition) attacks  
        - XML bomb attacks
        - Oversized documents
        """
        if not xml_content or not xml_content.strip():
            raise CCDASecurityError("Empty or invalid XML content")
            
        # Check document size
        if len(xml_content.encode('utf-8')) > self.max_document_size:
            raise CCDASecurityError(f"Document exceeds maximum size of {self.max_document_size} bytes")
        
        # Check for DTD declarations (potential security risk)
        if '<!DOCTYPE' in xml_content.upper():
            raise CCDASecurityError("DTD declarations are not allowed for security reasons")
            
        # Check for external entity references
        if '&' in xml_content and any(pattern in xml_content.upper() for pattern in ['SYSTEM', 'ENTITY', 'PUBLIC']):
            raise CCDASecurityError("External entity references are not allowed")
            
        # Check for processing instructions that could be malicious
        if '<?' in xml_content and not xml_content.strip().startswith('<?xml'):
            if any(pi in xml_content.upper() for pi in ['<?PHP', '<?ASP', '<?JSP']):
                raise CCDASecurityError("Malicious processing instructions detected")
    
    def _parse_xml_securely(self, xml_content: str):
        """Parse XML using secure parser settings."""
        try:
            # Use defusedxml for secure parsing
            parser = ET.XMLParser(
                resolve_entities=False,  # Disable entity resolution
                no_network=True,         # Disable network access
                strip_cdata=False        # Preserve CDATA sections
            )
            
            root = ET.fromstring(xml_content.encode('utf-8'), parser=parser)
            return root
            
        except ParseError as e:
            raise CCDAParsingError(f"XML parsing error: {str(e)}")
        except Exception as e:
            raise CCDASecurityError(f"Security validation failed during XML parsing: {str(e)}")
    
    def _validate_ccda_structure(self, root) -> None:
        """Validate basic CCDA document structure."""
        # Check root element
        if root.tag != '{urn:hl7-org:v3}ClinicalDocument':
            raise CCDAValidationError(f"Invalid root element: {root.tag}. Expected ClinicalDocument")
        
        # Check for required elements
        required_elements = [
            'typeId',
            'templateId', 
            'id',
            'code',
            'title',
            'recordTarget'
        ]
        
        for elem in required_elements:
            if root.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}{elem}') is None:
                logger.warning(f"Missing recommended element: {elem}")
    
    def _extract_document_metadata(self, root) -> Dict[str, Any]:
        """Extract document metadata from CCDA header."""
        metadata = {}
        
        try:
            # Document ID
            id_elem = root.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}id')
            if id_elem is not None:
                metadata['document_id'] = id_elem.get('extension', 'unknown')
            
            # Document title
            title_elem = root.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}title')
            if title_elem is not None:
                metadata['title'] = title_elem.text
            
            # Effective time
            effective_time = root.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}effectiveTime')
            if effective_time is not None:
                metadata['effective_time'] = effective_time.get('value')
            
            # Template IDs (document type validation)
            template_ids = []
            for template in root.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}templateId'):
                template_id = template.get('root')
                if template_id:
                    template_ids.append(template_id)
            metadata['template_ids'] = template_ids
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            
        return metadata
    
    def _parse_sections(self, root) -> Dict[str, List[Dict[str, Any]]]:
        """Parse all supported CCDA sections."""
        sections = {}
        
        # Find structured body
        structured_body = root.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}structuredBody')
        if structured_body is None:
            logger.warning("No structured body found in CCDA document")
            return sections
        
        # Parse each section by template ID
        for component in structured_body.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}component'):
            section = component.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}section')
            if section is not None:
                template_id = self._get_section_template_id(section)
                if template_id in self.CCDA_SECTION_TEMPLATES:
                    section_name = self.CCDA_SECTION_TEMPLATES[template_id]
                    sections[section_name] = self._parse_section_by_type(section, section_name)
        
        return sections
    
    def _get_section_template_id(self, section) -> Optional[str]:
        """Extract template ID from section."""
        template_elem = section.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}templateId')
        if template_elem is not None:
            return template_elem.get('root')
        return None
    
    def _parse_section_by_type(self, section, section_type: str) -> List[Dict[str, Any]]:
        """Parse section based on its type."""
        if section_type == "medications":
            return self._parse_medications_section(section)
        elif section_type == "results":
            return self._parse_results_section(section)
        elif section_type == "vital_signs":
            return self._parse_vital_signs_section(section)
        elif section_type == "allergies":
            return self._parse_allergies_section(section)
        else:
            return self._parse_generic_section(section)
    
    def _parse_medications_section(self, section) -> List[Dict[str, Any]]:
        """
        Parse medications section with exact preservation.
        
        Critical: No AI processing allowed - preserve exact values.
        """
        medications = []
        
        for entry in section.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}entry'):
            substance_admin = entry.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}substanceAdministration')
            if substance_admin is not None:
                med_data = self._extract_medication_data(substance_admin)
                if med_data:
                    # Generate preservation hash for safety validation
                    med_data['preservation_hash'] = self._generate_preservation_hash(med_data)
                    medications.append(med_data)
        
        return medications
    
    def _extract_medication_data(self, substance_admin) -> Dict[str, Any]:
        """Extract medication data with exact preservation."""
        med_data = {}
        
        try:
            # Medication name
            consumable = substance_admin.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}consumable')
            if consumable is not None:
                material = consumable.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}manufacturedMaterial')
                if material is not None:
                    code_elem = material.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}code')
                    if code_elem is not None:
                        med_data['substance_name'] = code_elem.get('displayName', 'Unknown medication')
            
            # Dosage amount
            dose_quantity = substance_admin.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}doseQuantity')
            if dose_quantity is not None:
                med_data['dosage_amount'] = dose_quantity.get('value')
                med_data['dosage_unit'] = dose_quantity.get('unit')
            
            # Frequency (effective time)
            effective_time = substance_admin.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}effectiveTime')
            if effective_time is not None:
                period = effective_time.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}period')
                if period is not None:
                    period_value = period.get('value')
                    period_unit = period.get('unit')
                    if period_value and period_unit:
                        med_data['frequency'] = f"Every {period_value} {period_unit}"
            
            # Route of administration
            route_code = substance_admin.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}routeCode')
            if route_code is not None:
                med_data['route'] = route_code.get('displayName')
            
            # Status
            status_code = substance_admin.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}statusCode')
            if status_code is not None:
                med_data['status'] = status_code.get('code')
                
        except Exception as e:
            logger.error(f"Error extracting medication data: {str(e)}")
            
        return med_data
    
    def _parse_results_section(self, section) -> List[Dict[str, Any]]:
        """Parse lab results section with exact preservation."""
        results = []
        
        for entry in section.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}entry'):
            organizer = entry.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}organizer')
            if organizer is not None:
                for component in organizer.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}component'):
                    observation = component.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}observation')
                    if observation is not None:
                        result_data = self._extract_lab_result_data(observation)
                        if result_data:
                            result_data['preservation_hash'] = self._generate_preservation_hash(result_data)
                            results.append(result_data)
        
        return results
    
    def _extract_lab_result_data(self, observation) -> Dict[str, Any]:
        """Extract lab result data with exact preservation."""
        result_data = {}
        
        try:
            # Test name
            code_elem = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}code')
            if code_elem is not None:
                result_data['test_name'] = code_elem.get('displayName')
                result_data['test_code'] = code_elem.get('code')
            
            # Test value
            value_elem = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}value')
            if value_elem is not None:
                result_data['value'] = value_elem.get('value')
                result_data['unit'] = value_elem.get('unit')
            
            # Reference range
            reference_range = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}referenceRange')
            if reference_range is not None:
                obs_range = reference_range.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}observationRange')
                if obs_range is not None:
                    text_elem = obs_range.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}text')
                    if text_elem is not None:
                        result_data['reference_range'] = text_elem.text
            
            # Interpretation code (abnormal flags)
            interp_code = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}interpretationCode')
            if interp_code is not None:
                result_data['interpretation'] = interp_code.get('code')
                
        except Exception as e:
            logger.error(f"Error extracting lab result data: {str(e)}")
            
        return result_data
    
    def _parse_vital_signs_section(self, section) -> List[Dict[str, Any]]:
        """Parse vital signs section with exact preservation."""
        vitals = []
        
        for entry in section.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}entry'):
            organizer = entry.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}organizer')
            if organizer is not None:
                for component in organizer.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}component'):
                    observation = component.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}observation')
                    if observation is not None:
                        vital_data = self._extract_vital_sign_data(observation)
                        if vital_data:
                            vital_data['preservation_hash'] = self._generate_preservation_hash(vital_data)
                            vitals.append(vital_data)
        
        return vitals
    
    def _extract_vital_sign_data(self, observation) -> Dict[str, Any]:
        """Extract vital sign data with exact preservation."""
        vital_data = {}
        
        try:
            # Vital sign name
            code_elem = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}code')
            if code_elem is not None:
                vital_data['vital_name'] = code_elem.get('displayName')
                vital_data['vital_code'] = code_elem.get('code')
            
            # Value and unit
            value_elem = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}value')
            if value_elem is not None:
                vital_data['value'] = value_elem.get('value')
                vital_data['unit'] = value_elem.get('unit')
            
            # Effective time
            effective_time = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}effectiveTime')
            if effective_time is not None:
                vital_data['measurement_time'] = effective_time.get('value')
                
        except Exception as e:
            logger.error(f"Error extracting vital sign data: {str(e)}")
            
        return vital_data
    
    def _parse_allergies_section(self, section) -> List[Dict[str, Any]]:
        """Parse allergies section with exact preservation."""
        allergies = []
        
        for entry in section.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}entry'):
            act = entry.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}act')
            if act is not None:
                allergy_data = self._extract_allergy_data(act)
                if allergy_data:
                    allergy_data['preservation_hash'] = self._generate_preservation_hash(allergy_data)
                    allergies.append(allergy_data)
        
        return allergies
    
    def _extract_allergy_data(self, act) -> Dict[str, Any]:
        """Extract allergy data with exact preservation."""
        allergy_data = {}
        
        try:
            # Find the observation within the act
            observation = act.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}observation')
            if observation is not None:
                # Allergen
                value_elem = observation.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}value')
                if value_elem is not None:
                    allergy_data['allergen'] = value_elem.get('displayName')
                
                # Reaction severity
                for entry_relationship in observation.findall(f'.//{{{self.XML_NAMESPACES["hl7"]}}}entryRelationship'):
                    obs = entry_relationship.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}observation')
                    if obs is not None:
                        code = obs.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}code')
                        if code is not None and 'SEV' in code.get('code', ''):
                            value = obs.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}value')
                            if value is not None:
                                allergy_data['severity'] = value.get('displayName')
                                
        except Exception as e:
            logger.error(f"Error extracting allergy data: {str(e)}")
            
        return allergy_data
    
    def _parse_generic_section(self, section) -> List[Dict[str, Any]]:
        """Parse generic section for narrative content."""
        section_data = []
        
        try:
            # Extract section title
            title_elem = section.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}title')
            title = title_elem.text if title_elem is not None else "Unknown Section"
            
            # Extract narrative text
            text_elem = section.find(f'.//{{{self.XML_NAMESPACES["hl7"]}}}text')
            if text_elem is not None:
                # Extract text content (may include HTML)
                narrative_text = self._extract_narrative_text(text_elem)
                if narrative_text:
                    section_data.append({
                        'section_title': title,
                        'narrative_text': narrative_text,
                        'ai_enhancement_allowed': True  # Flag for narrative sections
                    })
                    
        except Exception as e:
            logger.error(f"Error parsing generic section: {str(e)}")
            
        return section_data
    
    def _extract_narrative_text(self, text_elem) -> str:
        """Extract narrative text from CCDA text element."""
        try:
            # Handle both plain text and HTML content
            if text_elem.text:
                return text_elem.text.strip()
            else:
                # Convert XML element to string and clean HTML
                text_content = ET.tostring(text_elem, encoding='unicode', method='text')
                return text_content.strip()
        except Exception as e:
            logger.error(f"Error extracting narrative text: {str(e)}")
            return ""
    
    def _generate_preservation_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash for data preservation validation."""
        # Create deterministic string representation
        critical_fields = sorted([
            f"{k}:{v}" for k, v in data.items() 
            if k not in ['preservation_hash', 'ai_enhancement_allowed']
        ])
        data_string = "|".join(critical_fields)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()[:16]