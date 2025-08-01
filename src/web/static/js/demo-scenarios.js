/**
 * Clinical Demo Scenarios for Healthcare AI Demonstration
 * 
 * Contains realistic but fictitious clinical scenarios that demonstrate
 * the clinical notes summarizer's capabilities with different patient
 * populations and medical conditions.
 * 
 * All data is de-identified and represents authentic clinical scenarios
 * that healthcare professionals would recognize.
 */

const DemoScenarios = {
    
    /**
     * Comprehensive diabetes management scenario
     * 45-year-old Type 2 diabetic with multiple medications
     */
    diabetes: {
        name: "Diabetes Management",
        description: "Complex diabetes care with multiple medications including insulin",
        patientAge: "45 years old",
        conditions: ["Type 2 Diabetes", "Diabetic Nephropathy", "Dyslipidemia"],
        data: {
            "resourceType": "Bundle",
            "id": "diabetes-comprehensive-demo",
            "type": "collection",
            "timestamp": new Date().toISOString(),
            "entry": [
                {
                    "fullUrl": "Patient/diabetes-patient-demo",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "diabetes-patient-demo",
                        "name": [{"family": "DiabetesDemo", "given": ["Maria"]}],
                        "gender": "female",
                        "birthDate": "1978-03-15",
                        "identifier": [{"value": "DEMO-DIAB-001"}]
                    }
                },
                // Metformin - First-line diabetes medication
                {
                    "fullUrl": "MedicationRequest/metformin-demo-001",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "metformin-demo-001",
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
                        "subject": {"reference": "Patient/diabetes-patient-demo"},
                        "authoredOn": "2024-01-15T10:30:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-demo",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Take 1 tablet by mouth twice daily with breakfast and dinner",
                            "patientInstruction": "Take with food to reduce stomach upset. Continue monitoring blood glucose levels. Report persistent nausea, vomiting, or unusual muscle pain immediately.",
                            "timing": {
                                "repeat": {
                                    "frequency": 2,
                                    "period": 1,
                                    "periodUnit": "d",
                                    "when": ["PCM"]
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
                            "quantity": {"value": 60, "unit": "tablet"},
                            "expectedSupplyDuration": {"value": 30, "unit": "d"}
                        }
                    }
                },
                // Insulin Glargine - Long-acting basal insulin  
                {
                    "fullUrl": "MedicationRequest/insulin-glargine-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "insulin-glargine-demo",
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
                        "subject": {"reference": "Patient/diabetes-patient-demo"},
                        "authoredOn": "2024-01-15T10:35:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-demo",
                            "display": "Dr. Sarah Johnson, Endocrinology"
                        },
                        "dosageInstruction": [{
                            "sequence": 1,
                            "text": "Inject 28 units subcutaneously once daily at bedtime (same time each evening)",
                            "patientInstruction": "Inject at same time each evening (recommend 9 PM). Rotate injection sites (thighs, abdomen, upper arms). Store unused pens in refrigerator. Check blood glucose before injection.",
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
                                "doseQuantity": {
                                    "value": 28,
                                    "unit": "units",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "U"
                                }
                            }]
                        }]
                    }
                },
                // Lisinopril - ACE inhibitor for kidney protection
                {
                    "fullUrl": "MedicationRequest/lisinopril-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "lisinopril-demo",
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
                        "subject": {"reference": "Patient/diabetes-patient-demo"},
                        "authoredOn": "2024-01-15T10:45:00Z",
                        "requester": {
                            "reference": "Practitioner/endocrinologist-demo",
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
                            "patientInstruction": "Take in morning with or without food. Monitor blood pressure regularly. Report persistent dry cough, swelling of face/lips/tongue, or dizziness.",
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
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
    },

    /**
     * Pediatric asthma management scenario
     * 8-year-old child with moderate persistent asthma
     */
    "pediatric-asthma": {
        name: "Pediatric Asthma",
        description: "8-year-old with asthma requiring controller and rescue medications",
        patientAge: "8 years old",
        conditions: ["Moderate Persistent Asthma"],
        data: {
            "resourceType": "Bundle",
            "id": "pediatric-asthma-demo",
            "type": "collection", 
            "timestamp": new Date().toISOString(),
            "entry": [
                {
                    "fullUrl": "Patient/pediatric-asthma-demo",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pediatric-asthma-demo",
                        "name": [{"family": "AsthmaDemo", "given": ["Tommy"]}],
                        "gender": "male",
                        "birthDate": "2015-08-10",
                        "identifier": [{"value": "DEMO-PEDS-001"}],
                        "extension": [{
                            "url": "http://hl7.org/fhir/StructureDefinition/patient-weight",
                            "valueQuantity": {"value": 28, "unit": "kg"}
                        }]
                    }
                },
                // Albuterol - Rescue inhaler
                {
                    "fullUrl": "MedicationRequest/albuterol-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "albuterol-demo",
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
                        "subject": {"reference": "Patient/pediatric-asthma-demo"},
                        "authoredOn": "2024-01-20T14:15:00Z",
                        "requester": {
                            "reference": "Practitioner/pediatric-pulmonologist-demo",
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
                            "patientInstruction": "PEDIATRIC INSTRUCTIONS: Adult must supervise. Shake inhaler 5 times before use. Use spacer device for better delivery. Wait 1 minute between puffs. Rinse mouth after use. If no improvement after 2 puffs, seek emergency care.",
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
                                "doseQuantity": {
                                    "value": 2,
                                    "unit": "puff",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{puff}"
                                }
                            }]
                        }]
                    }
                },
                // Fluticasone - Controller medication
                {
                    "fullUrl": "MedicationRequest/fluticasone-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "fluticasone-demo",
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
                        "subject": {"reference": "Patient/pediatric-asthma-demo"},
                        "authoredOn": "2024-01-20T14:20:00Z",
                        "requester": {
                            "reference": "Practitioner/pediatric-pulmonologist-demo",
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
                            "patientInstruction": "CONTROLLER MEDICATION: Must use DAILY even when feeling well - prevents asthma attacks. Adult supervision required. Use with spacer device. Rinse mouth after each use to prevent thrush. This is NOT a rescue medication.",
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
                            "doseAndRate": [{
                                "doseQuantity": {
                                    "value": 2,
                                    "unit": "puff",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{puff}"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
    },

    /**
     * Geriatric polypharmacy scenario
     * 78-year-old with multiple conditions and potential drug interactions
     */
    "geriatric-polypharmacy": {
        name: "Geriatric Polypharmacy",
        description: "78-year-old with heart failure, diabetes, and multiple medications",
        patientAge: "78 years old", 
        conditions: ["Heart Failure", "Atrial Fibrillation", "Type 2 Diabetes"],
        data: {
            "resourceType": "Bundle",
            "id": "geriatric-polypharmacy-demo",
            "type": "collection",
            "timestamp": new Date().toISOString(),
            "entry": [
                {
                    "fullUrl": "Patient/geriatric-demo",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "geriatric-demo",
                        "name": [{"family": "ElderlyDemo", "given": ["Eleanor"]}],
                        "gender": "female",
                        "birthDate": "1945-11-22",
                        "identifier": [{"value": "DEMO-GER-001"}],
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/patient-weight",
                                "valueQuantity": {"value": 62, "unit": "kg"}
                            },
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/patient-creatinine-clearance",
                                "valueQuantity": {"value": 45, "unit": "mL/min"}
                            }
                        ]
                    }
                },
                // Digoxin - Heart failure (narrow therapeutic window)
                {
                    "fullUrl": "MedicationRequest/digoxin-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "digoxin-demo",
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
                        "subject": {"reference": "Patient/geriatric-demo"},
                        "authoredOn": "2024-02-01T09:00:00Z",
                        "requester": {
                            "reference": "Practitioner/cardiologist-demo",
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
                            "patientInstruction": "CRITICAL MEDICATION: Take at same time daily. GERIATRIC CONSIDERATIONS: Reduced dose due to age and kidney function. Monitor for signs of toxicity: nausea, vomiting, visual changes, confusion, irregular heartbeat. Regular blood level monitoring required.",
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
                                "doseQuantity": {
                                    "value": 0.125,
                                    "unit": "mg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mg"
                                }
                            }]
                        }]
                    }
                },
                // Warfarin - Anticoagulation  
                {
                    "fullUrl": "MedicationRequest/warfarin-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "warfarin-demo",
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
                        "subject": {"reference": "Patient/geriatric-demo"},
                        "authoredOn": "2024-02-01T09:15:00Z",
                        "requester": {
                            "reference": "Practitioner/cardiologist-demo",
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
                            "text": "Take as directed based on INR results: typically 1 tablet (2.5 mg) once daily",
                            "patientInstruction": "ANTICOAGULANT - HIGH RISK: Dose adjusted based on weekly INR blood tests. Target INR 2.0-3.0. GERIATRIC PRECAUTIONS: Higher bleeding risk. Maintain consistent vitamin K intake. Report any unusual bleeding, bruising, or dark stools immediately.",
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
                                    "value": 2.5,
                                    "unit": "mg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mg"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
    },

    /**
     * Psychiatric medication scenario
     * 32-year-old with depression and anxiety
     */
    psychiatric: {
        name: "Psychiatric Medications",
        description: "32-year-old with major depressive disorder and anxiety management",
        patientAge: "32 years old",
        conditions: ["Major Depressive Disorder", "Generalized Anxiety Disorder"],
        data: {
            "resourceType": "Bundle",
            "id": "psychiatric-medications-demo",
            "type": "collection",
            "timestamp": new Date().toISOString(),
            "entry": [
                {
                    "fullUrl": "Patient/psychiatric-demo",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "psychiatric-demo",
                        "name": [{"family": "MentalHealthDemo", "given": ["Sarah"]}],
                        "gender": "female",
                        "birthDate": "1991-07-14",
                        "identifier": [{"value": "DEMO-PSYCH-001"}]
                    }
                },
                // Sertraline - SSRI antidepressant
                {
                    "fullUrl": "MedicationRequest/sertraline-demo",
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "sertraline-demo",
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
                        "subject": {"reference": "Patient/psychiatric-demo"},
                        "authoredOn": "2024-02-10T11:30:00Z",
                        "requester": {
                            "reference": "Practitioner/psychiatrist-demo",
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
                            "patientInstruction": "ANTIDEPRESSANT: Start with lower dose to minimize side effects. Take with food to reduce nausea. Full effect may take 4-6 weeks. DO NOT STOP SUDDENLY. Monitor for worsening depression or suicidal thoughts. Contact provider if persistent side effects.",
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
                                "doseQuantity": {
                                    "value": 1,
                                    "unit": "tablet",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "{tbl}"
                                }
                            }]
                        }]
                    }
                }
            ]
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DemoScenarios;
}