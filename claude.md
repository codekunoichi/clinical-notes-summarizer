# Clinical Notes Summarizer - Claude Code Project

## Project Overview

You are helping build a healthcare AI solution that transforms incomprehensible medical summaries into patient-friendly "fridge magnet" summaries. This addresses a real problem where patients can't understand their own medical information.

## Core Approach: Hybrid Structured + AI

**CRITICAL PRINCIPLE:** Never AI-summarize critical medical data. Use AI only for narrative clarity.

### What to PRESERVE EXACTLY (No AI):
- Medication names, dosages, frequencies, instructions
- Lab values, units, reference ranges, results
- Vital signs and measurements  
- Appointment dates, times, locations
- Provider contact information
- Pharmacy addresses and phone numbers
- Insurance information
- Emergency contacts and medical alerts

### What to AI-ENHANCE for Clarity:
- Chief complaint descriptions
- Diagnosis explanations
- Procedure descriptions
- General care instructions
- Lifestyle recommendations
- Warning signs explanations

## Technical Stack

- **Backend:** Python 3.9+ with FastAPI
- **ML/AI:** Hugging Face Transformers (BART model for summarization)
- **Data:** FHIR-compatible JSON input/output
- **Testing:** pytest with comprehensive test coverage
- **Deployment:** Docker with health checks
- **Frontend:** Simple HTML/CSS/JavaScript (no framework)

## Development Approach

Use Test-Driven Development (TDD) with healthcare-specific safety testing:

1. **Write failing tests** for acceptance criteria
2. **Implement minimal code** to pass tests
3. **Refactor** for healthcare compliance and safety
4. **Validate** with real clinical scenarios

### **CRITICAL DEVELOPMENT INSTRUCTIONS**

**⚠️ ALWAYS USE VIRTUAL ENVIRONMENT:**
- **NEVER run Python commands without activating venv first**
- **ALWAYS check if venv is activated before running tests, pip installs, or any Python commands**
- **Required commands before any Python work:**
  ```bash
  source venv/bin/activate  # On macOS/Linux
  # or
  venv\Scripts\activate     # On Windows
  ```

**Test Execution Protocol:**
- Before running `pytest`: Verify venv is activated
- Before `pip install`: Verify venv is activated  
- Before any Python script: Verify venv is activated
- If tests fail due to missing packages, activate venv and install requirements first

**Environment Verification:**
- Check with `which python` should show path with `/venv/`
- Check with `pip list` should show project-specific packages
- If not in venv, STOP and activate it before continuing

**Python Command:**
- **ALWAYS use `python3` command (not `python`) on this machine**
- **ALWAYS use `pip3` command (not `pip`) on this machine**
- Example: `python3 -m pytest` instead of `python -m pytest`

## Safety Requirements

- ⚠️ No PHI storage or logging
- ⚠️ Prominent disclaimers about educational use only  
- ⚠️ Input validation and sanitization
- ⚠️ Error handling for edge cases
- ⚠️ Rate limiting and security measures

## Key Success Metrics

- **Safety:** Zero incidents of incorrect medication/dosage information
- **Accuracy:** >90% preservation of critical clinical information
- **Clarity:** 50% reduction in reading grade level for explanations
- **Performance:** <5 second processing time
- **Usability:** "Fridge magnet" format - concise and scannable

## Integration Goals

Design for easy integration with major EHR systems:
- EPIC MyChart integration examples
- NextGen patient portal compatibility  
- FHIR R4 standard compliance
- Generic REST API for any system

## Open Source Philosophy

This solution will be released under MIT license for maximum healthcare benefit. Focus on:
- Clear documentation for other developers
- Easy deployment and customization
- Educational value for healthcare AI community
- Trust-building through transparency

## Current Development Phase

Starting with core hybrid processing logic and TDD implementation. Follow the agent personas in the `/agents/` folder for role-specific guidance.

---

**Remember:** Healthcare lives depend on accuracy. When in doubt, preserve exact information rather than risk AI hallucination.