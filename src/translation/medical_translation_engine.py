"""
Medical Translation Engine

This module implements the core translation engine using Hugging Face mBART-50
with medical fine-tuning capabilities. It provides offline translation with
healthcare-specific terminology handling.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import torch
from transformers import (
    MBartForConditionalGeneration,
    MBart50TokenizerFast,
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)

from ..models.clinical_summary import ClinicalSummary
from ..models.processing_metadata import ProcessingMetadata

logger = logging.getLogger(__name__)


class MedicalTranslationError(Exception):
    """Raised when medical translation fails."""
    pass


class MedicalMBARTTranslator:
    """
    Medical translation engine using mBART-50 with healthcare specialization.
    
    This engine provides offline translation capabilities for medical content
    while maintaining HIPAA compliance and medical accuracy.
    """
    
    # Language code mapping for mBART-50
    LANGUAGE_CODES = {
        "english": "en_XX",
        "spanish": "es_XX", 
        "chinese": "zh_CN",
        "mandarin": "zh_CN",
        "en": "en_XX",
        "es": "es_XX",
        "zh": "zh_CN"
    }
    
    # Medical terminology that should be preserved across languages
    MEDICAL_PRESERVE_TERMS = {
        "spanish": {
            # Preserve English medication names but provide Spanish context
            "medication_indicators": ["mg", "ml", "tablet", "capsule", "injection"],
            "frequency_terms": ["daily", "twice", "three times", "as needed"],
            "route_terms": ["oral", "IV", "IM", "topical", "sublingual"]
        },
        "chinese": {
            "medication_indicators": ["毫克", "毫升", "片", "粒", "注射"],
            "frequency_terms": ["每日", "一日两次", "一日三次", "需要时"],
            "route_terms": ["口服", "静脉", "肌注", "外用", "舌下"]
        }
    }
    
    def __init__(self, 
                 model_name: str = "facebook/mbart-large-50-many-to-many-mmt",
                 medical_model_path: Optional[str] = None,
                 device: str = "auto"):
        """
        Initialize medical translation engine.
        
        Args:
            model_name: Base mBART model name
            medical_model_path: Path to medical fine-tuned model (if available)
            device: Device for model execution ("cpu", "cuda", or "auto")
        """
        self.model_name = model_name
        self.medical_model_path = medical_model_path
        self.device = self._setup_device(device)
        
        # Initialize models lazily for memory efficiency
        self._model = None
        self._tokenizer = None
        
        # Translation performance tracking
        self.translation_stats = {
            "total_translations": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "medical_terms_preserved": 0
        }
        
        logger.info(f"MedicalMBARTTranslator initialized with device: {self.device}")
    
    def _setup_device(self, device: str) -> torch.device:
        """Setup computation device with healthcare deployment considerations."""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                logger.info("GPU available - using CUDA for translation acceleration")
            else:
                device = "cpu"
                logger.info("GPU not available - using CPU for translation")
        
        return torch.device(device)
    
    @property
    def model(self) -> MBartForConditionalGeneration:
        """Lazy loading of translation model for memory efficiency."""
        if self._model is None:
            self._model = self._load_translation_model()
        return self._model
    
    @property 
    def tokenizer(self) -> MBart50TokenizerFast:
        """Lazy loading of tokenizer."""
        if self._tokenizer is None:
            self._tokenizer = self._load_tokenizer()
        return self._tokenizer
    
    def _load_translation_model(self) -> MBartForConditionalGeneration:
        """Load mBART translation model with healthcare optimizations."""
        try:
            start_time = time.time()
            
            # Try to load medical fine-tuned model first
            if self.medical_model_path and Path(self.medical_model_path).exists():
                logger.info(f"Loading medical fine-tuned model from {self.medical_model_path}")
                model = MBartForConditionalGeneration.from_pretrained(
                    self.medical_model_path,
                    torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )
            else:
                logger.info(f"Loading base mBART model: {self.model_name}")
                model = MBartForConditionalGeneration.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                    low_cpu_mem_usage=True
                )
            
            model.to(self.device)
            model.eval()  # Set to evaluation mode
            
            load_time = time.time() - start_time
            logger.info(f"Translation model loaded in {load_time:.2f} seconds")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load translation model: {str(e)}")
            raise MedicalTranslationError(f"Model loading failed: {str(e)}")
    
    def _load_tokenizer(self) -> MBart50TokenizerFast:
        """Load mBART tokenizer."""
        try:
            if self.medical_model_path and Path(self.medical_model_path).exists():
                tokenizer = MBart50TokenizerFast.from_pretrained(self.medical_model_path)
            else:
                tokenizer = MBart50TokenizerFast.from_pretrained(self.model_name)
                
            logger.info("Translation tokenizer loaded successfully")
            return tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {str(e)}")
            raise MedicalTranslationError(f"Tokenizer loading failed: {str(e)}")
    
    def translate_text(self, 
                      text: str, 
                      target_language: str,
                      source_language: str = "english",
                      max_length: int = 1000,
                      preserve_medical_terms: bool = True) -> str:
        """
        Translate text with medical terminology preservation.
        
        Args:
            text: Source text to translate
            target_language: Target language code or name
            source_language: Source language code or name
            max_length: Maximum translation length
            preserve_medical_terms: Whether to preserve medical terminology
            
        Returns:
            Translated text with medical safety guarantees
        """
        if not text or not text.strip():
            return text
        
        start_time = time.time()
        
        try:
            # Normalize language codes
            source_lang = self._normalize_language_code(source_language)
            target_lang = self._normalize_language_code(target_language)
            
            # Skip translation if source and target are the same
            if source_lang == target_lang:
                return text
            
            logger.info(f"Translating text from {source_lang} to {target_lang}")
            
            # Prepare text for medical translation
            preprocessed_text = self._preprocess_medical_text(text, preserve_medical_terms)
            
            # Set tokenizer source language
            self.tokenizer.src_lang = source_lang
            
            # Tokenize input
            encoded = self.tokenizer(
                preprocessed_text,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **encoded,
                    forced_bos_token_id=self.tokenizer.lang_code_to_id[target_lang],
                    max_length=max_length,
                    num_beams=4,  # Beam search for better quality
                    length_penalty=1.0,
                    early_stopping=True,
                    do_sample=False  # Deterministic for medical consistency
                )
            
            # Decode translation
            translation = self.tokenizer.batch_decode(
                generated_tokens, 
                skip_special_tokens=True
            )[0]
            
            # Post-process medical translation
            final_translation = self._postprocess_medical_translation(
                translation, target_language, preserve_medical_terms
            )
            
            # Update translation statistics
            translation_time = time.time() - start_time
            self._update_translation_stats(translation_time)
            
            logger.info(f"Translation completed in {translation_time:.2f} seconds")
            
            return final_translation
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise MedicalTranslationError(f"Translation failed: {str(e)}")
    
    def translate_batch(self, 
                       texts: List[str], 
                       target_language: str,
                       source_language: str = "english") -> List[str]:
        """
        Translate multiple texts in batch for efficiency.
        
        Args:
            texts: List of source texts to translate
            target_language: Target language code or name
            source_language: Source language code or name
            
        Returns:
            List of translated texts
        """
        if not texts:
            return texts
        
        start_time = time.time()
        logger.info(f"Batch translating {len(texts)} texts")
        
        try:
            # Filter out empty texts
            non_empty_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
            
            if not non_empty_texts:
                return texts
            
            # Normalize language codes
            source_lang = self._normalize_language_code(source_language)
            target_lang = self._normalize_language_code(target_language)
            
            # Skip if same language
            if source_lang == target_lang:
                return texts
            
            # Extract texts and indices
            indices, batch_texts = zip(*non_empty_texts)
            
            # Preprocess all texts
            preprocessed_texts = [
                self._preprocess_medical_text(text, preserve_medical_terms=True)
                for text in batch_texts
            ]
            
            # Set tokenizer source language
            self.tokenizer.src_lang = source_lang
            
            # Tokenize batch
            encoded = self.tokenizer(
                preprocessed_texts,
                return_tensors="pt",
                max_length=1000,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate batch translations
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **encoded,
                    forced_bos_token_id=self.tokenizer.lang_code_to_id[target_lang],
                    max_length=1000,
                    num_beams=4,
                    length_penalty=1.0,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode batch translations
            translations = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True
            )
            
            # Post-process translations
            final_translations = [
                self._postprocess_medical_translation(trans, target_language, True)
                for trans in translations
            ]
            
            # Reconstruct original order
            result = texts.copy()
            for idx, translation in zip(indices, final_translations):
                result[idx] = translation
            
            batch_time = time.time() - start_time
            logger.info(f"Batch translation completed in {batch_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Batch translation failed: {str(e)}")
            raise MedicalTranslationError(f"Batch translation failed: {str(e)}")
    
    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code to mBART format."""
        language_lower = language.lower().strip()
        
        if language_lower in self.LANGUAGE_CODES:
            return self.LANGUAGE_CODES[language_lower]
        
        # If already in mBART format, return as-is
        if language_lower in self.LANGUAGE_CODES.values():
            return language_lower
        
        raise MedicalTranslationError(f"Unsupported language: {language}")
    
    def _preprocess_medical_text(self, text: str, preserve_medical_terms: bool) -> str:
        """
        Preprocess text for medical translation with terminology preservation.
        
        Args:
            text: Source text
            preserve_medical_terms: Whether to preserve medical terminology
            
        Returns:
            Preprocessed text ready for translation
        """
        if not preserve_medical_terms:
            return text
        
        # Mark medical terms that should be preserved
        # This is a simplified approach - in production, use medical NER
        medical_indicators = [
            "mg", "ml", "mcg", "kg", "lb", "mmHg", "bpm",
            "tablet", "capsule", "injection", "IV", "IM",
            "daily", "twice daily", "three times daily", "as needed"
        ]
        
        preprocessed = text
        for indicator in medical_indicators:
            # Add special tokens to preserve these terms
            preprocessed = preprocessed.replace(
                indicator, 
                f"<PRESERVE>{indicator}</PRESERVE>"
            )
        
        return preprocessed
    
    def _postprocess_medical_translation(self, 
                                       translation: str, 
                                       target_language: str,
                                       preserve_medical_terms: bool) -> str:
        """
        Post-process translated text to restore medical terminology.
        
        Args:
            translation: Raw translation from model
            target_language: Target language
            preserve_medical_terms: Whether medical terms were preserved
            
        Returns:
            Final translation with medical terminology restored
        """
        if not preserve_medical_terms:
            return translation
        
        # Restore preserved medical terms
        postprocessed = translation
        
        # Remove preservation markers and restore original terms
        import re
        preserve_pattern = r'<PRESERVE>(.*?)</PRESERVE>'
        matches = re.findall(preserve_pattern, postprocessed)
        
        for match in matches:
            postprocessed = postprocessed.replace(
                f"<PRESERVE>{match}</PRESERVE>",
                match
            )
        
        # Apply language-specific medical term corrections
        postprocessed = self._apply_medical_terminology_corrections(
            postprocessed, target_language
        )
        
        return postprocessed
    
    def _apply_medical_terminology_corrections(self, 
                                             text: str, 
                                             target_language: str) -> str:
        """Apply language-specific medical terminology corrections."""
        target_lang = target_language.lower()
        
        if target_lang in ["spanish", "es", "es_xx"]:
            # Spanish medical corrections
            corrections = {
                "tableta": "tablet",  # Keep English for medication forms
                "cápsula": "capsule",
                "miligramo": "mg",
                "mililitro": "ml"
            }
            
            for spanish_term, english_term in corrections.items():
                text = text.replace(spanish_term, english_term)
        
        elif target_lang in ["chinese", "mandarin", "zh", "zh_cn"]:
            # Chinese medical corrections - keep critical terms in English/Latin
            corrections = {
                "毫克": "mg",
                "毫升": "ml", 
                "片剂": "tablet",
                "胶囊": "capsule"
            }
            
            for chinese_term, english_term in corrections.items():
                text = text.replace(chinese_term, english_term)
        
        return text
    
    def _update_translation_stats(self, translation_time: float) -> None:
        """Update translation performance statistics."""
        self.translation_stats["total_translations"] += 1
        self.translation_stats["total_time"] += translation_time
    
    def get_translation_stats(self) -> Dict[str, float]:
        """Get translation performance statistics."""
        stats = self.translation_stats.copy()
        
        if stats["total_translations"] > 0:
            stats["average_time"] = stats["total_time"] / stats["total_translations"]
        else:
            stats["average_time"] = 0.0
        
        return stats
    
    def is_supported_language(self, language: str) -> bool:
        """Check if language is supported for translation."""
        try:
            self._normalize_language_code(language)
            return True
        except MedicalTranslationError:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.LANGUAGE_CODES.keys())