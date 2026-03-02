"""
CEFR (Common European Framework of Reference) level analysis service.

This module analyzes the lexical complexity of speech by mapping words to
their CEFR levels (A1, A2, B1, B2, C1, C2) and calculating the distribution
of vocabulary across these levels.
"""

import pandas as pd
import re
from typing import Dict, Optional
from config.settings import settings


def clean_word(word: str) -> str:
    """
    Clean and normalize word for dictionary lookup.
    
    Removes punctuation and converts to lowercase for matching against
    CEFR dictionary.
    
    Args:
        word: Raw word string from transcript
        
    Returns:
        Cleaned word (lowercase, alphanumeric only)
        
    Example:
        >>> clean_word("Hello!")
        'hello'
    """
    return re.sub(r"[^a-zA-Z']", "", word).lower()


def load_cefr_dict(cefr_dict_path: str = None) -> Dict[str, str]:
    """
    Load CEFR level dictionary from CSV file.
    
    The dictionary maps words to their CEFR levels (A1, A2, B1, B2, C1, C2).
    
    Args:
        cefr_dict_path: Path to CSV file with columns ['word', 'level'].
                       If None, uses path from settings.
    
    Returns:
        Dictionary mapping word (lowercase) to CEFR level
        
    Example:
        >>> cefr_dict = load_cefr_dict("data/oxford_cerf.csv")
        >>> print(cefr_dict.get("hello"))  # 'A1'
    """
    if cefr_dict_path is None:
        cefr_dict_path = settings.cefr_dict_path
    
    df = pd.read_csv(cefr_dict_path)
    df['word_clean'] = df['word'].str.lower().str.strip()
    return dict(zip(df['word_clean'], df['level']))


def cefr_to_score(level: Optional[str]) -> int:
    """
    Convert CEFR level to numeric score for ranking.
    
    Higher scores indicate more advanced vocabulary levels.
    
    Args:
        level: CEFR level string (A1, A2, B1, B2, C1, C2) or None
        
    Returns:
        Numeric score: A1=1, A2=2, B1=3, B2=4, C1=5, C2=6, Unknown=0
        
    Example:
        >>> cefr_to_score("B2")
        4
    """
    mapping = {
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C2": 6,
    }
    return mapping.get(level, 0)


def get_proportion(index: int, result_df: pd.DataFrame) -> float:
    """
    Safely get proportion value from DataFrame by index.
    
    Args:
        index: Row index in DataFrame
        result_df: DataFrame containing proportion column
        
    Returns:
        Proportion value, or 0.0 if index not found
    """
    try:
        return float(result_df.iloc[index]["proportion"])
    except (IndexError, KeyError):
        return 0.0


def compute_lexical_cefr_metrics(transcript_csv_path: str) -> Dict[str, float]:
    """
    Compute CEFR level distribution from transcript CSV.
    
    This function analyzes the vocabulary complexity by:
    1. Mapping each word to its CEFR level using a dictionary
    2. Calculating the percentage distribution across CEFR levels
    3. Returning proportions for each level (A1, A2, B1, B2, C1)
    
    Args:
        transcript_csv_path: Path to CSV file containing transcript with column:
                           ['word']
    
    Returns:
        Dictionary containing:
        - file: Input file path
        - A1: Percentage of words at A1 level
        - A2: Percentage of words at A2 level
        - B1: Percentage of words at B1 level
        - B2: Percentage of words at B2 level
        - C1: Percentage of words at C1 level
        
    Example:
        >>> result = compute_lexical_cefr_metrics("transcript.csv")
        >>> print(f"A1 words: {result['A1']:.1f}%")
        >>> print(f"C1 words: {result['C1']:.1f}%")
    """
    asr_df = pd.read_csv(transcript_csv_path)
    cefr_dict = load_cefr_dict()
    
    words = []
    levels = []
    scores = []
    
    # Map each word to its CEFR level
    for w in asr_df["word"]:
        w_clean = clean_word(w)
        level = cefr_dict.get(w_clean, None)
        score = cefr_to_score(level)
        
        words.append(w_clean)
        levels.append(level)
        scores.append(score)
    
    # Create result DataFrame
    result_df = asr_df.copy()
    result_df["word_clean"] = words
    result_df["cefr_level"] = levels
    result_df["lexical_score"] = scores
    
    # Group by CEFR level and count
    result_df = result_df.groupby(['cefr_level']).agg({'lexical_score': 'count'}).reset_index()
    
    # Calculate proportions (percentages)
    total_words = result_df['lexical_score'].sum()
    if total_words > 0:
        result_df['proportion'] = result_df['lexical_score'] / total_words * 100
    else:
        result_df['proportion'] = 0.0
    
    # Return proportions for each level
    # Note: We assume levels are ordered A1, A2, B1, B2, C1 in the grouped result
    return {
        "file": transcript_csv_path,
        "A1": get_proportion(0, result_df),
        "A2": get_proportion(1, result_df),
        "B1": get_proportion(2, result_df),
        "B2": get_proportion(3, result_df),
        "C1": get_proportion(4, result_df),
    }

