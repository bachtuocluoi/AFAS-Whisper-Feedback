"""
Automatic Speech Recognition (ASR) service using Whisper.

This module provides transcription functionality using OpenAI's Whisper model
to convert audio files to text with word-level timestamps and confidence scores.
"""

import whisper
import pandas as pd
from typing import Dict
from config.settings import settings


class ASRService:
    """
    Service for performing speech recognition using Whisper model.
    
    This service handles loading the Whisper model and transcribing audio files
    with word-level timestamps and probability scores.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize ASR service with Whisper model.
        
        Args:
            model_name: Name of Whisper model to use (e.g., "base.en", "small.en").
                       If None, uses model from settings.
        """
        self.model_name = model_name or settings.whisper_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model into memory."""
        self.model = whisper.load_model(self.model_name)
    
    def transcribe(self, audio_file_path: str, word_timestamps: bool = True) -> Dict:
        """
        Transcribe audio file to text using Whisper.
        
        Args:
            audio_file_path: Path to audio file to transcribe
            word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Dictionary containing transcription results with segments and words
        """
        result = self.model.transcribe(audio_file_path, word_timestamps=word_timestamps)
        return result
    
    def transcribe_to_csv(
        self, 
        audio_file_path: str, 
        output_csv_path: str
    ) -> pd.DataFrame:
        """
        Transcribe audio file and save results to CSV.
        
        This method transcribes the audio, extracts word-level information
        (word, probability, start time, end time), and saves to CSV format.
        
        Args:
            audio_file_path: Path to input audio file
            output_csv_path: Path to output CSV file
            
        Returns:
            DataFrame containing transcription results
            
        Example:
            >>> service = ASRService()
            >>> df = service.transcribe_to_csv("audio.wav", "transcript.csv")
        """
        result = self.transcribe(audio_file_path, word_timestamps=True)
        
        words = []
        probs = []
        starts = []
        ends = []
        
        # Extract word-level information from segments
        if "segments" in result:
            for seg in result["segments"]:
                if "words" in seg:
                    for w in seg["words"]:
                        word = w.get("word", "").strip()
                        prob = w.get("probability", 0)
                        start = w.get("start", None)
                        end = w.get("end", None)
                        
                        words.append(word)
                        probs.append(prob)
                        starts.append(start)
                        ends.append(end)
        
        # Create DataFrame
        df = pd.DataFrame({
            "word": words,
            "probability": probs,
            "start": starts,
            "end": ends
        })
        
        # Save to CSV with UTF-8 BOM for Excel compatibility
        df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
        
        return df


# Global service instance (lazy loading)
_asr_service = None


def get_asr_service() -> ASRService:
    """
    Get or create global ASR service instance.
    
    Returns:
        ASRService: Singleton instance of ASR service
    """
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service

