"""
Medication interaction and contraindication test scenarios.

This module tests complex clinical scenarios involving drug interactions,
contraindications, and safety monitoring that require exact preservation
of critical medication information while providing enhanced patient guidance.

All scenarios represent real-world clinical challenges that healthcare
providers encounter when managing patients on multiple medications.
"""

import pytest
from typing import Dict, Any, List
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import SafetyLevel, ProcessingType


class TestMedicationInteractionScenarios:
    """
    Test scenarios involving potential medication interactions
    that require careful monitoring and patient education.
    """
    
    def test_warfarin_antibiotic_interaction_scenario(self):
        """
        Test warfarin-antibiotic interaction requiring INR monitoring.
        
        Scenario: Patient on warfarin prescribed antibiotics
        - Warfarin (anticoagulant) with narrow therapeutic window
        - Amoxicillin (may potentiate warfarin effect)
        - Critical interaction requiring enhanced monitoring
        - Patient education about bleeding risk
        """
        processor = HybridClinicalProcessor()
        
        warfarin_antibiotic_bundle = {
            "resourceType": "Bundle",
            "id": "warfarin-interaction-001",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "interaction-patient-001",
                        "name": [{"family": "InteractionPatient", "given": ["Richard"]}]
                    }
                },
                # Warfarin - baseline anticoagulation
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "warfarin-baseline-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "855332",
                                "display": "Warfarin Sodium 5 MG Oral Tablet"
                            }],
                            "text": "Warfarin sodium 5mg tablets"
                        },
                        "subject": {"reference": "Patient/interaction-patient-001"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth once daily in evening, adjust dose based on INR results",
                            "patientInstruction": "ANTICOAGULANT: Take same time daily. Target INR 2.0-3.0. DRUG INTERACTION ALERT: Multiple medications can affect warfarin levels. Check with pharmacist before starting any new medications including antibiotics, pain relievers, vitamins, or herbal supplements. Monitor for unusual bleeding or bruising.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["18:00"]
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                },
                # Amoxicillin - antibiotic with warfarin interaction potential
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "amoxicillin-interaction-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "308182",
                                "display": "Amoxicillin 500 MG Oral Capsule"
                            }],
                            "text": "Amoxicillin 500mg capsules"
                        },
                        "subject": {"reference": "Patient/interaction-patient-001"},
                        "dosageInstruction": [{
                            "text": "Take 1 capsule by mouth three times daily for 10 days for bacterial infection",
                            "patientInstruction": "ANTIBIOTIC: Complete full 10-day course even if feeling better. Take with or without food. CRITICAL DRUG INTERACTION WARNING: This antibiotic may increase the effect of your warfarin (blood thinner), increasing bleeding risk. You will need more frequent INR blood tests (likely every 3-4 days) during antibiotic treatment and for 1 week after completion. Watch for signs of increased bleeding: unusual bruising, nosebleeds, blood in urine/stool, excessive bleeding from cuts.",
                            "timing": {
                                "repeat": {
                                    "frequency": 3,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["08:00", "14:00", "20:00"]
                                }
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "capsule",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{capsule}"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 30, "unit": "capsule"},
                            "numberOfRepeatsAllowed": 0  # No refills for antibiotics
                        }
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(warfarin_antibiotic_bundle)
        
        # CRITICAL: All medication names and doses must be preserved exactly
        assert len(result.medications) == 2
        
        warfarin = next((m for m in result.medications if "Warfarin" in m.medication_name), None)
        amoxicillin = next((m for m in result.medications if "Amoxicillin" in m.medication_name), None)
        
        assert warfarin is not None
        assert amoxicillin is not None
        
        # CRITICAL: Exact medication details preserved
        assert warfarin.medication_name == "Warfarin sodium 5mg tablets"
        assert "1 tablet" in warfarin.dosage
        assert "1 time(s) per 1 d" in warfarin.frequency
        
        assert amoxicillin.medication_name == "Amoxicillin 500mg capsules"
        assert "1 capsule" in amoxicillin.dosage
        assert "3 time(s) per 1 d" in amoxicillin.frequency
        
        # CRITICAL: Drug interaction warnings must be preserved exactly
        assert "DRUG INTERACTION ALERT" in warfarin.instructions or "drug interaction" in warfarin.instructions.lower()
        assert "CRITICAL DRUG INTERACTION WARNING" in amoxicillin.instructions
        assert "warfarin" in amoxicillin.instructions.lower()
        assert "bleeding risk" in amoxicillin.instructions.lower()
        assert "INR blood tests" in amoxicillin.instructions
        
        # CRITICAL: No AI processing of medication interaction data
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed
    
    def test_diabetes_medication_contraindication_scenario(self):
        """
        Test diabetes medication with kidney disease contraindication.
        
        Scenario: Diabetic patient with declining kidney function
        - Metformin contraindicated with severe kidney disease
        - Dose adjustment requirements based on creatinine clearance
        - Alternative medication considerations
        """
        processor = HybridClinicalProcessor()
        
        metformin_contraindication_data = {
            "resourceType": "MedicationRequest",
            "id": "metformin-kidney-contraindication-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197804",
                    "display": "Metformin Hydrochloride 500 MG Oral Tablet"
                }],
                "text": "Metformin 500mg tablets"
            },
            "subject": {"reference": "Patient/kidney-disease-patient-001"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth twice daily with meals. CONTRAINDICATION WARNING: Monitor kidney function closely",
                "patientInstruction": "KIDNEY FUNCTION MONITORING REQUIRED: This medication is processed by the kidneys. CONTRAINDICATION: Do not use if creatinine clearance <30 mL/min. Current dose adjusted for mild kidney impairment (CrCl 45-60 mL/min). Must check kidney function every 3-6 months. STOP medication and contact provider immediately if experiencing: persistent nausea/vomiting, unusual muscle pain, trouble breathing, unusual tiredness, stomach pain, or dizziness (signs of lactic acidosis). Dehydration from illness can worsen kidney function - contact provider if unable to maintain fluid intake.",
                "timing": {
                    "repeat": {
                        "frequency": 2,
                        "period": 1,
                        "periodUnit": "d",
                        "when": ["PCM"]  # after meals
                    }
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 1,
                        "unit": "tablet",
                        "system": "http://unitsofmeasure.org",
                        "code": "{tbl}"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(metformin_contraindication_data)
        
        # CRITICAL: Medication name and dose preserved exactly
        assert result.medication_name == "Metformin 500mg tablets"
        assert "1 tablet" in result.dosage
        assert "2 time(s) per 1 d" in result.frequency
        
        # CRITICAL: Contraindication warnings must be preserved exactly
        assert "CONTRAINDICATION WARNING" in result.instructions
        assert "kidney function" in result.instructions.lower()
        assert "creatinine clearance" in result.instructions
        assert "<30 mL/min" in result.instructions
        assert "lactic acidosis" in result.instructions.lower()
        
        # CRITICAL: No AI processing of contraindication information
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed
    
    def test_opioid_benzodiazepine_interaction_scenario(self):
        """
        Test dangerous opioid-benzodiazepine interaction.
        
        Scenario: Patient prescribed both opioid and benzodiazepine
        - High risk of respiratory depression
        - FDA black box warning combination
        - Requires careful monitoring and patient education
        """
        processor = HybridClinicalProcessor()
        
        opioid_benzo_bundle = {
            "resourceType": "Bundle",
            "id": "opioid-benzo-interaction-001",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "high-risk-interaction-patient",
                        "name": [{"family": "HighRiskPatient", "given": ["Michael"]}]
                    }
                },
                # Oxycodone - opioid pain medication
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "oxycodone-high-risk-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "1049621",
                                "display": "Oxycodone Hydrochloride 5 MG Oral Tablet"
                            }],
                            "text": "Oxycodone 5mg tablets"
                        },
                        "subject": {"reference": "Patient/high-risk-interaction-patient"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth every 6 hours as needed for severe pain. Maximum 4 tablets in 24 hours.",
                            "patientInstruction": "CONTROLLED SUBSTANCE - OPIOID: FDA BLACK BOX WARNING: Concomitant use with benzodiazepines (like lorazepam) increases risk of profound sedation, respiratory depression, coma, and death. Use only if benefits outweigh risks. BOTH medications cause drowsiness and slowed breathing - NEVER exceed prescribed doses. Do not use alcohol. Have someone check on you regularly. Seek immediate medical attention for slow/shallow breathing, extreme drowsiness, confusion, or blue lips/fingernails.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 6,
                                    "periodUnit": "h"
                                }
                            },
                            "asNeeded": {
                                "text": "severe pain"
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }],
                            "maxDosePerPeriod": {
                                "numerator": {"value": 4, "unit": "tablet"},
                                "denominator": {"value": 24, "unit": "h"}
                            }
                        }]
                    }
                },
                # Lorazepam - benzodiazepine
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "lorazepam-high-risk-001",
                        "status": "active",
                        "intent": "order",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197589",
                                "display": "Lorazepam 0.5 MG Oral Tablet"
                            }],
                            "text": "Lorazepam 0.5mg tablets"
                        },
                        "subject": {"reference": "Patient/high-risk-interaction-patient"},
                        "dosageInstruction": [{
                            "text": "Take 1 tablet by mouth twice daily as needed for anxiety. Maximum 3 tablets in 24 hours.",
                            "patientInstruction": "CONTROLLED SUBSTANCE - BENZODIAZEPINE: FDA BLACK BOX WARNING: Concomitant use with opioids increases risk of profound sedation, respiratory depression, coma, and death. DANGEROUS COMBINATION with your oxycodone prescription. Use lowest effective doses. Avoid alcohol completely. May cause dependence with long-term use. Do not stop suddenly after regular use. Monitor for breathing problems, especially when combined with opioid pain medication.",
                            "timing": {
                                "repeat": {
                                    "frequency": 2,
                                    "period": 1,
                                    "periodUnit": "d"
                                }
                            },
                            "asNeeded": {
                                "text": "anxiety"
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Oral route"
                                }]
                            },
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }],
                            "maxDosePerPeriod": {
                                "numerator": {"value": 3, "unit": "tablet"},
                                "denominator": {"value": 24, "unit": "h"}
                            }
                        }]
                    }
                }
            ]
        }
        
        result = processor.process_clinical_data(opioid_benzo_bundle)
        
        # CRITICAL: Both medications processed correctly
        assert len(result.medications) == 2
        
        oxycodone = next((m for m in result.medications if "Oxycodone" in m.medication_name), None)
        lorazepam = next((m for m in result.medications if "Lorazepam" in m.medication_name), None)
        
        assert oxycodone is not None
        assert lorazepam is not None
        
        # CRITICAL: Exact medication details preserved
        assert oxycodone.medication_name == "Oxycodone 5mg tablets"
        assert "1 tablet" in oxycodone.dosage
        assert "Maximum 4 tablets" in oxycodone.instructions
        
        assert lorazepam.medication_name == "Lorazepam 0.5mg tablets"
        assert "0.5 tablet" in lorazepam.dosage or "1 tablet" in lorazepam.dosage
        assert "Maximum 3 tablets" in lorazepam.instructions
        
        # CRITICAL: FDA black box warnings must be preserved exactly
        assert "FDA BLACK BOX WARNING" in oxycodone.instructions
        assert "benzodiazepines" in oxycodone.instructions.lower()
        assert "respiratory depression" in oxycodone.instructions.lower()
        
        assert "FDA BLACK BOX WARNING" in lorazepam.instructions
        assert "opioids" in lorazepam.instructions.lower()
        assert "oxycodone" in lorazepam.instructions.lower()
        
        # CRITICAL: No AI processing of controlled substance interaction data
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed


