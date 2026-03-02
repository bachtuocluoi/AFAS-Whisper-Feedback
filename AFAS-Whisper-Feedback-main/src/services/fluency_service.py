"""
Fluency feature extraction service.

This module computes fluency metrics from speech transcripts, including
speech rate and pause ratio. Fluency measures the smoothness and naturalness
of speech delivery.
"""

import pandas as pd
from typing import Dict
from config.settings import settings


def compute_fluency_metrics(
    transcript_csv_path: str, 
    pause_threshold: float = None
) -> Dict[str, float]:
    """
    Compute fluency metrics from transcript CSV file.
    
    This function calculates:
    - Speech Rate: Words per second (WPS) or Words per minute (WPM)
    - Pause Ratio: Ratio of pause time to total speech duration
    
    The pause detection algorithm identifies gaps between words that exceed
    a threshold duration (default 0.25 seconds).
    
    Args:
        transcript_csv_path: Path to CSV file containing transcript with columns:
                           ['word', 'start', 'end']
        pause_threshold: Minimum gap duration (seconds) to consider as a pause.
                        If None, uses value from settings.
    
    Returns:
        Dictionary containing:
        - file: Input file path
        - speech_rate_wps: Speech rate in words per second
        - ratio_pauses_to_duration: Ratio of pause time to total duration (0.0-1.0)
    
    Example:
        >>> result = compute_fluency_metrics("transcript.csv")
        >>> print(f"Speech rate: {result['speech_rate_wps']:.2f} WPS")
        >>> print(f"Pause ratio: {result['ratio_pauses_to_duration']:.2%}")
    """
    if pause_threshold is None:
        pause_threshold = settings.pause_threshold
    
    df = pd.read_csv(transcript_csv_path)
    
    # Extract words with timestamps
    words = []
    for index in range(len(df)):
        words.append({
            "word": df.iloc[index]["word"],
            "start": df.iloc[index]["start"],
            "end": df.iloc[index]["end"]
        })
    
    if not words:
        return {
            "file": transcript_csv_path,
            "speech_rate_wps": 0.0,
            "ratio_pauses_to_duration": 0.0
        }
    
    total_duration = words[-1]['end']
    
    if total_duration == 0:
        return {
            "file": transcript_csv_path,
            "speech_rate_wps": 0.0,
            "ratio_pauses_to_duration": 0.0
        }
    
    # -------------------------
    # Speech Rate Calculation
    # -------------------------
    # Speech rate = total words / total duration
    # Convert to words per second (WPS)
    total_words = len(words)
    speech_rate_wpm = total_words / total_duration * 60  # Words per minute
    speech_rate_wps = speech_rate_wpm / 60  # Words per second
    
    # -------------------------
    # Pause Detection Algorithm
    # -------------------------
    # Identify gaps between consecutive words that exceed threshold
    pauses = []
    
    for i in range(1, total_words):
        prev_end = words[i-1]["end"]
        curr_start = words[i]["start"]
        gap = curr_start - prev_end
        
        if gap >= pause_threshold:
            pauses.append(gap)
    
    total_pause_time = sum(pauses)
    
    # Calculate pause ratio
    pause_ratio = float(total_pause_time) / total_duration if total_duration > 0 else 0.0
    
    # Return results
    return {
        "file": transcript_csv_path,
        "speech_rate_wps": speech_rate_wps,
        "ratio_pauses_to_duration": pause_ratio
    }

