"""
Complete workflow test demonstrating the full AFAS pipeline.

This script shows how to:
1. Transcribe audio using Whisper
2. Extract all features
3. Save to database via API
4. Retrieve results
"""

import os
import requests
import json
from src.services.asr_service import get_asr_service
from src.services.fluency_service import compute_fluency_metrics
from src.services.pronunciation_service import compute_pronunciation_metrics
from src.services.lexical_diversity_service import compute_lexical_diversity_metrics
from src.services.lexical_cefr_service import compute_lexical_cefr_metrics

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def full_workflow_example(audio_file_path: str = None, submit_id: int = 1):
    """
    Complete workflow example.
    
    Args:
        audio_file_path: Path to audio file (optional, for real transcription)
        submit_id: ID for the submission
    """
    print("=" * 60)
    print("AFAS Complete Workflow Example")
    print("=" * 60)
    
    # Step 1: ASR Transcription
    print("\n[Step 1] ASR Transcription")
    print("-" * 60)
    
    if audio_file_path and os.path.exists(audio_file_path):
        print(f"Transcribing audio: {audio_file_path}")
        asr_service = get_asr_service()
        transcript_csv = "transcript.csv"
        df = asr_service.transcribe_to_csv(audio_file_path, transcript_csv)
        print(f"✅ Transcription complete: {len(df)} words")
    else:
        print("⚠️  No audio file provided, using sample transcript")
        transcript_csv = "test_transcript.csv"
        # Create sample if doesn't exist
        from tests.test_services import create_sample_transcript
        create_sample_transcript(transcript_csv)
    
    # Step 2: Feature Extraction
    print("\n[Step 2] Feature Extraction")
    print("-" * 60)
    
    # Fluency
    print("Computing fluency metrics...")
    fluency_result = compute_fluency_metrics(transcript_csv)
    print(f"  Speech Rate: {fluency_result['speech_rate_wps']:.3f} WPS")
    print(f"  Pause Ratio: {fluency_result['ratio_pauses_to_duration']:.3%}")
    
    # Pronunciation
    print("Computing pronunciation metrics...")
    pronunciation_result = compute_pronunciation_metrics(transcript_csv)
    print(f"  Excellent (95-100%): {pronunciation_result['95-100%']:.1f}%")
    print(f"  Good (85-95%): {pronunciation_result['85–95%']:.1f}%")
    
    # Lexical Diversity
    print("Computing lexical diversity...")
    lexical_diversity = compute_lexical_diversity_metrics(transcript_csv)
    print(f"  TTR: {lexical_diversity['TTR']:.3f}")
    print(f"  MSTTR: {lexical_diversity['MSTTR']:.3f}")
    
    # CEFR Distribution
    print("Computing CEFR distribution...")
    try:
        cefr_result = compute_lexical_cefr_metrics(transcript_csv)
        print(f"  A1: {cefr_result['A1']:.1f}%")
        print(f"  B2: {cefr_result['B2']:.1f}%")
        print(f"  C1: {cefr_result['C1']:.1f}%")
    except Exception as e:
        print(f"  ⚠️  CEFR analysis failed: {e}")
        cefr_result = None
    
    # Step 3: Save to Database (via API)
    print("\n[Step 3] Saving to Database")
    print("-" * 60)
    
    try:
        # Save Fluency
        print("Saving fluency metrics...")
        response = requests.post(
            f"{API_BASE}/fluency/",
            json={
                "submit_id": submit_id,
                "speed_rate": fluency_result['speech_rate_wps'],
                "pause_ratio": fluency_result['ratio_pauses_to_duration']
            }
        )
        if response.status_code == 201:
            print("  ✅ Fluency saved")
        else:
            print(f"  ⚠️  Fluency save failed: {response.status_code}")
        
        # Save Lexical
        if cefr_result:
            print("Saving lexical metrics...")
            response = requests.post(
                f"{API_BASE}/lexical/",
                json={
                    "submit_id": submit_id,
                    "ttr": lexical_diversity['TTR'],
                    "msttr": lexical_diversity['MSTTR'],
                    "A1": cefr_result.get('A1', 0),
                    "A2": cefr_result.get('A2', 0),
                    "B1": cefr_result.get('B1', 0),
                    "B2": cefr_result.get('B2', 0),
                    "C1": cefr_result.get('C1', 0)
                }
            )
            if response.status_code == 201:
                print("  ✅ Lexical saved")
            else:
                print(f"  ⚠️  Lexical save failed: {response.status_code}")
        
        # Save Pronunciation
        print("Saving pronunciation metrics...")
        response = requests.post(
            f"{API_BASE}/pronunciation/",
            json={
                "submit_id": submit_id,
                "score_0_50": pronunciation_result['0–50%'],
                "score_50_70": pronunciation_result['50–70%'],
                "score_70_85": pronunciation_result['70–85%'],
                "score_85_95": pronunciation_result['85–95%'],
                "score_95_100": pronunciation_result['95-100%']
            }
        )
        if response.status_code == 201:
            print("  ✅ Pronunciation saved")
        else:
            print(f"  ⚠️  Pronunciation save failed: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Cannot connect to API server")
        print("  Please start the server: python -m uvicorn src.main:app --reload")
    
    # Step 4: Retrieve Results
    print("\n[Step 4] Retrieving Results")
    print("-" * 60)
    
    try:
        # Get Fluency
        response = requests.get(f"{API_BASE}/fluency/{submit_id}")
        if response.status_code == 200:
            print("Fluency Metrics:")
            print(json.dumps(response.json(), indent=2))
        
        # Get Lexical
        response = requests.get(f"{API_BASE}/lexical/{submit_id}")
        if response.status_code == 200:
            print("\nLexical Metrics:")
            print(json.dumps(response.json(), indent=2))
        
        # Get Pronunciation
        response = requests.get(f"{API_BASE}/pronunciation/{submit_id}")
        if response.status_code == 200:
            print("\nPronunciation Metrics:")
            print(json.dumps(response.json(), indent=2))
    
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Cannot connect to API server")
    
    print("\n" + "=" * 60)
    print("✅ Workflow completed!")
    print("=" * 60)


if __name__ == "__main__":
    import os
    import sys
    
    # Check if audio file provided as argument
    audio_file = None
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if not os.path.exists(audio_file):
            print(f"⚠️  Audio file not found: {audio_file}")
            audio_file = None
    
    full_workflow_example(audio_file_path=audio_file)

