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
    import pandas as pd
import re
from pathlib import Path
from typing import Dict, Optional
from config.settings import settings


def clean_word(word: str) -> str:
    return re.sub(r"[^a-zA-Z']", "", word).lower()


def load_cefr_dict(cefr_dict_path: str = None) -> Dict[str, str]:
    """
    Load CEFR level dictionary from CSV file.
    """

    if cefr_dict_path is None:
        cefr_dict_path = settings.cefr_dict_path

    csv_path = Path(cefr_dict_path)

    if not csv_path.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        csv_path = project_root / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"CEFR file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["word_clean"] = df["word"].astype(str).str.lower().str.strip()

    return dict(zip(df["word_clean"], df["level"]))


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


def compute_lexical_cefr_metrics(asr_result: dict) -> Dict[str, float]:
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
    cefr_dict = load_cefr_dict()

    words = []

    for seg in asr_result.get("segments", []):
        for w in seg.get("words", []):
            word = w.get("word", "").strip()
            if word:
                words.append(word)

    if not words:
        return {
            "a1": 0.0,
            "a2": 0.0,
            "b1": 0.0,
            "b2": 0.0,
            "c1": 0.0
        }

    cleaned_words = []
    levels = []
    scores = []

    for w in words:
        w_clean = clean_word(w)
        level = cefr_dict.get(w_clean, None)
        score = cefr_to_score(level)

        cleaned_words.append(w_clean)
        levels.append(level)
        scores.append(score)

    result_df = pd.DataFrame({
        "word_clean": cleaned_words,
        "cefr_level": levels,
        "lexical_score": scores
    })

    grouped = result_df.groupby("cefr_level").agg({"lexical_score": "count"}).reset_index()

    total_words = grouped["lexical_score"].sum()

    if total_words > 0:
        grouped["proportion"] = grouped["lexical_score"] / total_words * 100
    else:
        grouped["proportion"] = 0.0

    level_map = {
        "A1": 0.0,
        "A2": 0.0,
        "B1": 0.0,
        "B2": 0.0,
        "C1": 0.0
    }

    for _, row in grouped.iterrows():
        level = row["cefr_level"]
        proportion = float(row["proportion"])

        if level in level_map:
            level_map[level] = round(proportion, 2)

    return {
        "a1": level_map["A1"],
        "a2": level_map["A2"],
        "b1": level_map["B1"],
        "b2": level_map["B2"],
        "c1": level_map["C1"]
    }