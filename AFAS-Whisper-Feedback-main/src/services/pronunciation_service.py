"""
Pronunciation quality assessment service.

This module evaluates pronunciation quality based on ASR confidence scores.
Words are categorized into confidence bins, and the distribution provides
an indication of pronunciation accuracy.
"""

import pandas as pd
from typing import Dict


def compute_pronunciation_metrics(transcript_csv_path: str) -> Dict[str, float]:
    """
    Compute pronunciation quality metrics from transcript CSV.
    
    This function categorizes words into confidence score bins and calculates
    the percentage distribution. Higher confidence scores indicate better
    pronunciation accuracy.
    
    Confidence bins:
    - 0-50%: Poor pronunciation
    - 50-70%: Below average pronunciation
    - 70-85%: Average pronunciation
    - 85-95%: Good pronunciation
    - 95-100%: Excellent pronunciation
    
    Args:
        transcript_csv_path: Path to CSV file containing transcript with columns:
                           ['word', 'probability']
    
    Returns:
        Dictionary containing:
        - file: Input file path
        - "0–50%": Percentage of words in 0-50% confidence range
        - "50–70%": Percentage of words in 50-70% confidence range
        - "70–85%": Percentage of words in 70-85% confidence range
        - "85–95%": Percentage of words in 85-95% confidence range
        - "95-100%": Percentage of words in 95-100% confidence range
    
    Example:
        >>> result = compute_pronunciation_metrics("transcript.csv")
        >>> print(f"Excellent pronunciation: {result['95-100%']:.1f}%")
    """
    asr_df = pd.read_csv(transcript_csv_path)
    
    if asr_df.empty:
        return {
            "file": transcript_csv_path,
            "0–50%": 0.0,
            "50–70%": 0.0,
            "70–85%": 0.0,
            "85–95%": 0.0,
            "95-100%": 0.0,
        }
    
    result_df = asr_df.copy()
    
    # Define confidence bins
    bins = [0, 0.5, 0.7, 0.85, 0.95, 1.0]
    labels = ["0–50%", "50–70%", "70–85%", "85–95%", "95-100%"]
    
    # Categorize words into confidence bins
    result_df["conf_bin"] = pd.cut(
        result_df["probability"], 
        bins=bins, 
        labels=labels, 
        right=False
    )
    
    # Count words in each bin
    result_df = result_df.groupby(['conf_bin']).agg({'probability': 'count'}).reset_index()
    
    # Calculate proportions (percentages)
    total_words = result_df['probability'].sum()
    if total_words > 0:
        result_df['proportion'] = result_df['probability'] / total_words * 100
    else:
        result_df['proportion'] = 0.0
    
    # Helper function to safely get proportion
    def get_prop(index: int, df: pd.DataFrame) -> float:
        """Get proportion for bin at given index, return 0 if not found."""
        try:
            return float(df.iloc[index]["proportion"])
        except (IndexError, KeyError):
            return 0.0
    
    return {
        "file": transcript_csv_path,
        "0–50%": get_prop(0, result_df),
        "50–70%": get_prop(1, result_df),
        "70–85%": get_prop(2, result_df),
        "85–95%": get_prop(3, result_df),
        "95-100%": get_prop(4, result_df),
    }

