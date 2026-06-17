"""
Grammar feature extraction service.

This module computes grammar metrics from Whisper ASR result.
It checks grammatical errors from the generated transcript text.
"""

from typing import Dict, List
import re
import language_tool_python


_tool = None


def get_grammar_tool():
    """
    Lazy-load LanguageTool only when needed.

    This avoids starting LanguageTool immediately when the app starts.
    """
    global _tool

    if _tool is None:
        _tool = language_tool_python.LanguageTool("en-US")

    return _tool


def extract_text_from_asr(asr_result: dict) -> str:
    """
    Extract transcript text from Whisper ASR result.

    Priority:
    1. Use asr_result["text"] if available.
    2. Otherwise, join all words from segments.
    """

    text = asr_result.get("text", "")

    if text and text.strip():
        return text.strip()

    words: List[str] = []

    segments = asr_result.get("segments", [])

    for seg in segments:
        for w in seg.get("words", []):
            word = w.get("word", "").strip()

            if word:
                words.append(word)

    return " ".join(words).strip()


def split_sentences(text: str) -> List[str]:
    """
    Split transcript into sentences.

    Whisper transcript may not always contain clear punctuation,
    so if no sentence punctuation exists, the whole text is treated as one sentence.
    """

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences and text.strip():
        sentences = [text.strip()]

    return sentences


def compute_grammar_metrics(asr_result: dict) -> Dict[str, float]:
    """
    Compute grammar metrics from Whisper ASR result.

    Returns:
        - ratio_error_sentences: ratio of sentences that contain grammar errors
        - total_errors: total number of grammar errors
        - error_rate: grammar errors per word
        - total_sentences: number of detected sentences
        - total_words: number of words in transcript
    """

    text = extract_text_from_asr(asr_result)

    if not text:
        return {
            "ratio_error_sentences": 0.0,
            "total_errors": 0,
            "error_rate": 0.0,
            "total_sentences": 0,
            "total_words": 0
        }

    sentences = split_sentences(text)
    total_words = len(text.split())

    if not sentences or total_words == 0:
        return {
            "ratio_error_sentences": 0.0,
            "total_errors": 0,
            "error_rate": 0.0,
            "total_sentences": 0,
            "total_words": total_words
        }

    tool = get_grammar_tool()

    total_errors = 0
    error_sentences = 0

    for sent in sentences:
        matches = tool.check(sent)

        if matches:
            error_sentences += 1

        total_errors += len(matches)

    ratio_error_sentences = error_sentences / len(sentences)
    error_rate = total_errors / total_words if total_words else 0.0

    return {
        "ratio_error_sentences": round(ratio_error_sentences, 2),
        "total_errors": total_errors,
        "error_rate": round(error_rate, 2)
    }