"""
Pronunciation quality assessment service.

This module evaluates pronunciation quality based on ASR confidence scores.
Words are categorized into confidence bins, and the distribution provides
an indication of pronunciation accuracy.
"""

import pandas as pd
from typing import Dict


def compute_pronunciation_metrics(asr_result: dict) -> Dict[str, float]:
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
    probabilities = []

    for seg in asr_result.get("segments", []):
        for w in seg.get("words", []):
            prob = w.get("probability", 0.0)
            probabilities.append(prob)

    if not probabilities:
        return {
            "score_0_50": 0.0,
            "score_50_70": 0.0,
            "score_70_85": 0.0,
            "score_85_95": 0.0,
            "score_95_100": 0.0,
            "pronunciation_score": 0.0
        }

    asr_df = pd.DataFrame({
        "probability": probabilities
    })

    bins = [0, 0.5, 0.7, 0.85, 0.95, 1.000001]
    labels = ["0-50", "50-70", "70-85", "85-95", "95-100"]

    asr_df["conf_bin"] = pd.cut(
        asr_df["probability"],
        bins=bins,
        labels=labels,
        right=False
    )

    grouped = asr_df.groupby("conf_bin").agg({"probability": "count"}).reset_index()

    total_words = grouped["probability"].sum()

    if total_words > 0:
        grouped["proportion"] = grouped["probability"] / total_words * 100
    else:
        grouped["proportion"] = 0.0

    bin_map = {
        "0-50": 0.0,
        "50-70": 0.0,
        "70-85": 0.0,
        "85-95": 0.0,
        "95-100": 0.0
    }

    for _, row in grouped.iterrows():
        label = row["conf_bin"]
        proportion = float(row["proportion"])

        if label in bin_map:
            bin_map[label] = round(proportion, 2)

    # điểm pronunciation tổng hợp đơn giản: lấy tỷ lệ nhóm 95-100 chia 100
    pronunciation_score = round(bin_map["95-100"] / 100, 4)

    return {
        "score_0_50": bin_map["0-50"],
        "score_50_70": bin_map["50-70"],
        "score_70_85": bin_map["70-85"],
        "score_85_95": bin_map["85-95"],
        "score_95_100": bin_map["95-100"],
        "pronunciation_score": pronunciation_score
    }