"""
Realistic FHIR test data for comprehensive clinical scenarios.

This module contains authentic clinical test data that healthcare professionals
would recognize, covering complex medication regimens, multi-condition management,
and real-world scenarios that must be processed with zero-tolerance safety standards.

All test data is de-identified and represents realistic but fictional patients.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import pytest


class ClinicalTestDataFactory:
    """
    Factory class for generating realistic clinical test data.
    
    All generated data follows FHIR R4 standards and represents
    authentic clinical scenarios.
    """
    
    @staticmethod
    def create_diabetes_management_bundle() -> Dict[str, Any]:
        """
        Create comprehensive diabetes management bundle.
        
        Patient: 45-year-old Type 2 diabetic with multiple comorbidities
        - Metformin for glucose control
        - Insulin glargine (basal)
        - Insulin lispro (bolus)
        - Lisinopril for diabetic nephropathy
        - Atorvastatin for dyslipidemia
        """
        return {
            "resourceType": "Bundle",
            "id": "diabetes-comprehensive-001",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat(),
            "entry": [
                {
                    "fullUrl": "Patient/diabetes-patient-comprehensive",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "diabetes-patient-comprehensive",
                        "name": [{"family": "DiabetesComplex", "given": ["Maria"]}],
                        "gender": "female",
                        "birthDate": "1978-03-15",
                        "identifier": [{"value": "DIAB-COMP-001"}]
                    }
                },
                # Metformin - First-line diabetes medication
                {
                    "fullUrl": "MedicationRequest/metformin-diabetes-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "metformin-diabetes-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197804",
                                "display": "Metformin Hydrochloride 500 MG Oral Tablet"
                            }],
                            "text": "Metformin 500mg tablets"
                        },
                        "subject": {"reference": "Patient/diabetes-patient-comprehensive"},
                        "authoredOn": "2024-01-15T10:30:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-001",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Take 1 tablet by mouth twice daily with breakfast and dinner",
                            "patientInstruction": "Take with food to reduce stomach upset. Continue monitoring blood glucose levels. Report persistent nausea, vomiting, or unusual muscle pain immediately (lactic acidosis warning).",
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
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }],
                            "maxDosePerPeriod": {
                                "numerator": {"value": 2, "unit": "tablet"},
                                "denominator": {"value": 1, "unit": "d"}
                            }
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 60, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                },
                # Insulin Glargine - Long-acting basal insulin
                {
                    "fullUrl": "MedicationRequest/insulin-glargine-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "insulin-glargine-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "274783",
                                "display": "Insulin Glargine 100 unit/mL Pen Injector"
                            }],
                            "text": "Lantus (insulin glargine) 100 units/mL pen injector"
                        },
                        "subject": {"reference": "Patient/diabetes-patient-comprehensive"},
                        "authoredOn": "2024-01-15T10:35:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-001",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Inject 28 units subcutaneously once daily at bedtime (same time each evening)",
                            "patientInstruction": "Inject at same time each evening (recommend 9 PM). Rotate injection sites (thighs, abdomen, upper arms). Do not shake pen - roll gently between palms if needed. Store unused pens in refrigerator. In-use pen can be stored at room temperature for up to 28 days. Check blood glucose before injection.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["21:00"]
                                }
                            },
                            "site": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "78904004",
                                    "display": "Subcutaneous tissue structure"
                                }]
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "34206005",
                                    "display": "Subcutaneous route"
                                }]
                            },
                            "doseAndRate": [{
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 28,
                                    "unit": "units",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "U"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 5, "unit": "pen"},
                            "expectedSupplyDuration": {"value": 90, "unit": "d"}
                        }
                    }
                },
                # Insulin Lispro - Rapid-acting mealtime insulin
                {
                    "fullUrl": "MedicationRequest/insulin-lispro-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "insulin-lispro-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "285018",
                                "display": "Insulin Lispro 100 unit/mL Pen Injector"
                            }],
                            "text": "Humalog (insulin lispro) 100 units/mL pen injector"
                        },
                        "subject": {"reference": "Patient/diabetes-patient-comprehensive"},
                        "authoredOn": "2024-01-15T10:40:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-001",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Inject subcutaneously 15 minutes before meals based on carbohydrate content and blood glucose level",
                            "patientInstruction": "CARBOHYDRATE RATIO: 1 unit per 12 grams of carbohydrates. CORRECTION FACTOR: Add correction units based on blood glucose: 151-180 mg/dL: +2 units, 181-220 mg/dL: +4 units, 221-260 mg/dL: +6 units, 261-300 mg/dL: +8 units, >300 mg/dL: call provider immediately. Inject 15 minutes before eating. Typical doses: breakfast 8-12 units, lunch 6-10 units, dinner 10-14 units (adjust based on carb counting).",
                            "timing": {
                                "repeat": {
                                    "frequency": 3,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "when": ["AC"]  # before meals
                                }
                            },
                            "asNeeded": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "226553002",
                                    "display": "Carbohydrate intake"
                                }],
                                "text": "based on carbohydrate content and blood glucose"
                            },
                            "site": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "78904004",
                                    "display": "Subcutaneous tissue structure"
                                }]
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "34206005",
                                    "display": "Subcutaneous route"
                                }]
                            },
                            "doseAndRate": [{
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "calculated",
                                        "display": "Calculated"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 10,  # Average dose for calculation
                                    "unit": "units",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "U"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 5, "unit": "pen"},
                            "expectedSupplyDuration": {"value": 90, "unit": "d"}
                        }
                    }
                },
                # Lisinopril - ACE inhibitor for diabetic nephropathy protection
                {
                    "fullUrl": "MedicationRequest/lisinopril-diabetes-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "lisinopril-diabetes-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197361",
                                "display": "Lisinopril 10 MG Oral Tablet"
                            }],
                            "text": "Lisinopril 10mg tablets"
                        },
                        "subject": {"reference": "Patient/diabetes-patient-comprehensive"},
                        "authoredOn": "2024-01-15T10:45:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-001",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "127013003",
                                "display": "Diabetic nephropathy"
                            }],
                            "text": "Diabetic kidney disease protection and blood pressure control"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Take 1 tablet by mouth once daily in the morning",
                            "patientInstruction": "Take in morning with or without food. Monitor blood pressure regularly. Report persistent dry cough, swelling of face/lips/tongue (angioedema), dizziness, or kidney function changes. Avoid potassium supplements unless directed by provider.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["08:00"]
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
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 30, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def create_pediatric_asthma_bundle() -> Dict[str, Any]:
        """
        Create pediatric asthma management bundle.
        
        Patient: 8-year-old with moderate persistent asthma
        - Albuterol inhaler (rescue)
        - Fluticasone inhaler (controller)
        - Weight-based dosing considerations
        """
        return {
            "resourceType": "Bundle",
            "id": "pediatric-asthma-001",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat(),
            "entry": [
                {
                    "fullUrl": "Patient/pediatric-asthma-patient",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pediatric-asthma-patient",
                        "name": [{"family": "AsthmaChild", "given": ["Tommy"]}],
                        "gender": "male",
                        "birthDate": "2015-08-10",  # 8 years old
                        "identifier": [{"value": "PEDS-ASTHMA-001"}],
                        "extension": [{
                            "url": "http://hl7.org/fhir/StructureDefinition/patient-weight",
                            "valueQuantity": {"value": 28, "unit": "kg"}
                        }]
                    }
                },
                # Albuterol - Rescue inhaler
                {
                    "fullUrl": "MedicationRequest/albuterol-pediatric-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "albuterol-pediatric-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "630208",
                                "display": "Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler"
                            }],
                            "text": "ProAir HFA (albuterol sulfate) 90 mcg/actuation inhaler"
                        },
                        "subject": {"reference": "Patient/pediatric-asthma-patient"},
                        "authoredOn": "2024-01-20T14:15:00Z",
                        "requester": {
                            "reference": "Practitioner/pediatric-pulmonologist-001",
                            "display": "Dr. Michael Chen, Pediatric Pulmonology"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "195967001",
                                "display": "Asthma"
                            }],
                            "text": "Moderate persistent asthma - rescue medication"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Inhale 2 puffs by mouth every 4-6 hours as needed for wheezing, shortness of breath, or cough",
                            "patientInstruction": "PEDIATRIC INSTRUCTIONS: Adult must supervise administration. Shake inhaler 5 times before each use. Use spacer device (AeroChamber) for better delivery. Child should breathe slowly and deeply through spacer for 5-10 breaths after actuation. Wait 1 minute between puffs. Rinse mouth after use. If needing more than 2-3 times per week, contact provider. If no improvement after 2 puffs, seek emergency care.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 4,
                                    "periodUnit": "h",
                                    "frequencyMax": 6
                                }
                            },
                            "asNeeded": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "56018004",
                                    "display": "Wheezing"
                                }],
                                "text": "wheezing, shortness of breath, or cough"
                            },
                            "route": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "26643006",
                                    "display": "Inhalation route"
                                }]
                            },
                            "method": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "421984009",
                                    "display": "Inhalation with metered dose inhaler and spacer"
                                }]
                            },
                            "doseAndRate": [{
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 2,
                                    "unit": "puff",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{puff}"
                                }
                            }],
                            "maxDosePerPeriod": {
                                "numerator": {"value": 12, "unit": "puff"},
                                "denominator": {"value": 24, "unit": "h"}
                            }
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 1, "unit": "inhaler"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                },
                # Fluticasone - Controller medication
                {
                    "fullUrl": "MedicationRequest/fluticasone-pediatric-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "fluticasone-pediatric-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "895994",
                                "display": "Fluticasone Propionate 0.044 MG/ACTUAT Metered Dose Inhaler"
                            }],
                            "text": "Flovent HFA (fluticasone propionate) 44 mcg/actuation inhaler"
                        },
                        "subject": {"reference": "Patient/pediatric-asthma-patient"},
                        "authoredOn": "2024-01-20T14:20:00Z",
                        "requester": {
                            "reference": "Practitioner/pediatric-pulmonologist-001",
                            "display": "Dr. Michael Chen, Pediatric Pulmonology"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "195967001",
                                "display": "Asthma"
                            }],
                            "text": "Moderate persistent asthma - daily controller therapy"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Inhale 2 puffs by mouth twice daily (morning and evening)",
                            "patientInstruction": "PEDIATRIC CONTROLLER MEDICATION: Must use DAILY even when feeling well - this prevents asthma attacks. Adult supervision required. Shake inhaler 5 times before use. Use with spacer device. Wait 1 minute between puffs. Rinse mouth and spit out water after each use to prevent thrush. This is NOT a rescue medication - use albuterol for acute symptoms.",
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
                                    "display": "Inhalation route"
                                }]
                            },
                            "method": {
                                "coding": [{
                                    "system": "http://snomed.info/sct",
                                    "code": "421984009",
                                    "display": "Inhalation with metered dose inhaler and spacer"
                                }]
                            },
                            "doseAndRate": [{
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 2,
                                    "unit": "puff",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{puff}"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 1, "unit": "inhaler"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def create_geriatric_polypharmacy_bundle() -> Dict[str, Any]:
        """
        Create geriatric polypharmacy bundle with medication interactions.
        
        Patient: 78-year-old with multiple conditions
        - Heart failure medications
        - Diabetes medications  
        - Osteoporosis treatment
        - Depression management
        - Potential drug interactions requiring monitoring
        """
        return {
            "resourceType": "Bundle",
            "id": "geriatric-polypharmacy-001",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat(),
            "entry": [
                {
                    "fullUrl": "Patient/geriatric-patient-001",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "geriatric-patient-001",
                        "name": [{"family": "ElderlyPatient", "given": ["Eleanor"]}],
                        "gender": "female",
                        "birthDate": "1945-11-22",  # 78 years old
                        "identifier": [{"value": "GER-POLY-001"}],
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/patient-weight",
                                "valueQuantity": {"value": 62, "unit": "kg"}
                            },
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/patient-creatinine-clearance",
                                "valueQuantity": {"value": 45, "unit": "mL/min"}  # Reduced kidney function
                            }
                        ]
                    }
                },
                # Digoxin - Heart failure (narrow therapeutic window)
                {
                    "fullUrl": "MedicationRequest/digoxin-geriatric-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "digoxin-geriatric-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "197604",
                                "display": "Digoxin 0.125 MG Oral Tablet"
                            }],
                            "text": "Digoxin 0.125mg (125 mcg) tablets"
                        },
                        "subject": {"reference": "Patient/geriatric-patient-001"},
                        "authoredOn": "2024-02-01T09:00:00Z",
                        "requester": {
                            "reference": "Practitioner/cardiologist-001",
                            "display": "Dr. Robert Martinez, Cardiology"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "84114007",
                                "display": "Heart failure"
                            }],
                            "text": "Heart failure with reduced ejection fraction"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Take 1 tablet (0.125 mg) by mouth once daily",
                            "patientInstruction": "CRITICAL MEDICATION: Narrow margin between therapeutic and toxic levels. Take at same time daily. GERIATRIC CONSIDERATIONS: Reduced dose due to age and kidney function. Monitor for signs of toxicity: nausea, vomiting, visual changes (yellow halos), confusion, irregular heartbeat. Regular blood level monitoring required. Many drug interactions - inform all providers of this medication.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["08:00"]
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
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 0.125,
                                    "unit": "mg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mg"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 30, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                },
                # Warfarin - Anticoagulation (many drug interactions)
                {
                    "fullUrl": "MedicationRequest/warfarin-geriatric-001", 
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "warfarin-geriatric-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "855332",
                                "display": "Warfarin Sodium 2.5 MG Oral Tablet"
                            }],
                            "text": "Warfarin sodium 2.5mg tablets"
                        },
                        "subject": {"reference": "Patient/geriatric-patient-001"},
                        "authoredOn": "2024-02-01T09:15:00Z",
                        "requester": {
                            "reference": "Practitioner/cardiologist-001",
                            "display": "Dr. Robert Martinez, Cardiology"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "49436004",
                                "display": "Atrial fibrillation"
                            }],
                            "text": "Atrial fibrillation - stroke prevention"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Take as directed based on INR results: typically 1 tablet (2.5 mg) once daily, adjust per INR monitoring",
                            "patientInstruction": "ANTICOAGULANT - HIGH RISK MEDICATION: Dose adjusted based on weekly INR blood tests. Target INR 2.0-3.0. GERIATRIC PRECAUTIONS: Higher bleeding risk, more frequent monitoring. Maintain consistent vitamin K intake (leafy greens). Avoid alcohol excess. Report any unusual bleeding, bruising, dark stools, or blood in urine immediately. Many drug and food interactions - check with pharmacist before starting any new medications including over-the-counter drugs.",
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
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "calculated",
                                        "display": "Calculated"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 2.5,
                                    "unit": "mg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mg"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 30, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def create_psychiatric_medication_bundle() -> Dict[str, Any]:
        """
        Create psychiatric medication management bundle.
        
        Patient: 32-year-old with major depressive disorder and anxiety
        - Antidepressant with titration schedule
        - Anti-anxiety medication (controlled substance)
        - Sleep aid
        - Careful monitoring for side effects and drug interactions
        """
        return {
            "resourceType": "Bundle",
            "id": "psychiatric-medications-001",
            "type": "collection",
            "timestamp": datetime.utcnow().isoformat(),
            "entry": [
                {
                    "fullUrl": "Patient/psychiatric-patient-001",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "psychiatric-patient-001",
                        "name": [{"family": "MentalHealthPatient", "given": ["Sarah"]}],
                        "gender": "female",
                        "birthDate": "1991-07-14",  # 32 years old
                        "identifier": [{"value": "PSYCH-001"}]
                    }
                },
                # Sertraline - SSRI antidepressant with titration  
                {
                    "fullUrl": "MedicationRequest/sertraline-psychiatric-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "sertraline-psychiatric-001",
                        "status": "active",
                        "intent": "order",
                        "priority": "routine",
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "312938",
                                "display": "Sertraline Hydrochloride 50 MG Oral Tablet"
                            }],
                            "text": "Sertraline (Zoloft) 50mg tablets"
                        },
                        "subject": {"reference": "Patient/psychiatric-patient-001"},
                        "authoredOn": "2024-02-10T11:30:00Z",
                        "requester": {
                            "reference": "Practitioner/psychiatrist-001",
                            "display": "Dr. Jennifer Park, Psychiatry"
                        },
                        "reasonCode": [{
                            "coding": [{
                                "system": "http://snomed.info/sct",
                                "code": "370143000",
                                "display": "Major depressive disorder"
                            }],
                            "text": "Major depressive disorder, recurrent episode, moderate severity"
                        }],
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "TITRATION SCHEDULE: Week 1-2: Take 25mg (half tablet) once daily. Week 3+: Take 50mg (1 tablet) once daily with food",
                            "patientInstruction": "ANTIDEPRESSANT MEDICATION: Start with lower dose to minimize side effects. Take with food to reduce nausea. Full therapeutic effect may take 4-6 weeks. DO NOT STOP SUDDENLY - must taper gradually. Monitor for worsening depression or suicidal thoughts, especially first few weeks. Common initial side effects: nausea, headache, sleep changes, sexual side effects (usually improve). Contact provider if persistent side effects or mood worsening.",
                            "timing": {
                                "repeat": {
                                    "frequency": 1,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "timeOfDay": ["08:00"]
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
                                "type": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                        "code": "ordered",
                                        "display": "Ordered"
                                    }]
                                },
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }],
                        "dispenseRequest": {
                            "quantity": {"value": 30, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                }
            ]
        }


@pytest.fixture
def diabetes_management_bundle():
    """Fixture for comprehensive diabetes management test data."""
    return ClinicalTestDataFactory.create_diabetes_management_bundle()


@pytest.fixture
def pediatric_asthma_bundle():
    """Fixture for pediatric asthma management test data."""
    return ClinicalTestDataFactory.create_pediatric_asthma_bundle()


@pytest.fixture
def geriatric_polypharmacy_bundle():
    """Fixture for geriatric polypharmacy test data."""
    return ClinicalTestDataFactory.create_geriatric_polypharmacy_bundle()


@pytest.fixture
def psychiatric_medication_bundle():
    """Fixture for psychiatric medication management test data."""
    return ClinicalTestDataFactory.create_psychiatric_medication_bundle()


# Emergency Protocol Test Data
@pytest.fixture
def emergency_protocol_data():
    """Emergency medication protocols for critical care scenarios."""
    return {
        "anaphylaxis_protocol": {
            "resourceType": "MedicationRequest",
            "id": "epinephrine-emergency-001",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "727373",
                    "display": "Epinephrine 0.3 MG/0.3 ML Auto-Injector"
                }],
                "text": "EpiPen (epinephrine) 0.3 mg auto-injector"
            },
            "subject": {"reference": "Patient/emergency-patient-001"},
            "dosageInstruction": [{
                "text": "Inject 0.3 mg intramuscularly in outer thigh immediately for severe allergic reaction (anaphylaxis)",
                "patientInstruction": "EMERGENCY MEDICATION: Use immediately for severe allergic reactions with difficulty breathing, swelling, or severe hives. Remove safety cap, press firmly against outer thigh through clothing for 10 seconds. Call 911 immediately after use. May repeat in 15 minutes if symptoms persist. Seek emergency medical care even if symptoms improve.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 15,
                        "periodUnit": "min",
                        "countMax": 2
                    }
                },
                "asNeeded": {
                    "text": "severe allergic reaction (anaphylaxis)"
                },
                "site": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "68367000",
                        "display": "Thigh structure"
                    }]
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "78421000",
                        "display": "Intramuscular route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 0.3,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg"
                    }
                }]
            }]
        }
    }