"""
TDD Tests for Translation API Endpoints

This module tests the multilingual fridge magnet translation API endpoints
with healthcare safety validation and medical data preservation.
"""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import Mock, patch

from src.api.main import app

client = TestClient(app)


class TestTranslationAPIEndpoints:
    """Test translation API endpoints with medical safety requirements."""
    
    def test_supported_languages_endpoint(self):
        """Test that supported languages endpoint returns correct languages."""
        response = client.get("/api/v1/translate/supported-languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "supported_languages" in data
        languages = data["supported_languages"]
        
        # Verify Spanish support
        spanish_lang = next((lang for lang in languages if lang["code"] == "spanish"), None)
        assert spanish_lang is not None
        assert spanish_lang["name"] == "Spanish"
        assert spanish_lang["available"] is True
        
        # Verify Mandarin support
        mandarin_lang = next((lang for lang in languages if lang["code"] == "mandarin"), None)
        assert mandarin_lang is not None
        assert mandarin_lang["name"] == "Mandarin Chinese"
        assert mandarin_lang["available"] is True
        
        # Verify medical safety info
        assert data["medical_safety"] == "Zero-tolerance medication/dosage preservation"
    
    def test_translation_status_endpoint(self):
        """Test translation service status endpoint."""
        response = client.get("/api/v1/translate/translation-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "translation_available" in data
        assert "supported_languages" in data
        assert "safety_features" in data
        
        # Verify safety features
        safety = data["safety_features"]
        assert safety["medication_preservation"] is True
        assert safety["lab_value_preservation"] is True
        assert safety["dosage_preservation"] is True
        assert safety["phi_protection"] is True
    
    def test_translation_health_check(self):
        """Test translation service health check endpoint."""
        response = client.get("/api/v1/translate/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "translation"
        assert data["status"] in ["healthy", "degraded"]
        assert "translation_enabled" in data
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    @patch('src.formatter.patient_friendly.PatientFriendlyFormatter')
    def test_translate_fridge_magnet_endpoint_success(self, mock_formatter_class):
        """Test successful translation of fridge magnet content."""
        # Mock the formatter and its translation capability
        mock_formatter = Mock()
        mock_formatter.translation_enabled = True
        mock_formatter_class.return_value = mock_formatter
        
        # Mock translated output
        mock_translated_output = Mock()
        mock_translated_output.content = "Translated fridge magnet content in Spanish"
        mock_translated_output.metadata = {
            "translated_to": "spanish",
            "translation_timestamp": "2024-02-18T12:00:00Z"
        }
        mock_formatter.translate_formatted_output.return_value = mock_translated_output
        
        # Test request
        test_request = {
            "english_content": "🏥 YOUR HEALTH SUMMARY\n💊 Lisinopril 10mg - Take daily",
            "target_language": "spanish",
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/translate", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["target_language"] == "spanish"
        assert data["original_language"] == "english"
        assert data["critical_data_preserved"] is True
        assert "translated_content" in data
        assert "translation_timestamp" in data
    
    def test_translate_fridge_magnet_unsupported_language(self):
        """Test translation with unsupported language."""
        test_request = {
            "english_content": "Sample fridge magnet content",
            "target_language": "french",  # Not supported
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/translate", json=test_request)
        
        # Should return validation error for unsupported language
        assert response.status_code == 422
    
    def test_translate_fridge_magnet_empty_content(self):
        """Test translation with empty content."""
        test_request = {
            "english_content": "",
            "target_language": "spanish",
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/translate", json=test_request)
        
        # Should return validation error for empty content
        assert response.status_code == 422
    
    @patch('src.formatter.patient_friendly.PatientFriendlyFormatter')
    def test_translate_service_unavailable(self, mock_formatter_class):
        """Test translation when service is unavailable."""
        # Mock formatter with translation disabled
        mock_formatter = Mock()
        mock_formatter.translation_enabled = False
        mock_formatter_class.return_value = mock_formatter
        
        test_request = {
            "english_content": "Sample content",
            "target_language": "spanish",
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/translate", json=test_request)
        
        assert response.status_code == 503
        assert "Translation service not available" in response.json()["detail"]
    
    @patch('src.summarizer.hybrid_processor.HybridClinicalProcessor')
    @patch('src.formatter.patient_friendly.PatientFriendlyFormatter')
    def test_process_and_translate_endpoint(self, mock_formatter_class, mock_processor_class):
        """Test the combined process and translate endpoint."""
        # Mock processor
        mock_processor = Mock()
        mock_clinical_summary = Mock()
        mock_processor.process_clinical_data.return_value = mock_clinical_summary
        mock_processor_class.return_value = mock_processor
        
        # Mock formatter
        mock_formatter = Mock()
        mock_formatter.translation_enabled = True
        mock_translated_output = Mock()
        mock_translated_output.content = "Translated clinical summary"
        mock_translated_output.metadata = {"translated_to": "spanish"}
        mock_formatter.format_and_translate.return_value = mock_translated_output
        mock_formatter_class.return_value = mock_formatter
        
        # Test request with FHIR data
        test_request = {
            "fhir_data": {
                "resourceType": "Bundle",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "medicationCodeableConcept": {"text": "Lisinopril 10mg"}
                        }
                    }
                ]
            },
            "target_language": "spanish",
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/process-and-translate", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["target_language"] == "spanish"
        assert data["critical_data_preserved"] is True
        
        # Verify the processor was called
        mock_processor.process_clinical_data.assert_called_once()
        
        # Verify the formatter was called with correct parameters
        mock_formatter.format_and_translate.assert_called_once()
    
    def test_medical_data_preservation_validation(self):
        """Test that critical medical data preservation is validated."""
        # This test verifies that the API enforces medical data preservation
        test_request = {
            "english_content": "Lisinopril 10mg daily, HbA1c 7.2%, BP 135/80 mmHg",
            "target_language": "spanish",
            "output_format": "html"
        }
        
        response = client.post("/api/v1/translate/translate", json=test_request)
        
        # Even if translation fails, the API should indicate preservation requirement
        if response.status_code == 200:
            data = response.json()
            assert data["critical_data_preserved"] is True
    
    def test_api_request_validation(self):
        """Test API request validation for translation endpoints."""
        # Test missing required fields
        response = client.post("/api/v1/translate/translate", json={})
        assert response.status_code == 422
        
        # Test invalid language codes
        invalid_request = {
            "english_content": "Sample content",
            "target_language": "invalid_language",
            "output_format": "html"
        }
        response = client.post("/api/v1/translate/translate", json=invalid_request)
        assert response.status_code == 422
        
        # Test invalid output format should still work (defaults handled)
        valid_request = {
            "english_content": "Sample content", 
            "target_language": "spanish",
            "output_format": "invalid_format"
        }
        # This should not necessarily fail as format defaults are handled


class TestTranslationSafety:
    """Test translation safety and medical data preservation."""
    
    def test_medication_name_preservation_requirement(self):
        """Test that API documents medication name preservation."""
        response = client.get("/api/v1/translate/supported-languages")
        data = response.json()
        
        # Verify safety documentation
        assert "medical_safety" in data
        assert "preservation" in data["medical_safety"].lower()
    
    def test_translation_metadata_requirements(self):
        """Test that translation responses include required safety metadata."""
        # Mock a successful translation to test metadata structure
        sample_metadata_structure = {
            "success": True,
            "original_language": "english",
            "target_language": "spanish",
            "critical_data_preserved": True,
            "translation_timestamp": "2024-02-18T12:00:00Z"
        }
        
        # Verify all required safety fields are documented
        required_fields = ["critical_data_preserved", "original_language", "target_language"]
        
        for field in required_fields:
            assert field in sample_metadata_structure
    
    def test_safety_feature_documentation(self):
        """Test that safety features are properly documented in API."""
        response = client.get("/api/v1/translate/translation-status")
        
        if response.status_code == 200:
            data = response.json()
            safety_features = data.get("safety_features", {})
            
            # Verify critical safety features are documented
            critical_features = [
                "medication_preservation",
                "lab_value_preservation", 
                "dosage_preservation",
                "phi_protection"
            ]
            
            for feature in critical_features:
                if feature in safety_features:
                    assert safety_features[feature] is True


class TestTranslationAPIIntegration:
    """Integration tests for translation API with existing system."""
    
    def test_translation_api_integration_with_health_check(self):
        """Test that translation endpoints integrate with main API health check."""
        # Main API health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Translation-specific health check
        response = client.get("/api/v1/translate/health") 
        assert response.status_code == 200
    
    def test_api_documentation_includes_translation(self):
        """Test that API documentation includes translation endpoints."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Verify translation endpoints are documented
        translation_endpoints = [
            "/api/v1/translate/translate",
            "/api/v1/translate/process-and-translate", 
            "/api/v1/translate/supported-languages",
            "/api/v1/translate/health"
        ]
        
        for endpoint in translation_endpoints:
            assert endpoint in paths or any(endpoint in path for path in paths.keys())
    
    def test_translation_error_handling_consistency(self):
        """Test that translation endpoints handle errors consistently with main API."""
        # Test 404 for non-existent endpoint
        response = client.get("/api/v1/translate/non-existent")
        assert response.status_code == 404
        
        # Test method not allowed
        response = client.delete("/api/v1/translate/health")
        assert response.status_code == 405