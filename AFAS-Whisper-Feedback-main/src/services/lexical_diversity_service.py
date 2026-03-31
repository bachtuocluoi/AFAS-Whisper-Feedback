"""
Lexical diversity feature extraction service.

This module computes vocabulary diversity metrics including Type-Token Ratio (TTR)
and Mean Segmental Type-Token Ratio (MSTTR). These metrics measure the richness
and variety of vocabulary used in speech.
"""

import re
from typing import List, Dict
import pandas as pd
from config.settings import settings


def tokenize(words: List[str]) -> List[str]:
    """
    Tokenize and clean word list.
    
    This function normalizes words by:
    - Converting to lowercase
    - Removing non-alphabetic characters (except apostrophes)
    - Filtering out empty strings
    
    Args:
        words: List of word strings from transcript
        
    Returns:
        List of cleaned tokens (lowercase, alphanumeric only)
        
    Example:
        >>> tokens = tokenize(["Hello,", "world!", "it's"])
        >>> print(tokens)  # ['hello', 'world', "it's"]
    """
    tokens = []
    for w in words:
        w = w.lower()
        w = re.sub(r"[^a-z']", "", w)  # Keep only letters and apostrophes
        if w != "":
            tokens.append(w)
    return tokens


def compute_ttr(tokens: List[str]) -> float:
    """
    Compute Type-Token Ratio (TTR).
    
    TTR measures vocabulary diversity by calculating the ratio of unique words
    (types) to total words (tokens). Higher TTR indicates more diverse vocabulary.
    
    Formula: TTR = number of unique types / total number of tokens
    
    Args:
        tokens: List of tokenized words
        
    Returns:
        TTR value between 0.0 and 1.0
        
    Example:
        >>> tokens = ["hello", "world", "hello", "python"]
        >>> print(compute_ttr(tokens))  # 0.75 (3 unique / 4 total)
    """
    if len(tokens) == 0:
        return 0.0
    
    types = len(set(tokens))
    tokens_n = len(tokens)
    return types / tokens_n


def compute_msttr(
    tokens: List[str], 
    segment_size: int = None
) -> float:
    """
    Compute Mean Segmental Type-Token Ratio (MSTTR).
    
    MSTTR is a more stable measure of lexical diversity than TTR because it
    calculates TTR for fixed-size segments and averages them. This reduces
    the effect of text length on the metric.
    
    Algorithm:
    1. Divide tokens into segments of fixed size
    2. Calculate TTR for each segment
    3. Return the mean of all segment TTRs
    
    Args:
        tokens: List of tokenized words
        segment_size: Size of each segment for TTR calculation.
                     If None, uses value from settings.
    
    Returns:
        MSTTR value between 0.0 and 1.0
        
    Example:
        >>> tokens = ["hello"] * 100 + ["world"] * 50
        >>> print(compute_msttr(tokens, segment_size=50))
    """
    if segment_size is None:
        segment_size = settings.msttr_segment_size
    
    if len(tokens) < segment_size:
        return compute_ttr(tokens)
    
    ttrs = []
    # Slide window through tokens with step size equal to segment_size
    for i in range(0, len(tokens) - segment_size + 1, segment_size):
        segment = tokens[i:i+segment_size]
        ttrs.append(compute_ttr(segment))
    
    if not ttrs:
        return 0.0
    
    return float(sum(ttrs) / len(ttrs))


def compute_lexical_diversity_metrics(asr_result: dict) -> Dict[str, float]:
    """
    Compute lexical diversity metrics from transcript CSV.
    
    This function calculates vocabulary diversity measures including:
    - Unique types: Number of distinct words
    - Total tokens: Total number of words
    - TTR: Type-Token Ratio
    - MSTTR: Mean Segmental Type-Token Ratio
    
    Args:
        transcript_csv_path: Path to CSV file containing transcript with column:
                           ['word']
    
    Returns:
        Dictionary containing:
        - file: Input file path
        - unique_types: Number of unique words
        - total_tokens: Total number of words
        - TTR: Type-Token Ratio
        - MSTTR: Mean Segmental Type-Token Ratio
        
    Example:
        >>> result = compute_lexical_diversity_metrics("transcript.csv")
        >>> print(f"TTR: {result['TTR']:.3f}")
        >>> print(f"MSTTR: {result['MSTTR']:.3f}")
    """
    raw_words = []

    for seg in asr_result.get("segments", []):
        for w in seg.get("words", []):
            word = w.get("word", "").strip()
            if word:
                raw_words.append(word)

    tokens = tokenize(raw_words)

    if not tokens:
        return {
            "unique_types": 0,
            "total_tokens": 0,
            "ttr": 0.0,
            "msttr": 0.0
        }

    return {
        "unique_types": len(set(tokens)),
        "total_tokens": len(tokens),
        "ttr": round(compute_ttr(tokens), 4),
        "msttr": round(compute_msttr(tokens, segment_size=settings.msttr_segment_size), 4),
    }

