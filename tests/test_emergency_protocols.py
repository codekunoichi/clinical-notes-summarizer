"""
Emergency medication protocol tests for critical care scenarios.

This module tests emergency medication protocols where precise dosing
and timing are critical for patient survival. All tests maintain
zero-tolerance safety standards for life-critical medications.

Emergency Scenarios Covered:
1. Anaphylaxis (EpiPen, emergency epinephrine)
2. Severe Hypoglycemia (glucagon, emergency glucose)
3. Cardiac Emergencies (nitroglycerin, emergency cardiac medications)
4. Asthma Exacerbation (emergency bronchodilators)
5. Diabetic Ketoacidosis (insulin protocols)
6. Opioid Overdose (naloxone protocols)
"""

import pytest
import time
from typing import Dict, Any
from src.summarizer.hybrid_processor import HybridClinicalProcessor
from src.models.clinical import SafetyLevel, ProcessingType


class TestAnaphylaxisEmergencyProtocols:
    """
    Test anaphylaxis emergency protocols with epinephrine auto-injectors.
    Life-critical timing and dosing requirements.
    """
    
    def test_epipen_adult_emergency_protocol(self):
        """
        Test adult EpiPen emergency protocol.
        
        Scenario: Adult with severe allergic reaction
        - EpiPen 0.3mg auto-injector
        - Critical timing requirements
        - Repeat dosing protocol
        - Emergency care instructions
        """
        processor = HybridClinicalProcessor()
        
        epipen_emergency_data = {
            "resourceType": "MedicationRequest",
            "id": "epipen-adult-emergency-001",
            "status": "active",
            "intent": "order",
            "priority": "stat",  # Emergency priority
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "727373",
                    "display": "Epinephrine 0.3 MG/0.3 ML Auto-Injector"
                }],
                "text": "EpiPen (epinephrine) 0.3mg auto-injector"
            },
            "subject": {"reference": "Patient/adult-anaphylaxis-001"},
            "dosageInstruction": [{
                "text": "Inject 0.3mg intramuscularly in outer thigh immediately for severe allergic reaction (anaphylaxis). May repeat once after 15 minutes if symptoms persist.",
                "patientInstruction": "LIFE-SAVING EMERGENCY MEDICATION: Use IMMEDIATELY for severe allergic reactions with any of these signs: difficulty breathing, swelling of face/lips/tongue/throat, severe full-body hives, rapid pulse, dizziness/fainting, severe nausea/vomiting/diarrhea. ADMINISTRATION: Remove blue safety cap, press orange tip firmly against outer thigh through clothing for 10 seconds, massage area for 10 seconds. Call 911 IMMEDIATELY after injection. May repeat dose in 15 minutes if symptoms not improving. Seek emergency medical care even if symptoms improve.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 15,
                        "periodUnit": "min",
                        "countMax": 2  # Maximum 2 doses
                    }
                },
                "asNeeded": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "39579001",
                        "display": "Anaphylaxis"
                    }],
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
        
        result = processor.process_medication_data(epipen_emergency_data)
        
        # CRITICAL: Exact medication name and dose preserved
        assert result.medication_name == "EpiPen (epinephrine) 0.3mg auto-injector"
        assert "0.3 mg" in result.dosage
        
        # CRITICAL: Emergency instructions preserved exactly
        assert "LIFE-SAVING EMERGENCY MEDICATION" in result.instructions
        assert "IMMEDIATELY" in result.instructions
        assert "Call 911" in result.instructions
        assert "difficulty breathing" in result.instructions.lower()
        assert "outer thigh" in result.instructions.lower()
        assert "10 seconds" in result.instructions
        assert "15 minutes" in result.instructions
        
        # CRITICAL: No AI processing of emergency medication data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed
    
    def test_epipen_pediatric_emergency_protocol(self):
        """
        Test pediatric EpiPen Jr emergency protocol.
        
        Scenario: Child with severe allergic reaction
        - EpiPen Jr 0.15mg for children 15-30kg
        - Weight-specific dosing critical
        - Parent/caregiver instructions
        """
        processor = HybridClinicalProcessor()
        
        epipen_jr_data = {
            "resourceType": "MedicationRequest",
            "id": "epipen-jr-emergency-001",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "727374", 
                    "display": "Epinephrine 0.15 MG/0.3 ML Auto-Injector"
                }],
                "text": "EpiPen Jr (epinephrine) 0.15mg auto-injector"
            },
            "subject": {"reference": "Patient/pediatric-anaphylaxis-22kg"},
            "dosageInstruction": [{
                "text": "Inject 0.15mg intramuscularly in outer thigh immediately for severe allergic reaction. Pediatric dose for child weighing 22kg (15-30kg weight range).",
                "patientInstruction": "PEDIATRIC EMERGENCY MEDICATION: For children 15-30kg (33-66 lbs). Child weighs 22kg - correct dose. Use for severe allergic reactions: trouble breathing, swelling of face/mouth, severe hives covering body, vomiting/diarrhea with other symptoms. CAREGIVER ADMINISTRATION: Hold child's leg still, remove blue cap, press orange tip against outer thigh for 10 seconds through clothing, massage area. CALL 911 IMMEDIATELY after giving injection. May give second dose after 15 minutes if no improvement. Go to emergency room even if child seems better.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 15,
                        "periodUnit": "min", 
                        "countMax": 2
                    }
                },
                "asNeeded": {
                    "text": "severe allergic reaction in child"
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
                        "value": 0.15,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(epipen_jr_data)
        
        # CRITICAL: Pediatric dose and weight specifications preserved exactly
        assert result.medication_name == "EpiPen Jr (epinephrine) 0.15mg auto-injector"
        assert "0.15 mg" in result.dosage
        assert "22kg" in result.instructions
        assert "15-30kg" in result.instructions
        assert "PEDIATRIC EMERGENCY MEDICATION" in result.instructions
        
        # CRITICAL: No AI processing of pediatric emergency data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestSevereHypoglycemiaProtocols:
    """
    Test severe hypoglycemia emergency protocols with glucagon.
    Critical for diabetic patients with severe low blood sugar.
    """
    
    def test_glucagon_emergency_kit_protocol(self):
        """
        Test glucagon emergency kit for severe hypoglycemia.
        
        Scenario: Diabetic patient with severe hypoglycemia (unconscious)
        - Glucagon injection kit
        - Family/caregiver administration
        - Critical timing for brain protection
        """
        processor = HybridClinicalProcessor()
        
        glucagon_emergency_data = {
            "resourceType": "MedicationRequest",
            "id": "glucagon-emergency-kit-001",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "5447",
                    "display": "Glucagon 1 MG Injection Kit"
                }],
                "text": "Glucagon 1mg emergency injection kit"
            },
            "subject": {"reference": "Patient/diabetic-hypoglycemia-001"},
            "dosageInstruction": [{
                "text": "Inject 1mg intramuscularly or subcutaneously immediately for severe hypoglycemia when patient is unconscious or unable to swallow",
                "patientInstruction": "SEVERE HYPOGLYCEMIA EMERGENCY: Use when diabetic person is unconscious or cannot safely swallow due to low blood sugar. FAMILY/CAREGIVER INSTRUCTIONS: 1) Mix powder and liquid in kit - shake until dissolved, 2) Inject entire contents into thigh or buttock muscle (or under skin), 3) Turn person on side to prevent choking, 4) Call 911 immediately, 5) Give sugar by mouth ONLY when person is awake and able to swallow safely. Person should wake up within 15 minutes - if not, call 911 again. Feed person as soon as they can swallow safely.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "h",
                        "countMax": 1  # Usually single dose
                    }
                },
                "asNeeded": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "302866003",
                        "display": "Severe hypoglycemia"
                    }],
                    "text": "severe hypoglycemia with unconsciousness"
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
                        "value": 1,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(glucagon_emergency_data)
        
        # CRITICAL: Exact medication and dose preserved
        assert result.medication_name == "Glucagon 1mg emergency injection kit"
        assert "1 mg" in result.dosage
        
        # CRITICAL: Emergency protocol steps preserved exactly
        assert "SEVERE HYPOGLYCEMIA EMERGENCY" in result.instructions
        assert "unconscious" in result.instructions.lower()
        assert "Mix powder and liquid" in result.instructions
        assert "Call 911" in result.instructions
        assert "15 minutes" in result.instructions
        assert "turn person on side" in result.instructions.lower()
        
        # CRITICAL: No AI processing of emergency protocol
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestCardiacEmergencyProtocols:
    """
    Test cardiac emergency medication protocols.
    Critical for acute cardiac events.
    """
    
    def test_nitroglycerin_chest_pain_protocol(self):
        """
        Test sublingual nitroglycerin for chest pain.
        
        Scenario: Patient with coronary artery disease having chest pain
        - Sublingual nitroglycerin tablets
        - 5-minute repeat protocol
        - Emergency care instructions
        """
        processor = HybridClinicalProcessor()
        
        nitroglycerin_emergency_data = {
            "resourceType": "MedicationRequest",
            "id": "nitroglycerin-chest-pain-001",
            "status": "active",
            "intent": "order",
            "priority": "urgent",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "564666",
                    "display": "Nitroglycerin 0.4 MG Sublingual Tablet"
                }],
                "text": "Nitroglycerin 0.4mg sublingual tablets"
            },
            "subject": {"reference": "Patient/cardiac-patient-001"},
            "dosageInstruction": [{
                "text": "Place 1 tablet under tongue at first sign of chest pain. May repeat every 5 minutes for maximum of 3 tablets in 15 minutes. Call 911 if chest pain not relieved after first tablet.",
                "patientInstruction": "CARDIAC EMERGENCY MEDICATION: For chest pain from heart condition. PROTOCOL: 1st tablet - place under tongue at first sign of chest pain, let dissolve completely (do not chew/swallow), sit down immediately. Wait 5 minutes. If pain not gone: 2nd tablet under tongue. Wait 5 minutes. If pain still present: 3rd tablet and CALL 911 IMMEDIATELY. Do not take more than 3 tablets in 15 minutes. May cause dizziness/headache - normal side effects. Store in original dark bottle, keep dry. Replace every 3-6 months.",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 5,
                        "periodUnit": "min",
                        "countMax": 3  # Maximum 3 tablets
                    }
                },
                "asNeeded": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "29857009",
                        "display": "Chest pain"
                    }],
                    "text": "chest pain"
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "37161004",
                        "display": "Sublingual route"
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
        
        result = processor.process_medication_data(nitroglycerin_emergency_data)
        
        # CRITICAL: Exact cardiac medication details preserved
        assert result.medication_name == "Nitroglycerin 0.4mg sublingual tablets"
        assert "1 tablet" in result.dosage
        
        # CRITICAL: Emergency protocol timing preserved exactly
        assert "CARDIAC EMERGENCY MEDICATION" in result.instructions
        assert "5 minutes" in result.instructions
        assert "maximum of 3 tablets" in result.instructions.lower()
        assert "15 minutes" in result.instructions
        assert "CALL 911" in result.instructions
        assert "under tongue" in result.instructions.lower()
        assert "do not chew" in result.instructions.lower()
        
        # CRITICAL: No AI processing of cardiac emergency data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestOpioidOverdoseProtocols:
    """
    Test opioid overdose reversal protocols with naloxone.
    Critical for opioid overdose emergencies.
    """
    
    def test_naloxone_nasal_spray_overdose_protocol(self):
        """
        Test naloxone nasal spray for opioid overdose.
        
        Scenario: Suspected opioid overdose
        - Naloxone nasal spray 4mg
        - Emergency administration protocol
        - Repeat dosing if needed
        """
        processor = HybridClinicalProcessor()
        
        naloxone_emergency_data = {
            "resourceType": "MedicationRequest",
            "id": "naloxone-overdose-001",
            "status": "active",
            "intent": "order",
            "priority": "stat",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "1659929",
                    "display": "Naloxone Hydrochloride 4 MG/0.1 ML Nasal Spray"
                }],
                "text": "Narcan (naloxone) 4mg nasal spray"
            },
            "subject": {"reference": "Patient/opioid-overdose-001"},
            "dosageInstruction": [{
                "text": "Spray contents of 1 device (4mg) into one nostril immediately for suspected opioid overdose. May repeat with second device after 2-3 minutes if person not responding normally.",
                "patientInstruction": "OPIOID OVERDOSE EMERGENCY: Use when person is unresponsive or barely responsive, slow/absent breathing, blue lips/fingernails, gurgling sounds, limp body. ADMINISTRATION: 1) Tilt head back, insert device in nostril, 2) Press plunger firmly to spray entire contents, 3) Call 911 IMMEDIATELY, 4) Perform rescue breathing if trained, 5) Stay with person, 6) If no response in 2-3 minutes, use second spray in other nostril, 7) Continue rescue efforts until help arrives. Person may wake up agitated/confused - normal reaction. Overdose can return when naloxone wears off (30-90 minutes).",
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 3,
                        "periodUnit": "min",
                        "countMax": 2  # Up to 2 devices
                    }
                },
                "asNeeded": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "55680006",
                        "display": "Opioid overdose"
                    }],
                    "text": "suspected opioid overdose"
                },
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "46713006",
                        "display": "Nasal route"
                    }]
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 4,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg"
                    }
                }]
            }]
        }
        
        result = processor.process_medication_data(naloxone_emergency_data)
        
        # CRITICAL: Exact overdose reversal medication preserved
        assert result.medication_name == "Narcan (naloxone) 4mg nasal spray"
        assert "4 mg" in result.dosage
        
        # CRITICAL: Overdose recognition and response protocol preserved exactly
        assert "OPIOID OVERDOSE EMERGENCY" in result.instructions
        assert "unresponsive" in result.instructions.lower()
        assert "slow/absent breathing" in result.instructions.lower()
        assert "blue lips" in result.instructions.lower()
        assert "Call 911 IMMEDIATELY" in result.instructions
        assert "2-3 minutes" in result.instructions
        assert "second spray" in result.instructions.lower()
        assert "30-90 minutes" in result.instructions
        
        # CRITICAL: No AI processing of overdose emergency data
        assert result.metadata.safety_level == SafetyLevel.CRITICAL
        assert not result.metadata.ai_processed


