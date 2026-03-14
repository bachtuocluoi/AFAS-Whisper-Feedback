"""
Fluency feature extraction service.

This module computes fluency metrics from speech transcripts, including
speech rate and pause ratio. Fluency measures the smoothness and naturalness
of speech delivery.
"""

from typing import Dict


def compute_fluency_metrics(
    asr_result: dict,
    pause_threshold: float = 0.25
) -> Dict[str, float]:
    """
    Compute fluency metrics directly from Whisper ASR result.

    Args:
        asr_result: Whisper transcription result dictionary
        pause_threshold: Minimum gap duration (seconds) to consider as a pause

    Returns:
        Dictionary containing:
        - speech_rate: words per minute
        - pause_ratio: ratio of pause time to total duration
    """

    words = []

    segments = asr_result.get("segments", [])
    for seg in segments:
        for w in seg.get("words", []):
            word = w.get("word", "").strip()
            start = w.get("start", 0.0)
            end = w.get("end", 0.0)

            if word:
                words.append({
                    "word": word,
                    "start": start,
                    "end": end
                })

    if not words:
        return {
            "speech_rate": 0.0,
            "pause_ratio": 0.0
        }

    total_duration = words[-1]["end"]

    if total_duration <= 0:
        return {
            "speech_rate": 0.0,
            "pause_ratio": 0.0
        }

    total_words = len(words)

    # Words per minute
    speech_rate = (total_words / total_duration) * 60

    pauses = []
    for i in range(1, total_words):
        prev_end = words[i - 1]["end"]
        curr_start = words[i]["start"]
        gap = curr_start - prev_end

        if gap >= pause_threshold:
            pauses.append(gap)

    total_pause_time = sum(pauses)
    pause_ratio = total_pause_time / total_duration if total_duration > 0 else 0.0

    return {
        "speech_rate": round(speech_rate, 2),
        "pause_ratio": round(pause_ratio, 4)
    }
