"""
Test script for AFAS feature extraction services.

This script demonstrates how to test the feature extraction algorithms
without needing the API server.
"""

import pandas as pd
import os
from src.services.fluency_service import compute_fluency_metrics
from src.services.pronunciation_service import compute_pronunciation_metrics
from src.services.lexical_diversity_service import compute_lexical_diversity_metrics
from src.services.lexical_cefr_service import compute_lexical_cefr_metrics


def create_sample_transcript(filename: str = "test_transcript.csv"):
    """
    Create a sample transcript CSV file for testing.
    
    This creates a realistic transcript with:
    - Multiple words with timestamps
    - Varying confidence scores
    - Some pauses between words
    """
    data = {
        'word': [
            'hello', 'world', 'this', 'is', 'a', 'test', 'of', 'the',
            'automatic', 'feedback', 'system', 'for', 'speaking', 'assessment',
            'it', 'measures', 'fluency', 'pronunciation', 'and', 'lexical',
            'diversity', 'using', 'advanced', 'algorithms', 'and', 'machine',
            'learning', 'techniques'
        ],
        'probability': [
            0.95, 0.92, 0.88, 0.90, 0.85, 0.93, 0.87, 0.91,
            0.89, 0.94, 0.86, 0.88, 0.92, 0.90,
            0.85, 0.88, 0.91, 0.93, 0.87, 0.89,
            0.92, 0.88, 0.90, 0.94, 0.86, 0.89,
            0.91, 0.93
        ],
        'start': [
            0.0, 0.5, 1.2, 1.8, 2.2, 2.6, 3.1, 3.5,
            4.0, 4.6, 5.2, 5.8, 6.4, 7.0,
            7.8, 8.3, 8.9, 9.5, 10.2, 10.7,
            11.3, 11.9, 12.5, 13.1, 13.7, 14.3,
            14.9, 15.5
        ],
        'end': [
            0.5, 1.0, 1.7, 2.1, 2.5, 2.9, 3.4, 3.8,
            4.5, 5.1, 5.7, 6.3, 6.9, 7.5,
            8.2, 8.7, 9.3, 9.9, 10.6, 11.1,
            11.7, 12.3, 12.9, 13.5, 14.1, 14.7,
            15.3, 16.0
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Created sample transcript: {filename}")
    return filename


def test_fluency_service(filename: str = "test_transcript.csv"):
    """Test fluency metrics calculation."""
    print("\n" + "=" * 50)
    print("Testing Fluency Service")
    print("=" * 50)
    
    if not os.path.exists(filename):
        print(f"Creating sample transcript: {filename}")
        create_sample_transcript(filename)
    
    result = compute_fluency_metrics(filename)
    
    print(f"\nResults:")
    print(f"  File: {result['file']}")
    print(f"  Speech Rate: {result['speech_rate_wps']:.3f} words/second")
    print(f"  Pause Ratio: {result['ratio_pauses_to_duration']:.3%}")
    
    print("\n✅ Fluency service test passed")
    return result


def test_pronunciation_service(filename: str = "test_transcript.csv"):
    """Test pronunciation metrics calculation."""
    print("\n" + "=" * 50)
    print("Testing Pronunciation Service")
    print("=" * 50)
    
    if not os.path.exists(filename):
        print(f"Creating sample transcript: {filename}")
        create_sample_transcript(filename)
    
    result = compute_pronunciation_metrics(filename)
    
    print(f"\nResults:")
    print(f"  File: {result['file']}")
    print(f"  0-50%:   {result['0–50%']:.2f}%")
    print(f"  50-70%:  {result['50–70%']:.2f}%")
    print(f"  70-85%:  {result['70–85%']:.2f}%")
    print(f"  85-95%:  {result['85–95%']:.2f}%")
    print(f"  95-100%: {result['95-100%']:.2f}%")
    
    print("\n✅ Pronunciation service test passed")
    return result


def test_lexical_diversity_service(filename: str = "test_transcript.csv"):
    """Test lexical diversity metrics calculation."""
    print("\n" + "=" * 50)
    print("Testing Lexical Diversity Service")
    print("=" * 50)
    
    if not os.path.exists(filename):
        print(f"Creating sample transcript: {filename}")
        create_sample_transcript(filename)
    
    result = compute_lexical_diversity_metrics(filename)
    
    print(f"\nResults:")
    print(f"  File: {result['file']}")
    print(f"  Unique Types: {result['unique_types']}")
    print(f"  Total Tokens: {result['total_tokens']}")
    print(f"  TTR: {result['TTR']:.3f}")
    print(f"  MSTTR: {result['MSTTR']:.3f}")
    
    print("\n✅ Lexical diversity service test passed")
    return result


def test_lexical_cefr_service(filename: str = "test_transcript.csv"):
    """Test CEFR level analysis."""
    print("\n" + "=" * 50)
    print("Testing CEFR Lexical Service")
    print("=" * 50)
    
    if not os.path.exists(filename):
        print(f"Creating sample transcript: {filename}")
        create_sample_transcript(filename)
    
    try:
        result = compute_lexical_cefr_metrics(filename)
        
        print(f"\nResults:")
        print(f"  File: {result['file']}")
        print(f"  A1: {result['A1']:.2f}%")
        print(f"  A2: {result['A2']:.2f}%")
        print(f"  B1: {result['B1']:.2f}%")
        print(f"  B2: {result['B2']:.2f}%")
        print(f"  C1: {result['C1']:.2f}%")
        
        print("\n✅ CEFR lexical service test passed")
        return result
    except FileNotFoundError as e:
        print(f"\n⚠️  Warning: CEFR dictionary not found: {e}")
        print("   Make sure data/oxford_cerf.csv exists")
        return None


def run_all_service_tests():
    """Run all service tests."""
    print("=" * 50)
    print("AFAS Service Test Suite")
    print("=" * 50)
    
    # Create sample transcript
    transcript_file = create_sample_transcript()
    
    # Run all tests
    test_fluency_service(transcript_file)
    test_pronunciation_service(transcript_file)
    test_lexical_diversity_service(transcript_file)
    test_lexical_cefr_service(transcript_file)
    
    print("\n" + "=" * 50)
    print("✅ All service tests completed!")
    print("=" * 50)
    
    # Cleanup (optional)
    # os.remove(transcript_file)
    # print(f"\nCleaned up: {transcript_file}")


if __name__ == "__main__":
    run_all_service_tests()

