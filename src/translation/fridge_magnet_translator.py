"""
Fridge Magnet Translator

Simple translation service that takes the completed English fridge magnet output
and translates it to Spanish and Mandarin while preserving critical medical data.

Flow: English Clinical Data → English Fridge Magnet → Translated Fridge Magnet
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

logger = logging.getLogger(__name__)


class FridgeMagnetTranslationError(Exception):
    """Raised when fridge magnet translation fails."""
    pass


class FridgeMagnetTranslator:
    """
    Translates completed English fridge magnet output to Spanish and Mandarin.
    
    This translator works on the final patient-friendly summary output,
    preserving medication names, dosages, and critical medical data.
    """
    
    def __init__(self):
        """Initialize fridge magnet translator with mBART model."""
        self.model = None
        self.tokenizer = None
        self._load_translation_model()
        
        # Patterns for preserving critical medical data during translation
        self.preserve_patterns = {
            'medication_dosage': r'\b\d+\.?\d*\s*(mg|ml|mcg|g|tablet|capsule)s?\b',
            'medication_frequency': r'\b(daily|twice daily|three times daily|as needed|every \d+ hours?)\b',
            'lab_values': r'\b\d+\.?\d*\s*(mg/dL|mmol/L|mmHg|bpm|%)\b',
            'dates_times': r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}:\d{2}\s?(AM|PM)\b',
            'medication_names': r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s\d+\.?\d*\s*mg\b'
        }
    
    def _load_translation_model(self):
        """Load mBART translation model."""
        try:
            model_name = "facebook/mbart-large-50-many-to-many-mmt"
            self.model = MBartForConditionalGeneration.from_pretrained(model_name)
            self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
            logger.info("Fridge magnet translation model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
            raise FridgeMagnetTranslationError(f"Model loading failed: {e}")
    
    def translate_fridge_magnet(self, english_fridge_magnet: str, target_language: str) -> str:
        """
        Translate English fridge magnet to target language.
        
        Args:
            english_fridge_magnet: Complete English fridge magnet text
            target_language: 'spanish' or 'mandarin'
        
        Returns:
            Translated fridge magnet with preserved medical data
        """
        if target_language.lower() not in ['spanish', 'mandarin']:
            raise FridgeMagnetTranslationError(f"Unsupported language: {target_language}")
        
        logger.info(f"Translating fridge magnet to {target_language}")
        
        # Step 1: Extract and preserve critical medical data
        preserved_data = self._extract_critical_data(english_fridge_magnet)
        
        # Step 2: Create masked version for translation
        masked_text = self._mask_critical_data(english_fridge_magnet, preserved_data)
        
        # Step 3: Translate masked version
        translated_text = self._translate_text(masked_text, target_language)
        
        # Step 4: Restore critical data
        final_translation = self._restore_critical_data(translated_text, preserved_data, target_language)
        
        return final_translation
    
    def _extract_critical_data(self, text: str) -> Dict[str, List[str]]:
        """Extract critical medical data that should not be translated."""
        preserved_data = {}
        
        for pattern_name, pattern in self.preserve_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            preserved_data[pattern_name] = matches
            logger.debug(f"Preserved {len(matches)} {pattern_name} items")
        
        return preserved_data
    
    def _mask_critical_data(self, text: str, preserved_data: Dict[str, List[str]]) -> str:
        """Replace critical data with placeholders for translation."""
        masked_text = text
        placeholder_map = {}
        
        for pattern_name, pattern in self.preserve_patterns.items():
            matches = re.finditer(pattern, masked_text, re.IGNORECASE)
            for i, match in enumerate(matches):
                placeholder = f"___{pattern_name.upper()}_{i}___"
                placeholder_map[placeholder] = match.group()
                masked_text = masked_text.replace(match.group(), placeholder, 1)
        
        return masked_text
    
    def _translate_text(self, text: str, target_language: str) -> str:
        """Translate text using mBART model."""
        try:
            # Set language codes
            lang_codes = {
                'spanish': 'es_XX',
                'mandarin': 'zh_CN'
            }
            
            self.tokenizer.src_lang = "en_XX"
            target_lang = lang_codes[target_language.lower()]
            
            # Tokenize
            encoded = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
            
            # Generate translation
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[target_lang],
                max_length=1024,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode
            translation = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            return translation
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise FridgeMagnetTranslationError(f"Translation failed: {e}")
    
    def _restore_critical_data(self, translated_text: str, preserved_data: Dict, target_language: str) -> str:
        """Restore critical medical data in the translated text."""
        final_text = translated_text
        
        # Restore preserved patterns
        for pattern_name, pattern in self.preserve_patterns.items():
            if pattern_name in preserved_data:
                for i, preserved_item in enumerate(preserved_data[pattern_name]):
                    placeholder = f"___{pattern_name.upper()}_{i}___"
                    final_text = final_text.replace(placeholder, preserved_item)
        
        # Add language-specific medical context
        final_text = self._add_medical_context(final_text, target_language)
        
        return final_text
    
    def _add_medical_context(self, text: str, target_language: str) -> str:
        """Add language-specific medical context and disclaimers."""
        
        if target_language.lower() == 'spanish':
            # Add Spanish medical disclaimer
            disclaimer = "\n\n⚠️ IMPORTANTE: Los nombres de medicamentos permanecen en inglés. Consulte a su médico si tiene preguntas."
            return text + disclaimer
            
        elif target_language.lower() == 'mandarin':
            # Add Mandarin medical disclaimer  
            disclaimer = "\n\n⚠️ 重要提示：药物名称保持英文。如有疑问请咨询您的医生。"
            return text + disclaimer
        
        return text

    def translate_html_fridge_magnet(self, html_content: str, target_language: str) -> str:
        """
        Translate HTML fridge magnet content while preserving structure.
        
        Args:
            html_content: HTML fridge magnet content
            target_language: Target language for translation
        
        Returns:
            Translated HTML with preserved medical data and structure
        """
        # Extract text content from HTML
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Translate text nodes while preserving HTML structure
            text_nodes = soup.find_all(string=True)
            
            for text_node in text_nodes:
                if text_node.strip() and text_node.parent.name not in ['script', 'style']:
                    translated_text = self.translate_fridge_magnet(str(text_node), target_language)
                    text_node.replace_with(translated_text)
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"HTML translation failed: {e}")
            # Fallback to text translation
            return self.translate_fridge_magnet(html_content, target_language)


# Simple API for existing formatter integration
def translate_patient_summary(english_summary: str, target_language: str) -> str:
    """
    Simple function to translate English patient summary to target language.
    
    Args:
        english_summary: Complete English fridge magnet summary
        target_language: 'spanish' or 'mandarin'
    
    Returns:
        Translated summary with preserved medical data
    """
    translator = FridgeMagnetTranslator()
    return translator.translate_fridge_magnet(english_summary, target_language)