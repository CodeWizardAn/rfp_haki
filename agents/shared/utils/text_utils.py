"""
Text Cleaning Utilities
Common text processing and cleaning functions

Features:
- Text normalization
- Special character removal
- Number extraction
- Fuzzy matching
- Tokenization
"""

import re
import unicodedata
from typing import List, Optional, Tuple, Set, Dict, Any
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class FuzzyMatchResult:
    """Result of a fuzzy match"""
    matched: bool
    score: float
    original: str
    candidate: str
    normalized_original: str
    normalized_candidate: str


class TextCleaner:
    """
    Text cleaning and processing utilities
    """
    
    # Common abbreviations in wire/cable industry
    ABBREVIATIONS = {
        'sqmm': 'sq mm',
        'sq.mm': 'sq mm',
        'mm2': 'sq mm',
        'mm²': 'sq mm',
        'kv': 'kV',
        'mv': 'mV',
        'deg': '°',
        'degc': '°C',
        'degf': '°F',
        'no.': 'number',
        'nos.': 'numbers',
        'qty': 'quantity',
        'spec': 'specification',
        'specs': 'specifications',
        'temp': 'temperature',
        'max': 'maximum',
        'min': 'minimum',
        'approx': 'approximately',
        'dia': 'diameter',
        'thk': 'thickness',
        'len': 'length',
        'wt': 'weight',
        'vol': 'voltage',
        'curr': 'current',
        'res': 'resistance',
        'cond': 'conductor',
        'ins': 'insulation',
        'arm': 'armour',
    }
    
    # Words to remove (stopwords for technical context)
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
    }
    
    def __init__(self, preserve_numbers: bool = True):
        """
        Initialize text cleaner
        
        Args:
            preserve_numbers: Whether to preserve numbers during cleaning
        """
        self.preserve_numbers = preserve_numbers
    
    def clean(
        self,
        text: str,
        lowercase: bool = True,
        remove_punctuation: bool = False,
        expand_abbreviations: bool = True,
        remove_stopwords: bool = False
    ) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_punctuation: Remove punctuation
            expand_abbreviations: Expand common abbreviations
            remove_stopwords: Remove stopwords
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        result = text
        
        # Normalize unicode
        result = unicodedata.normalize('NFKD', result)
        
        # Normalize whitespace
        result = self.normalize_whitespace(result)
        
        # Lowercase
        if lowercase:
            result = result.lower()
        
        # Expand abbreviations
        if expand_abbreviations:
            for abbr, full in self.ABBREVIATIONS.items():
                result = re.sub(rf'\b{abbr}\b', full, result, flags=re.IGNORECASE)
        
        # Remove punctuation (but keep numbers and units)
        if remove_punctuation:
            if self.preserve_numbers:
                # Keep numbers, decimal points, and unit indicators
                result = re.sub(r'[^\w\s.°/×x-]', ' ', result)
            else:
                result = re.sub(r'[^\w\s]', ' ', result)
        
        # Remove stopwords
        if remove_stopwords:
            words = result.split()
            words = [w for w in words if w.lower() not in self.STOPWORDS]
            result = ' '.join(words)
        
        # Final whitespace normalization
        result = self.normalize_whitespace(result)
        
        return result.strip()
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        # Replace various whitespace with single space
        result = re.sub(r'[\t\n\r\f\v]+', ' ', text)
        # Collapse multiple spaces
        result = re.sub(r' +', ' ', result)
        
        return result.strip()
    
    def remove_special_chars(
        self,
        text: str,
        keep_chars: str = "",
        replace_with: str = " "
    ) -> str:
        """
        Remove special characters from text
        
        Args:
            text: Input text
            keep_chars: Characters to keep (in addition to alphanumeric)
            replace_with: Replacement character
            
        Returns:
            Text with special characters removed
        """
        if not text:
            return ""
        
        pattern = rf'[^\w\s{re.escape(keep_chars)}]'
        result = re.sub(pattern, replace_with, text)
        
        return self.normalize_whitespace(result)
    
    def extract_numbers(
        self,
        text: str,
        include_decimals: bool = True,
        include_negative: bool = False
    ) -> List[float]:
        """
        Extract all numbers from text
        
        Args:
            text: Input text
            include_decimals: Include decimal numbers
            include_negative: Include negative numbers
            
        Returns:
            List of extracted numbers
        """
        if not text:
            return []
        
        if include_negative:
            if include_decimals:
                pattern = r'-?\d+\.?\d*'
            else:
                pattern = r'-?\d+'
        else:
            if include_decimals:
                pattern = r'\d+\.?\d*'
            else:
                pattern = r'\d+'
        
        matches = re.findall(pattern, text)
        
        numbers = []
        for m in matches:
            try:
                if '.' in m:
                    numbers.append(float(m))
                else:
                    numbers.append(float(int(m)))
            except ValueError:
                continue
        
        return numbers
    
    def extract_alphanumeric(self, text: str) -> str:
        """
        Extract only alphanumeric characters
        
        Args:
            text: Input text
            
        Returns:
            Alphanumeric-only text
        """
        if not text:
            return ""
        
        return re.sub(r'[^a-zA-Z0-9]', '', text)
    
    def fuzzy_match(
        self,
        text1: str,
        text2: str,
        threshold: float = 0.8,
        normalize: bool = True
    ) -> FuzzyMatchResult:
        """
        Perform fuzzy matching between two strings
        
        Args:
            text1: First text
            text2: Second text
            threshold: Match threshold (0-1)
            normalize: Normalize texts before matching
            
        Returns:
            FuzzyMatchResult with match details
        """
        original1, original2 = text1, text2
        
        if normalize:
            text1 = self.clean(text1, lowercase=True, remove_stopwords=True)
            text2 = self.clean(text2, lowercase=True, remove_stopwords=True)
        
        # Calculate similarity
        ratio = SequenceMatcher(None, text1, text2).ratio()
        
        return FuzzyMatchResult(
            matched=ratio >= threshold,
            score=ratio,
            original=original1,
            candidate=original2,
            normalized_original=text1,
            normalized_candidate=text2
        )
    
    def tokenize(
        self,
        text: str,
        lowercase: bool = True,
        remove_stopwords: bool = False,
        min_length: int = 1
    ) -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_stopwords: Remove stopwords
            min_length: Minimum token length
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Clean and split
        cleaned = self.clean(text, lowercase=lowercase, remove_stopwords=remove_stopwords)
        tokens = cleaned.split()
        
        # Filter by length
        tokens = [t for t in tokens if len(t) >= min_length]
        
        return tokens
    
    def extract_key_value_pairs(
        self,
        text: str,
        separators: List[str] = [':', '=', '-']
    ) -> Dict[str, str]:
        """
        Extract key-value pairs from text
        
        Args:
            text: Input text
            separators: List of key-value separators
            
        Returns:
            Dictionary of extracted pairs
        """
        if not text:
            return {}
        
        result = {}
        
        # Build pattern for separators
        sep_pattern = '|'.join(re.escape(s) for s in separators)
        
        # Match patterns like "Key: Value" or "Key = Value"
        pattern = rf'(\w[\w\s]*?)\s*(?:{sep_pattern})\s*([^\n;,]+)'
        
        matches = re.findall(pattern, text)
        
        for key, value in matches:
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            result[key] = value
        
        return result
    
    def highlight_differences(
        self,
        text1: str,
        text2: str
    ) -> Tuple[str, str, List[Tuple[int, int]]]:
        """
        Find and highlight differences between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Tuple of (text1_marked, text2_marked, difference_positions)
        """
        matcher = SequenceMatcher(None, text1, text2)
        
        differences = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences.append((i1, i2, j1, j2, tag))
        
        # Simple position list
        diff_positions = [(d[0], d[1]) for d in differences]
        
        return text1, text2, diff_positions


# Module-level cleaner instance
_cleaner = TextCleaner()


def clean_text(
    text: str,
    lowercase: bool = True,
    remove_punctuation: bool = False
) -> str:
    """Clean and normalize text"""
    return _cleaner.clean(text, lowercase=lowercase, remove_punctuation=remove_punctuation)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    return _cleaner.normalize_whitespace(text)


def remove_special_chars(text: str, keep_chars: str = "") -> str:
    """Remove special characters from text"""
    return _cleaner.remove_special_chars(text, keep_chars=keep_chars)


def extract_numbers(text: str, include_decimals: bool = True) -> List[float]:
    """Extract numbers from text"""
    return _cleaner.extract_numbers(text, include_decimals=include_decimals)


def extract_alphanumeric(text: str) -> str:
    """Extract only alphanumeric characters"""
    return _cleaner.extract_alphanumeric(text)


def fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> FuzzyMatchResult:
    """Perform fuzzy matching"""
    return _cleaner.fuzzy_match(text1, text2, threshold=threshold)


def tokenize(text: str, lowercase: bool = True) -> List[str]:
    """Tokenize text into words"""
    return _cleaner.tokenize(text, lowercase=lowercase)