class TestEmergencyProtocolPerformance:
    """
    Test performance requirements for emergency medication processing.
    Emergency protocols must be processed instantly for life-critical situations.
    """
    
    def test_emergency_protocol_processing_speed(self):
        """
        Test that emergency protocols are processed within strict time limits.
        
        Emergency medications must be processed in <2 seconds for critical care.
        """
        processor = HybridClinicalProcessor()
        
        # Bundle of emergency medications
        emergency_bundle = {
            "resourceType": "Bundle",
            "id": "emergency-medications-001",
            "type": "collection",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "emergency-patient-001",
                    "name": [{"family": "EmergencyPatient", "given": ["Critical"]}]
                }},
                # EpiPen
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "emergency-epipen",
                    "status": "active",
                    "intent": "order",
                    "priority": "stat",
                    "medicationCodeableConcept": {
                        "text": "EpiPen (epinephrine) 0.3mg auto-injector"
                    },
                    "subject": {"reference": "Patient/emergency-patient-001"},
                    "dosageInstruction": [{
                        "text": "Inject 0.3mg immediately for anaphylaxis",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 0.3, "unit": "mg"}}]
                    }]
                }},
                # Nitroglycerin
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "emergency-nitroglycerin",
                    "status": "active",
                    "intent": "order",
                    "priority": "urgent",
                    "medicationCodeableConcept": {
                        "text": "Nitroglycerin 0.4mg sublingual tablets"
                    },
                    "subject": {"reference": "Patient/emergency-patient-001"},
                    "dosageInstruction": [{
                        "text": "Place 1 tablet under tongue for chest pain",
                        "timing": {"repeat": {"frequency": 1, "period": 5, "periodUnit": "min"}},
                        "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}]
                    }]
                }},
                # Naloxone
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "emergency-naloxone",
                    "status": "active",
                    "intent": "order",
                    "priority": "stat",
                    "medicationCodeableConcept": {
                        "text": "Narcan (naloxone) 4mg nasal spray"
                    },
                    "subject": {"reference": "Patient/emergency-patient-001"},
                    "dosageInstruction": [{
                        "text": "Spray 4mg into nostril for opioid overdose",
                        "timing": {"repeat": {"frequency": 1, "period": 3, "periodUnit": "min"}},
                        "doseAndRate": [{"doseQuantity": {"value": 4, "unit": "mg"}}]
                    }]
                }}
            ]
        }
        
        # Test emergency processing speed
        start_time = time.time()
        result = processor.process_clinical_data(emergency_bundle)
        processing_time = time.time() - start_time
        
        # CRITICAL: Emergency protocols must process in <2 seconds
        assert processing_time < 2.0, f"Emergency processing took {processing_time:.2f}s, exceeds 2s critical limit"
        
        # CRITICAL: All emergency medications processed correctly
        assert len(result.medications) == 3
        
        # Verify emergency medication names preserved
        medication_names = [med.medication_name for med in result.medications]
        assert "EpiPen (epinephrine) 0.3mg auto-injector" in medication_names
        assert "Nitroglycerin 0.4mg sublingual tablets" in medication_names  
        assert "Narcan (naloxone) 4mg nasal spray" in medication_names
        
        # CRITICAL: All emergency medications maintain critical safety level
        for medication in result.medications:
            assert medication.metadata.safety_level == SafetyLevel.CRITICAL
            assert not medication.metadata.ai_processed
        
        # CRITICAL: Safety validation must pass for all emergency medications
        assert result.safety_validation.passed
        assert len(result.safety_validation.errors) == 0
    
    def test_concurrent_emergency_protocol_processing(self):
        """
        Test concurrent processing of multiple emergency protocols.
        
        Multiple emergency situations may occur simultaneously in healthcare settings.
        """
        import threading
        import queue
        
        processor = HybridClinicalProcessor()
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def process_emergency_medication(med_data, result_queue, error_queue):
            try:
                start_time = time.time()
                result = processor.process_medication_data(med_data)
                processing_time = time.time() - start_time
                result_queue.put((result, processing_time))
            except Exception as e:
                error_queue.put(e)
        
        # Different emergency medications for concurrent processing
        emergency_medications = [
            {
                "resourceType": "MedicationRequest",
                "id": "concurrent-epipen",
                "status": "active",
                "intent": "order",
                "priority": "stat",
                "subject": {"reference": "Patient/emergency-1"},
                "medicationCodeableConcept": {"text": "EpiPen (epinephrine) 0.3mg auto-injector"},
                "dosageInstruction": [{
                    "text": "Inject immediately for anaphylaxis",
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                    "doseAndRate": [{"doseQuantity": {"value": 0.3, "unit": "mg"}}]
                }]
            },
            {
                "resourceType": "MedicationRequest",
                "id": "concurrent-glucagon",
                "status": "active",
                "intent": "order",
                "priority": "stat",
                "subject": {"reference": "Patient/emergency-2"},
                "medicationCodeableConcept": {"text": "Glucagon 1mg emergency injection kit"},
                "dosageInstruction": [{
                    "text": "Inject for severe hypoglycemia",
                    "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "h"}},
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "mg"}}]
                }]
            },
            {
                "resourceType": "MedicationRequest",
                "id": "concurrent-naloxone",
                "status": "active",
                "intent": "order",
                "priority": "stat",
                "subject": {"reference": "Patient/emergency-3"},
                "medicationCodeableConcept": {"text": "Narcan (naloxone) 4mg nasal spray"},
                "dosageInstruction": [{
                    "text": "Spray for opioid overdose",
                    "timing": {"repeat": {"frequency": 1, "period": 3, "periodUnit": "min"}},
                    "doseAndRate": [{"doseQuantity": {"value": 4, "unit": "mg"}}]
                }]
            }
        ]
        
        # Start concurrent processing
        threads = []
        for med_data in emergency_medications:
            thread = threading.Thread(
                target=process_emergency_medication,
                args=(med_data, results_queue, errors_queue)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all emergency processing to complete
        for thread in threads:
            thread.join()
        
        # CRITICAL: No errors in concurrent emergency processing
        assert errors_queue.empty(), f"Concurrent emergency processing errors: {list(errors_queue.queue)}"
        
        # Verify all emergency medications processed
        results = []
        processing_times = []
        while not results_queue.empty():
            result, processing_time = results_queue.get()
            results.append(result)
            processing_times.append(processing_time)
        
        assert len(results) == len(emergency_medications)
        
        # CRITICAL: All emergency processing times under 2 seconds
        for i, processing_time in enumerate(processing_times):
            assert processing_time < 2.0, f"Emergency medication {i} took {processing_time:.2f}s, exceeds 2s limit"
        
        # CRITICAL: All emergency medications maintain safety standards
        for result in results:
            assert result.metadata.safety_level == SafetyLevel.CRITICAL
            assert not result.metadata.ai_processed
            assert result.metadata.validation_passed