class TestContraindicationScenarios:
    """
    Test scenarios involving medication contraindications
    where specific medications are prohibited in certain patients.
    """
    
    def test_ace_inhibitor_pregnancy_contraindication(self):
        """
        Test ACE inhibitor contraindication in pregnancy.
        
        Scenario: Pregnant patient with hypertension
        - ACE inhibitors absolutely contraindicated in pregnancy
        - Teratogenic effects on fetal development
        - Alternative antihypertensive required
        """
        processor = HybridClinicalProcessor()
        
        pregnancy_contraindication_data = {
            "resourceType": "MedicationRequest",
            "id": "lisinopril-pregnancy-contraindication",
            "status": "entered-in-error",  # Contraindicated medication
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197361",
                    "display": "Lisinopril 10 MG Oral Tablet"
                }],
                "text": "Lisinopril 10mg tablets"
            },
            "subject": {"reference": "Patient/pregnant-patient-001"},
            "statusReason": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "182856006",
                    "display": "Drug contraindicated in pregnancy"
                }],
                "text": "ABSOLUTE CONTRAINDICATION: ACE inhibitors prohibited in pregnancy"
            },
            "dosageInstruction": [{
                "text": "CONTRAINDICATED IN PREGNANCY - DO NOT USE",
                "patientInstruction": "PREGNANCY CONTRAINDICATION: This medication (ACE inhibitor) is absolutely contraindicated during pregnancy due to risk of severe birth defects including kidney problems, skull defects, and fetal death. If you are pregnant or planning pregnancy, stop this medication immediately and contact your healthcare provider for alternative blood pressure medication. Pregnancy category D - positive evidence of human fetal risk.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "d"
                    }
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 1,
                        "unit": "tablet",
                        "system": "http://unitsofmeasure.org",
                        "code": "{tbl}"
                    }
                }]
            }]
        }
        
        # This should raise an error due to the contraindication
        with pytest.raises(ValueError) as exc_info:
            processor.process_medication_data(pregnancy_contraindication_data)
        
        # Error should indicate contraindication
        assert "contraindication" in str(exc_info.value).lower() or "entered-in-error" in str(exc_info.value).lower()
    
    def test_nsaid_heart_failure_contraindication(self):
        """
        Test NSAID contraindication in heart failure.
        
        Scenario: Heart failure patient prescribed NSAID
        - NSAIDs can worsen heart failure
        - Fluid retention and kidney effects
        - Alternative pain management required
        """
        processor = HybridClinicalProcessor()
        
        nsaid_contraindication_data = {
            "resourceType": "MedicationRequest",
            "id": "ibuprofen-heart-failure-contraindication",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "310965",
                    "display": "Ibuprofen 600 MG Oral Tablet"
                }],
                "text": "Ibuprofen 600mg tablets"
            },
            "subject": {"reference": "Patient/heart-failure-patient-001"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth every 8 hours as needed for pain. CAUTION: Heart failure contraindication",
                "patientInstruction": "HEART FAILURE CONTRAINDICATION WARNING: NSAIDs like ibuprofen can worsen heart failure by causing fluid retention and reducing kidney function. AVOID if you have heart failure. This medication may cause: leg swelling, shortness of breath, weight gain, elevated blood pressure, and kidney problems. Alternative pain management options include acetaminophen (Tylenol) or topical pain relievers. Contact your cardiologist before using any anti-inflammatory medications.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 8,
                        "periodUnit": "h"
                    }
                },
                "asNeeded": {
                    "text": "pain"
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 1,
                        "unit": "tablet",
                        "system": "http://unitsofmeasure.org",
                        "code": "{tbl}"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(nsaid_contraindication_data)
        
        # CRITICAL: Medication details preserved exactly
        assert result.medication_name == "Ibuprofen 600mg tablets"
        assert "1 tablet" in result.dosage
        
        # CRITICAL: Contraindication warning preserved exactly
        assert "HEART FAILURE CONTRAINDICATION WARNING" in result.instructions
        assert "worsen heart failure" in result.instructions.lower()
        assert "fluid retention" in result.instructions.lower()
        assert "AVOID if you have heart failure" in result.instructions
        
        # CRITICAL: No AI processing of contraindication data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestAgeSpecificDosingScenarios:
    """
    Test scenarios for age-specific dosing requirements
    where adult and pediatric/geriatric dosing differs significantly.
    """
    
    def test_pediatric_weight_based_dosing(self):
        """
        Test pediatric weight-based dosing calculations.
        
        Scenario: 5-year-old with ear infection
        - Amoxicillin dosed at 40-50 mg/kg/day
        - Weight-based calculation critical for safety
        - Liquid formulation for pediatric use
        """
        processor = HybridClinicalProcessor()
        
        pediatric_dosing_data = {
            "resourceType": "MedicationRequest",
            "id": "amoxicillin-pediatric-weight-based",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "308189",
                    "display": "Amoxicillin 250 MG/5 ML Oral Suspension"
                }],
                "text": "Amoxicillin 250mg/5mL oral suspension"
            },
            "subject": {"reference": "Patient/pediatric-patient-5yr-18kg"},
            "dosageInstruction": [{
                "text": "Give 4.5 mL (225mg) by mouth twice daily for 10 days. Weight-based dose: 25 mg/kg/day divided twice daily (child weighs 18 kg)",
                "patientInstruction": "PEDIATRIC WEIGHT-BASED DOSING: Dose calculated as 25 mg/kg/day ÷ 2 doses = 12.5 mg/kg per dose. Child weighs 18 kg: 12.5 mg/kg × 18 kg = 225 mg per dose = 4.5 mL per dose. Shake bottle well before each use. Use provided measuring device - do not use household spoons. Give with or without food. Complete full 10-day course even if child feels better. Store in refrigerator.",
                "timing": {
                    "repeat": {
                        "frequency": 2,
                        "period": 1,
                        "periodUnit": "d",
                        "timeOfDay": ["08:00", "20:00"]
                    }
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 4.5,
                        "unit": "mL",
                        "system": "http://unitsofmeasure.org",
                        "code": "mL"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(pediatric_dosing_data)
        
        # CRITICAL: Exact pediatric dosing calculations must be preserved
        assert result.medication_name == "Amoxicillin 250mg/5mL oral suspension"
        assert "4.5 mL" in result.dosage
        assert "2 time(s) per 1 d" in result.frequency
        
        # CRITICAL: Weight-based calculation details must be preserved exactly
        assert "25 mg/kg/day" in result.instructions
        assert "18 kg" in result.instructions
        assert "225mg" in result.instructions
        assert "12.5 mg/kg per dose" in result.instructions
        
        # CRITICAL: No AI processing of pediatric dosing calculations
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed
    
    def test_geriatric_dose_reduction_scenario(self):
        """
        Test geriatric dose reduction for medication safety.
        
        Scenario: 85-year-old with reduced kidney function
        - Digoxin dose reduced for age and kidney function
        - "Start low, go slow" geriatric principle
        - Enhanced monitoring requirements
        """
        processor = HybridClinicalProcessor()
        
        geriatric_dosing_data = {
            "resourceType": "MedicationRequest",
            "id": "digoxin-geriatric-reduced-dose",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197604",
                    "display": "Digoxin 0.125 MG Oral Tablet"
                }],
                "text": "Digoxin 0.125mg (125 mcg) tablets"
            },
            "subject": {"reference": "Patient/geriatric-patient-85yr-45kg"},
            "dosageInstruction": [{
                "text": "Take 1 tablet by mouth every other day (alternate days). Geriatric dose reduction: standard dose 0.25mg daily reduced to 0.125mg every other day due to age 85 years, weight 45kg, and creatinine clearance 35 mL/min",
                "patientInstruction": "GERIATRIC DOSING - REDUCED FREQUENCY: Take every other day (Mon-Wed-Fri or Tue-Thu-Sat pattern) due to your age and kidney function. This is HALF the standard frequency to prevent toxicity. NARROW THERAPEUTIC WINDOW: Small difference between effective and toxic dose. Monitor for toxicity signs: nausea, vomiting, visual changes (yellow/green halos), confusion, slow heart rate. Regular blood level monitoring required every 6-8 weeks initially, then every 3-6 months.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 2,
                        "periodUnit": "d"  # Every other day
                    }
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 1,
                        "unit": "tablet",
                        "system": "http://unitsofmeasure.org",
                        "code": "{tbl}"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(geriatric_dosing_data)
        
        # CRITICAL: Exact geriatric dosing must be preserved
        assert result.medication_name == "Digoxin 0.125mg (125 mcg) tablets"
        assert "1 tablet" in result.dosage
        assert "1 time(s) per 2 d" in result.frequency
        
        # CRITICAL: Geriatric rationale must be preserved exactly
        assert "age 85 years" in result.instructions
        assert "45kg" in result.instructions
        assert "creatinine clearance 35 mL/min" in result.instructions
        assert "every other day" in result.instructions.lower()
        assert "HALF the standard frequency" in result.instructions
        
        # CRITICAL: No AI processing of geriatric dosing adjustments
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed